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
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelRequest, ToolReturnPart
from pydantic_ai.models import Model

from ac_engineer.config.io import get_effective_model
from ac_engineer.knowledge.index import SIGNAL_MAP
from ac_engineer.knowledge.loader import get_docs_cache
from ac_engineer.knowledge.models import KnowledgeFragment
from ac_engineer.storage.models import LlmEvent, LlmToolCall

from .models import (
    AgentDeps,
    DriverFeedback,
    EngineerResponse,
    PrincipalNarrative,
    SetupChange,
    SpecialistResult,
)
from .conversion import to_physical, to_storage
from .setup_reader import read_parameter_ranges
from .setup_writer import validate_changes
from .tools import (
    get_corner_metrics,
    get_lap_detail,
    get_setup_range,
    search_kb,
)

if TYPE_CHECKING:
    from ac_engineer.config import ACConfig
    from ac_engineer.engineer.models import ParameterRange, SessionSummary, ValidationResult

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

DOMAIN_TOOLS: dict[str, list] = {
    "balance": [get_setup_range, get_corner_metrics, search_kb],
    "tyre": [get_setup_range, get_lap_detail, search_kb],
    "aero": [get_setup_range, get_corner_metrics, search_kb],
    "technique": [get_lap_detail, get_corner_metrics, search_kb],
    "principal": [get_lap_detail, get_corner_metrics],
}

DOMAIN_PARAMS: dict[str, tuple[str, ...]] = {
    "balance": (
        "SPRING_RATE", "DAMP_BUMP", "DAMP_FAST_BUMP", "DAMP_REBOUND",
        "DAMP_FAST_REBOUND", "ARB_", "RIDE_HEIGHT", "BRAKE_POWER", "BRAKE_BIAS",
    ),
    "tyre": ("PRESSURE_", "CAMBER_", "TOE_OUT_", "TOE_IN_"),
    "aero": ("WING_", "SPLITTER_"),
    "technique": (),
    "principal": (),
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


def extract_tool_calls(result) -> list[LlmToolCall]:
    """Extract tool call details from a Pydantic AI agent result.

    Iterates all_messages(), finds ToolReturnPart instances in ModelRequest
    messages, and estimates token count as len(str(content)) // 4.
    """
    tool_calls: list[LlmToolCall] = []
    call_index = 0
    for message in result.all_messages():
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    response_tokens = len(str(part.content)) // 4
                    tool_calls.append(
                        LlmToolCall(
                            tool_name=part.tool_name,
                            response_tokens=response_tokens,
                            call_index=call_index,
                        )
                    )
                    call_index += 1
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

    # Register domain-scoped tools
    for tool_fn in DOMAIN_TOOLS[domain]:
        agent.tool(tool_fn)

    return agent


# ---------------------------------------------------------------------------
# Knowledge pre-loading
# ---------------------------------------------------------------------------


def _select_knowledge_fragments(signals: list[str]) -> list[KnowledgeFragment]:
    """Select knowledge fragments for a set of signals using SIGNAL_MAP.

    Deterministic: same signals always produce same fragments in same order.
    Capped at 8 fragments.
    """
    seen: set[tuple[str, str]] = set()
    fragments: list[KnowledgeFragment] = []
    docs_cache = get_docs_cache()

    for signal in signals:
        for doc, section in SIGNAL_MAP.get(signal, []):
            key = (doc, section)
            if key in seen:
                continue
            seen.add(key)

            doc_sections = docs_cache.get(doc)
            if doc_sections is None:
                continue
            content = doc_sections.get(section, "")
            if not content:
                continue

            fragments.append(
                KnowledgeFragment(
                    source_file=doc,
                    section_title=section,
                    content=content,
                )
            )
            if len(fragments) >= 8:
                return fragments

    return fragments


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------


def _build_user_prompt(
    summary: SessionSummary,
    domain_signals: list[str],
    knowledge_fragments: list[KnowledgeFragment] | None = None,
    domain: str | None = None,
) -> str:
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

    # Vehicle dynamics knowledge
    lines.append(f"")
    lines.append(f"### Vehicle Dynamics Knowledge")
    if knowledge_fragments:
        for frag in knowledge_fragments:
            lines.append(f"**[{frag.source_file} > {frag.section_title}]**")
            lines.append(frag.content)
            lines.append(f"")
    else:
        lines.append(
            "No pre-loaded knowledge for these signals. "
            "Use the search_kb tool if you need vehicle dynamics information."
        )

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

    # Current setup — filter by domain if specified
    setup_params = summary.active_setup_parameters or {}
    if domain is not None:
        prefixes = DOMAIN_PARAMS.get(domain, ())
        if not prefixes:
            # Domains with empty prefixes (technique, principal) get no setup params
            setup_params = {}
        else:
            # Collect all prefixes from all domains for fallback detection
            all_prefixes = tuple(
                p for ps in DOMAIN_PARAMS.values() for p in ps
            )
            filtered: dict[str, dict[str, float | str]] = {}
            for section, params in setup_params.items():
                if section.startswith(prefixes):
                    filtered[section] = params
                elif domain == "balance" and not section.startswith(all_prefixes):
                    # Unrecognized sections fall back to balance
                    filtered[section] = params
            setup_params = filtered

    if setup_params:
        lines.append(f"")
        lines.append(f"### Current Setup Parameters")
        for section, params in setup_params.items():
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


def _populate_storage_fields(
    changes: list[SetupChange],
    ranges: dict[str, ParameterRange],
) -> list[SetupChange]:
    """Annotate each SetupChange with raw storage values and convention."""
    result: list[SetupChange] = []
    for change in changes:
        pr = ranges.get(change.section)
        if pr is None:
            result.append(change)
            continue
        storage_after = to_storage(change.value_after, pr)
        storage_before = (
            to_storage(change.value_before, pr)
            if change.value_before is not None
            else None
        )
        result.append(change.model_copy(update={
            "storage_value_before": storage_before,
            "storage_value_after": storage_after,
            "storage_convention": pr.storage_convention or "direct",
        }))
    return result


# ---------------------------------------------------------------------------
# Principal agent synthesis (Phase 12)
# ---------------------------------------------------------------------------


def _build_synthesis_prompt(
    response: EngineerResponse,
    specialist_results: dict[str, SpecialistResult],
) -> str:
    """Format specialist outputs into a user prompt for the principal agent synthesis."""
    lines: list[str] = []

    # Domain summaries
    lines.append("## Specialist Domain Summaries\n")
    for domain in sorted(specialist_results.keys(), key=lambda d: DOMAIN_PRIORITY.get(d, 99)):
        result = specialist_results[domain]
        lines.append(f"**{domain.title()}**: {result.domain_summary}\n")

    # Setup changes
    if response.setup_changes:
        lines.append("## Setup Changes\n")
        for c in response.setup_changes:
            lines.append(
                f"- [{c.section}] {c.parameter}: {c.value_before} → {c.value_after}"
            )
            lines.append(f"  Reasoning: {c.reasoning}")
            lines.append(f"  Expected effect: {c.expected_effect}\n")

    # Driver feedback
    if response.driver_feedback:
        lines.append("## Driver Feedback\n")
        for fb in response.driver_feedback:
            lines.append(f"- **{fb.area}**: {fb.observation}")
            lines.append(f"  Suggestion: {fb.suggestion}\n")

    # Signals addressed
    if response.signals_addressed:
        lines.append("## Signals Addressed\n")
        for sig in response.signals_addressed:
            lines.append(f"- {sig}")
        lines.append("")

    # Output instructions
    lines.append("## Your Task\n")
    lines.append(
        "Synthesize the specialist findings above into two distinct fields:\n"
        "\n"
        "**summary**: An executive headline of 2–4 sentences (≤80 words). "
        "State the dominant problem, its severity, and the correction direction. "
        "Use driver-friendly language — no raw parameter names like 'ARB_FRONT' or 'PRESSURE_LF'. "
        "Instead say 'front anti-roll bar' or 'front tyre pressure'.\n"
        "\n"
        "**explanation**: A detailed narrative of multiple paragraphs (≤300 words). "
        "Connect specialist findings causally — explain WHY the car behaves this way "
        "and HOW the changes work together. Discuss trade-offs between domains. "
        "Integrate technique suggestions naturally. "
        "Close with what the driver should expect to feel on track. "
        "Do NOT repeat the individual change reasoning fields verbatim — synthesize them."
    )

    return "\n".join(lines)


async def _synthesize_with_principal(
    response: EngineerResponse,
    specialist_results: dict[str, SpecialistResult],
    config: ACConfig,
):
    """Invoke the principal agent to produce a narrative summary and explanation.

    Uses structured output (result_type=PrincipalNarrative), no tools.
    Returns the full RunResult so the caller can extract usage.
    """
    from pydantic_ai.usage import UsageLimits

    model = build_model(config)
    system_prompt = _load_skill_prompt("principal")

    agent: Agent[None, PrincipalNarrative] = Agent(
        model,
        output_type=PrincipalNarrative,
        system_prompt=system_prompt,
    )

    user_prompt = _build_synthesis_prompt(response, specialist_results)

    result = await agent.run(
        user_prompt,
        usage_limits=UsageLimits(request_limit=5),
    )

    return result


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
    diagnostic_mode: bool = False,
    traces_dir: Path | None = None,
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

    # Convert raw storage values to physical units in the summary
    if summary.active_setup_parameters and ranges:
        converted_params = {}
        for section, params in summary.active_setup_parameters.items():
            pr = ranges.get(section)
            if pr and isinstance(params.get("VALUE"), (int, float)):
                converted_params[section] = {**params, "VALUE": to_physical(params["VALUE"], pr)}
            else:
                converted_params[section] = params
        summary = summary.model_copy(update={"active_setup_parameters": converted_params})

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

    # Build model with API key
    model = build_model(config)

    # Run specialist agents
    specialist_results: dict[str, SpecialistResult] = {}
    collected_usage: list[LlmEvent] = []
    collected_traces: list[dict] = []
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

        # Select domain-specific knowledge fragments
        domain_fragments = _select_knowledge_fragments(domain_signals)

        deps = AgentDeps(
            session_summary=summary,
            parameter_ranges=ranges,
            domain_signals=domain_signals,
            knowledge_fragments=domain_fragments,
            resolution_tier=resolution_tier,
        )

        try:
            agent = _build_specialist_agent(domain, model)
            user_prompt = _build_user_prompt(summary, domain_signals, domain_fragments, domain=domain)

            start_time = time.perf_counter()
            from pydantic_ai.usage import UsageLimits
            result = await agent.run(
                user_prompt, deps=deps,
                usage_limits=UsageLimits(request_limit=10),
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            specialist_results[domain] = result.output

            # Capture diagnostic trace (non-critical)
            if diagnostic_mode:
                try:
                    from .trace import serialize_agent_trace

                    system_prompt = _load_skill_prompt(domain)
                    trace_dict = serialize_agent_trace(
                        domain, system_prompt, user_prompt, result,
                    )
                    collected_traces.append(trace_dict)
                except Exception:
                    logger.warning("Failed to serialize trace for '%s'", domain, exc_info=True)

            # Extract usage data
            try:
                usage = result.usage()
                tool_calls = extract_tool_calls(result)
                llm_event = LlmEvent(
                    session_id=summary.session_id,
                    event_type="analysis",
                    agent_name=domain,
                    model=effective_model,
                    input_tokens=usage.input_tokens or 0,
                    output_tokens=usage.output_tokens or 0,
                    cache_read_tokens=usage.cache_read_tokens or 0,
                    cache_write_tokens=usage.cache_write_tokens or 0,
                    request_count=usage.requests or 0,
                    tool_call_count=usage.tool_calls or 0,
                    duration_ms=duration_ms,
                    tool_calls=tool_calls,
                )
                collected_usage.append(llm_event)

                # Log usage summary
                logger.info(
                    "Agent usage: domain=%s input_tokens=%d output_tokens=%d "
                    "tool_call_count=%d duration_ms=%d",
                    domain,
                    llm_event.input_tokens,
                    llm_event.output_tokens,
                    llm_event.tool_call_count,
                    duration_ms,
                )
            except Exception:
                logger.warning("Failed to extract usage for '%s'", domain, exc_info=True)

        except UsageLimitExceeded:
            logger.warning("Agent '%s' exceeded usage limit (request_limit=5)", domain)
            continue
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

    # Populate storage fields for frontend display
    response = response.model_copy(update={
        "setup_changes": _populate_storage_fields(response.setup_changes, ranges),
    })

    # Principal agent synthesis (Phase 12)
    try:
        synthesis_start = time.perf_counter()
        synthesis_result = await _synthesize_with_principal(
            response, specialist_results, config,
        )
        synthesis_duration_ms = int((time.perf_counter() - synthesis_start) * 1000)
        narrative = synthesis_result.output
        response = response.model_copy(update={
            "summary": narrative.summary,
            "explanation": narrative.explanation,
        })

        # Track principal agent usage (T009)
        try:
            usage = synthesis_result.usage()
            llm_event = LlmEvent(
                session_id=summary.session_id,
                event_type="analysis",
                agent_name="principal",
                model=effective_model,
                input_tokens=usage.input_tokens or 0,
                output_tokens=usage.output_tokens or 0,
                cache_read_tokens=usage.cache_read_tokens or 0,
                cache_write_tokens=usage.cache_write_tokens or 0,
                request_count=usage.requests or 0,
                tool_call_count=0,
                duration_ms=synthesis_duration_ms,
                tool_calls=[],
            )
            collected_usage.append(llm_event)
        except Exception:
            logger.warning("Failed to extract principal agent usage", exc_info=True)

        # Capture principal diagnostic trace
        if diagnostic_mode:
            try:
                from .trace import serialize_agent_trace

                system_prompt = _load_skill_prompt("principal")
                user_prompt = _build_synthesis_prompt(response, specialist_results)
                trace_dict = serialize_agent_trace(
                    "principal", system_prompt, user_prompt, synthesis_result,
                )
                collected_traces.append(trace_dict)
            except Exception:
                logger.warning("Failed to serialize principal trace", exc_info=True)
    except Exception:
        logger.warning(
            "Principal agent synthesis failed, keeping concatenated text",
            exc_info=True,
        )

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
            explanation=response.explanation,
        )
        recommendation_id = rec.recommendation_id
    except Exception:
        logger.warning("Failed to persist recommendation", exc_info=True)

    # Write diagnostic trace (non-critical)
    if diagnostic_mode and recommendation_id and collected_traces and traces_dir:
        try:
            from .trace import format_trace_markdown, write_trace

            trace_content = format_trace_markdown(
                summary.session_id, "recommendation", recommendation_id,
                collected_traces,
            )
            write_trace(traces_dir, "rec", recommendation_id, trace_content)
            logger.info("Wrote diagnostic trace for recommendation %s", recommendation_id)
        except Exception:
            logger.warning("Failed to write diagnostic trace", exc_info=True)

    # Persist usage data
    if recommendation_id and collected_usage:
        try:
            from ac_engineer.storage.usage import save_llm_event

            for usage_record in collected_usage:
                usage_record = usage_record.model_copy(
                    update={
                        "context_type": "recommendation",
                        "context_id": recommendation_id,
                    }
                )
                save_llm_event(db_path, usage_record)
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

    # Resolve parameter ranges (with show_clicks/storage_convention) for
    # re-validation and outbound storage conversion.
    ranges: dict[str, ParameterRange] = {}
    if ac_install_path and car_name:
        from ac_engineer.resolver import resolve_parameters

        resolved = resolve_parameters(ac_install_path, car_name, db_path)
        ranges = resolved.parameters

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
    outcomes = apply_changes(setup_path, validation_results, parameter_ranges=ranges)

    # Update status
    update_recommendation_status(db_path, recommendation_id, "applied")

    return outcomes
