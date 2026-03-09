"""AI agent orchestration for session analysis and setup recommendations.

Uses Pydantic AI agents with programmatic orchestration:
- route_signals() maps detected signals to specialist domains
- get_model_string() builds provider-specific model identifiers
- Specialist agents (balance, tyre, aero, technique) run independently
- Results combined, validated, and persisted
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ToolReturnPart
from pydantic_ai.models import Model

from ac_engineer.config.io import get_effective_model
from ac_engineer.knowledge import search_knowledge as kb_search
from ac_engineer.knowledge.models import KnowledgeFragment
from ac_engineer.storage.models import AgentUsage, ToolCallDetail

from .models import (
    AgentDeps,
    DriverFeedback,
    EngineerResponse,
    SetupChange,
    SpecialistResult,
)
from .setup_reader import read_parameter_ranges
from .setup_writer import validate_changes
from .tools import (
    get_corner_metrics,
    get_current_value,
    get_lap_detail,
    get_setup_range,
    search_kb,
)

if TYPE_CHECKING:
    from ac_engineer.config import ACConfig
    from ac_engineer.engineer.models import ParameterRange, SessionSummary, ValidationResult
    from ac_engineer.knowledge.models import KnowledgeFragment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — Signal-to-domain routing (R3)
# ---------------------------------------------------------------------------

SIGNAL_DOMAINS: dict[str, list[str]] = {
    "high_understeer": ["balance"],
    "high_oversteer": ["balance"],
    "brake_balance_issue": ["balance", "technique"],
    "suspension_bottoming": ["balance"],
    "tyre_temp_spread_high": ["tyre"],
    "tyre_temp_imbalance": ["tyre"],
    "tyre_wear_rapid": ["tyre"],
    "high_slip_angle": ["tyre"],
    "low_consistency": ["technique"],
    "lap_time_degradation": ["tyre"],
}

DOMAIN_PRIORITY: dict[str, int] = {
    "balance": 1,
    "tyre": 2,
    "aero": 3,
    "technique": 4,
}

AERO_SECTIONS: set[str] = {
    "WING_1", "WING_2", "WING_3", "WING_4",
    "RIDE_HEIGHT_0", "RIDE_HEIGHT_1",
    "RIDE_HEIGHT_LF", "RIDE_HEIGHT_RF", "RIDE_HEIGHT_LR", "RIDE_HEIGHT_RR",
}

# Domains that produce setup changes (used for aero trigger)
_SETUP_DOMAINS = {"balance", "tyre"}

# ---------------------------------------------------------------------------
# Skills prompt directory
# ---------------------------------------------------------------------------

_SKILLS_DIR = Path(__file__).parent / "skills"


def _load_skill_prompt(domain: str) -> str:
    """Load a specialist's system prompt from its markdown file."""
    prompt_path = _SKILLS_DIR / f"{domain}.md"
    return prompt_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Public functions — routing & model selection
# ---------------------------------------------------------------------------


def route_signals(
    signals: list[str],
    setup_parameters: dict[str, dict[str, float | str]] | None = None,
) -> list[str]:
    """Map detected signals to specialist domains.

    Returns sorted list of unique domain names by priority (balance first).
    Adds 'aero' if setup contains aero sections AND balance/tyre signals present.
    """
    domains: set[str] = set()

    for signal in signals:
        for domain in SIGNAL_DOMAINS.get(signal, []):
            domains.add(domain)

    # Aero detection: car has aero params AND has balance or tyre signals
    if setup_parameters and domains & _SETUP_DOMAINS:
        setup_sections = set(setup_parameters.keys())
        if setup_sections & AERO_SECTIONS:
            domains.add("aero")

    return sorted(domains, key=lambda d: DOMAIN_PRIORITY.get(d, 99))


def get_model_string(config: ACConfig) -> str:
    """Build Pydantic AI model string from ACConfig.

    Maps provider names to Pydantic AI prefixes:
    - 'anthropic' → 'anthropic:model'
    - 'openai' → 'openai:model'
    - 'gemini' → 'google-gla:model'
    """
    provider = config.llm_provider
    model = get_effective_model(config)
    prefix = "google-gla" if provider == "gemini" else provider
    return f"{prefix}:{model}"


def build_model(config: ACConfig) -> Model:
    """Build a Pydantic AI Model with the API key from config.

    Creates the appropriate provider with explicit api_key so the agent
    doesn't rely on environment variables being set.
    """
    from pydantic_ai.models import infer_model
    from pydantic_ai.providers import infer_provider

    model_name = get_effective_model(config)
    api_key = config.api_key
    provider_name = config.llm_provider

    if provider_name == "gemini":
        from pydantic_ai.providers.google import GoogleProvider

        provider = GoogleProvider(api_key=api_key)
        return infer_model(f"google-gla:{model_name}", provider_factory=lambda _: provider)
    elif provider_name == "anthropic":
        from pydantic_ai.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider(api_key=api_key)
        return infer_model(f"anthropic:{model_name}", provider_factory=lambda _: provider)
    elif provider_name == "openai":
        from pydantic_ai.providers.openai import OpenAIProvider

        provider = OpenAIProvider(api_key=api_key)
        return infer_model(f"openai:{model_name}", provider_factory=lambda _: provider)
    else:
        # Fallback: let Pydantic AI infer the provider (may use env vars)
        return infer_model(get_model_string(config))


# ---------------------------------------------------------------------------
# Usage extraction helper (T001)
# ---------------------------------------------------------------------------


def _extract_tool_calls(result) -> list[ToolCallDetail]:
    """Extract tool call details from a Pydantic AI agent result.

    Iterates all_messages(), finds ToolReturnPart instances in ModelRequest
    messages, and estimates token count as len(str(content)) // 4.
    """
    tool_calls: list[ToolCallDetail] = []
    for message in result.all_messages():
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    token_count = len(str(part.content)) // 4
                    tool_calls.append(
                        ToolCallDetail(
                            tool_name=part.tool_name,
                            token_count=token_count,
                        )
                    )
    return tool_calls


# ---------------------------------------------------------------------------
# Specialist agent factory
# ---------------------------------------------------------------------------


def _build_specialist_agent(domain: str, model: str | Model) -> Agent[AgentDeps, SpecialistResult]:
    """Create a specialist Pydantic AI agent for the given domain."""
    system_prompt = _load_skill_prompt(domain)

    agent: Agent[AgentDeps, SpecialistResult] = Agent(
        model,
        deps_type=AgentDeps,
        output_type=SpecialistResult,
        system_prompt=system_prompt,
    )

    # Register tools
    agent.tool(search_kb)
    agent.tool(get_setup_range)
    agent.tool(get_current_value)
    agent.tool(get_lap_detail)
    agent.tool(get_corner_metrics)

    return agent


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def _build_user_prompt(summary: SessionSummary, domain_signals: list[str]) -> str:
    """Format SessionSummary data into a natural language prompt for specialists."""
    lines = [
        f"## Session Analysis Request",
        f"",
        f"**Car**: {summary.car_name} | **Track**: {summary.track_name}",
        f"**Flying Laps**: {summary.flying_lap_count} | **Best Lap**: {summary.best_lap_time_s}s",
    ]

    if summary.lap_time_stddev_s is not None:
        lines.append(f"**Lap Time Std Dev**: {summary.lap_time_stddev_s:.3f}s")

    # Signals
    lines.append(f"")
    lines.append(f"### Detected Signals (your domain)")
    for sig in domain_signals:
        lines.append(f"- {sig}")

    # Corner issues
    if summary.corner_issues:
        lines.append(f"")
        lines.append(f"### Corner Issues")
        for ci in summary.corner_issues:
            lines.append(f"- {ci.description} (severity: {ci.severity})")

    # Tyre data
    if summary.tyre_temp_averages:
        lines.append(f"")
        lines.append(f"### Tyre Temperatures (avg)")
        for wheel, temp in summary.tyre_temp_averages.items():
            lines.append(f"- {wheel}: {temp}°C")

    if summary.tyre_pressure_averages:
        lines.append(f"")
        lines.append(f"### Tyre Pressures (avg)")
        for wheel, press in summary.tyre_pressure_averages.items():
            lines.append(f"- {wheel}: {press} psi")

    # Stint trends
    if summary.stints:
        lines.append(f"")
        lines.append(f"### Stint Trends")
        for stint in summary.stints:
            trend_info = f"Stint {stint.stint_index}: {stint.flying_lap_count} flying laps, trend={stint.lap_time_trend}"
            if stint.lap_time_slope_s_per_lap is not None:
                trend_info += f", slope={stint.lap_time_slope_s_per_lap:.3f}s/lap"
            lines.append(f"- {trend_info}")

    # Lap details
    if summary.laps:
        lines.append(f"")
        lines.append(f"### Lap Times")
        for lap in summary.laps:
            best_marker = " (BEST)" if lap.is_best else ""
            lines.append(f"- Lap {lap.lap_number}: {lap.lap_time_s}s (+{lap.gap_to_best_s}s){best_marker}")

    # Current setup
    if summary.active_setup_parameters:
        lines.append(f"")
        lines.append(f"### Current Setup Parameters")
        for section, params in summary.active_setup_parameters.items():
            for param, value in params.items():
                lines.append(f"- {section}.{param} = {value}")
        lines.append(f"")
        lines.append(
            "IMPORTANT: SetupChange.section must be one of the exact section names "
            "listed above. SetupChange.parameter is always 'VALUE'. "
            "Range data may not be available for all sections — if tools return no "
            "range data, propose small incremental changes based on the current "
            "values shown above."
        )
    else:
        lines.append(f"")
        lines.append(
            "WARNING: No setup parameters available. "
            "Do not propose SetupChanges — provide analysis only."
        )

    lines.append(f"")
    lines.append("Analyze this data and provide your specialist recommendations.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Result combination
# ---------------------------------------------------------------------------


def _combine_results(
    session_id: str,
    specialist_results: dict[str, SpecialistResult],
    summary: SessionSummary,
) -> EngineerResponse:
    """Merge all SpecialistResults into a single EngineerResponse."""
    all_changes: list[SetupChange] = []
    all_feedback: list[DriverFeedback] = []
    domain_summaries: list[str] = []
    signals_addressed: set[str] = set()

    # Process in priority order
    for domain in sorted(specialist_results.keys(), key=lambda d: DOMAIN_PRIORITY.get(d, 99)):
        result = specialist_results[domain]
        all_changes.extend(result.setup_changes)
        all_feedback.extend(result.driver_feedback)
        if result.domain_summary:
            domain_summaries.append(f"**{domain.title()}**: {result.domain_summary}")

    # Map signals to addressed list
    for signal in summary.signals:
        for domain in SIGNAL_DOMAINS.get(signal, []):
            if domain in specialist_results:
                signals_addressed.add(signal)

    # Build combined summary
    combined_summary = "\n\n".join(domain_summaries) if domain_summaries else "No specialist findings."

    # Determine overall confidence
    confidences = []
    for result in specialist_results.values():
        for change in result.setup_changes:
            confidences.append(change.confidence)
    if not confidences:
        overall_confidence = "medium"
    else:
        conf_order = {"high": 0, "medium": 1, "low": 2}
        avg_conf = sum(conf_order.get(c, 1) for c in confidences) / len(confidences)
        if avg_conf <= 0.5:
            overall_confidence = "high"
        elif avg_conf <= 1.5:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"

    return EngineerResponse(
        session_id=session_id,
        setup_changes=all_changes,
        driver_feedback=all_feedback,
        signals_addressed=sorted(signals_addressed),
        summary=combined_summary,
        explanation=combined_summary,
        confidence=overall_confidence,
    )


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------


def _resolve_conflicts(changes: list[SetupChange]) -> list[SetupChange]:
    """Remove duplicate section/parameter changes, keeping highest-priority domain's.

    Since changes are added in priority order (balance first), first occurrence wins.
    """
    seen: set[tuple[str, str]] = set()
    resolved: list[SetupChange] = []
    for change in changes:
        key = (change.section, change.parameter)
        if key not in seen:
            seen.add(key)
            resolved.append(change)
    return resolved


# ---------------------------------------------------------------------------
# Post-validation
# ---------------------------------------------------------------------------


def _post_validate_changes(
    changes: list[SetupChange],
    ranges: dict[str, ParameterRange],
) -> list[SetupChange]:
    """Validate and clamp all setup changes against parameter ranges."""
    validation_results = validate_changes(ranges, changes)

    updated: list[SetupChange] = []
    for change, vr in zip(changes, validation_results):
        if not vr.is_valid and vr.clamped_value is not None:
            # Clamp value and note in reasoning
            updated.append(change.model_copy(update={
                "value_after": vr.clamped_value,
                "reasoning": f"{change.reasoning} [Note: value clamped from {change.value_after} to {vr.clamped_value}]",
            }))
        elif vr.warning:
            updated.append(change.model_copy(update={
                "reasoning": f"{change.reasoning} [Warning: {vr.warning}]",
            }))
        else:
            updated.append(change)

    return updated


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


async def analyze_with_engineer(
    summary: SessionSummary,
    config: ACConfig,
    db_path: Path,
    ac_install_path: Path | None = None,
    parameter_ranges: dict[str, ParameterRange] | None = None,
    resolution_tier: int | None = None,
) -> EngineerResponse:
    """Primary entry point for AI-powered session analysis.

    Orchestrates: read ranges → route signals → pre-load knowledge →
    run specialists → combine → validate → resolve conflicts → persist → return.
    """
    install_path = ac_install_path or config.ac_install_path

    # Edge case: no flying laps
    if summary.flying_lap_count == 0:
        return EngineerResponse(
            session_id=summary.session_id,
            summary="Insufficient data: no flying laps detected in this session.",
            explanation="The session contains no clean flying laps to analyze. Complete at least one full lap without pit stops to get recommendations.",
            confidence="low",
        )

    # Read parameter ranges (use pre-resolved if provided)
    if parameter_ranges is not None:
        ranges = parameter_ranges
    else:
        ranges = read_parameter_ranges(install_path, summary.car_name)

    # Route signals to domains
    domains = route_signals(summary.signals, summary.active_setup_parameters)

    # Edge case: no signals
    if not domains:
        return EngineerResponse(
            session_id=summary.session_id,
            signals_addressed=[],
            summary="No issues detected. The car appears to be well-balanced for this session.",
            explanation="All telemetry signals are within normal ranges. No setup changes recommended at this time.",
            confidence="high",
        )

    # Pre-load knowledge for domain signals
    from ac_engineer.knowledge import get_knowledge_for_signals, search_knowledge

    all_knowledge: list[KnowledgeFragment] = []
    for signal in summary.signals:
        frags = search_knowledge(signal)
        for frag in frags[:3]:  # Top 3 per signal
            if frag not in all_knowledge:
                all_knowledge.append(frag)

    # Build model with API key
    model = build_model(config)

    # Run specialist agents
    specialist_results: dict[str, SpecialistResult] = {}
    collected_usage: list[AgentUsage] = []
    effective_model = get_effective_model(config)

    for domain in domains:
        # Determine domain-specific signals
        domain_signals = [
            s for s in summary.signals
            if domain in SIGNAL_DOMAINS.get(s, [])
        ]
        # Aero gets balance+tyre signals (it supplements them)
        if domain == "aero":
            domain_signals = [
                s for s in summary.signals
                if any(d in _SETUP_DOMAINS for d in SIGNAL_DOMAINS.get(s, []))
            ]

        deps = AgentDeps(
            session_summary=summary,
            parameter_ranges=ranges,
            domain_signals=domain_signals,
            knowledge_fragments=all_knowledge,
            resolution_tier=resolution_tier,
        )

        try:
            agent = _build_specialist_agent(domain, model)
            user_prompt = _build_user_prompt(summary, domain_signals)

            start_time = time.perf_counter()
            result = await agent.run(user_prompt, deps=deps)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            specialist_results[domain] = result.output

            # Extract usage data (T002)
            try:
                usage = result.usage()
                tool_calls = _extract_tool_calls(result)
                agent_usage = AgentUsage(
                    domain=domain,
                    model=effective_model,
                    input_tokens=usage.input_tokens or 0,
                    output_tokens=usage.output_tokens or 0,
                    tool_call_count=usage.tool_calls or 0,
                    turn_count=usage.requests or 0,
                    duration_ms=duration_ms,
                    tool_calls=tool_calls,
                )
                collected_usage.append(agent_usage)

                # Log usage summary (T004)
                logger.info(
                    "Agent usage: domain=%s input_tokens=%d output_tokens=%d "
                    "tool_call_count=%d duration_ms=%d",
                    domain,
                    agent_usage.input_tokens,
                    agent_usage.output_tokens,
                    agent_usage.tool_call_count,
                    duration_ms,
                )
            except Exception:
                logger.warning("Failed to extract usage for '%s'", domain, exc_info=True)

        except Exception:
            logger.exception("Specialist '%s' failed", domain)

    # Edge case: all specialists failed
    if not specialist_results:
        return EngineerResponse(
            session_id=summary.session_id,
            signals_addressed=summary.signals,
            summary="Analysis could not be completed due to an error.",
            explanation="The AI analysis encountered errors. Please try again or check your LLM provider configuration.",
            confidence="low",
        )

    # Combine results
    response = _combine_results(summary.session_id, specialist_results, summary)

    # Post-validate and clamp
    response = response.model_copy(update={
        "setup_changes": _post_validate_changes(response.setup_changes, ranges),
    })

    # Resolve conflicts
    response = response.model_copy(update={
        "setup_changes": _resolve_conflicts(response.setup_changes),
    })

    # Persist recommendation
    recommendation_id: str | None = None
    try:
        from ac_engineer.storage import save_recommendation
        from ac_engineer.storage.models import SetupChange as StorageSetupChange

        storage_changes = [
            StorageSetupChange(
                section=c.section,
                parameter=c.parameter,
                old_value=str(c.value_before) if c.value_before is not None else "",
                new_value=str(c.value_after),
                reasoning=c.reasoning,
            )
            for c in response.setup_changes
        ]
        rec = save_recommendation(
            db_path,
            summary.session_id,
            response.summary,
            storage_changes,
        )
        recommendation_id = rec.recommendation_id
    except Exception:
        logger.warning("Failed to persist recommendation", exc_info=True)

    # Persist usage data (T003)
    if recommendation_id and collected_usage:
        try:
            from ac_engineer.storage.usage import save_agent_usage

            for usage_record in collected_usage:
                usage_record = usage_record.model_copy(
                    update={"recommendation_id": recommendation_id}
                )
                save_agent_usage(db_path, usage_record)
        except Exception:
            logger.warning("Failed to persist usage data", exc_info=True)

    # Attach resolution tier metadata
    if resolution_tier is not None:
        tier_notice = ""
        if resolution_tier == 3:
            tier_notice = (
                "Parameter data was inferred from the session's active setup file. "
                "Exact adjustment ranges and factory defaults are not available for this car. "
                "Recommendations may be less precise."
            )
        response = response.model_copy(
            update={
                "resolution_tier": resolution_tier,
                "tier_notice": tier_notice,
            }
        )

    return response


# ---------------------------------------------------------------------------
# Apply recommendation
# ---------------------------------------------------------------------------


async def apply_recommendation(
    recommendation_id: str,
    setup_path: Path,
    db_path: Path,
    ac_install_path: Path | None = None,
    car_name: str | None = None,
) -> list:
    """Apply a previously generated recommendation to a setup file.

    Orchestrates: load from DB → validate → backup → apply → update status.
    """
    from ac_engineer.storage import get_recommendations, update_recommendation_status
    from ac_engineer.storage.models import Recommendation

    from .models import ChangeOutcome, ValidationResult
    from .setup_writer import apply_changes, create_backup

    # Find recommendation
    # We need to search across sessions, so query directly
    from ac_engineer.storage.db import _connect

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM recommendations WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Recommendation not found: {recommendation_id!r}")
        rec_dict = dict(row)

        change_rows = conn.execute(
            "SELECT * FROM setup_changes WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchall()
    finally:
        conn.close()

    if not change_rows:
        raise ValueError(f"No changes found for recommendation: {recommendation_id!r}")

    # Build ValidationResults from stored changes
    from .models import SetupChange as EngSetupChange

    # Read parameter ranges for re-validation
    ranges = {}
    if ac_install_path and car_name:
        ranges = read_parameter_ranges(ac_install_path, car_name)

    # Convert stored changes to SetupChange for validation
    proposed_changes = []
    for cr in change_rows:
        cr_dict = dict(cr)
        proposed_changes.append(EngSetupChange(
            section=cr_dict["section"],
            parameter=cr_dict["parameter"],
            value_before=float(cr_dict["old_value"]) if cr_dict["old_value"] else None,
            value_after=float(cr_dict["new_value"]),
            reasoning=cr_dict.get("reasoning", ""),
            expected_effect="",
            confidence="medium",
        ))

    # Validate
    validation_results = validate_changes(ranges, proposed_changes)

    # Backup + apply
    if not setup_path.is_file():
        raise FileNotFoundError(f"Setup file not found: {setup_path}")

    create_backup(setup_path)
    outcomes = apply_changes(setup_path, validation_results)

    # Update status
    update_recommendation_status(db_path, recommendation_id, "applied")

    return outcomes
