"""Pydantic AI tool implementations for specialist agents.

All tools receive RunContext[AgentDeps] and return strings for the LLM.
"""

from __future__ import annotations

from pydantic_ai import RunContext

from ac_engineer.knowledge.search import search_knowledge

from .models import AgentDeps


async def search_kb(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search the vehicle dynamics knowledge base for relevant information.

    Returns formatted knowledge fragments with source attribution.
    """
    fragments = search_knowledge(query)
    if not fragments:
        return "No relevant knowledge found."

    parts = []
    for frag in fragments[:5]:  # Limit to top 5
        parts.append(
            f"[Source: {frag.source_file} > {frag.section_title}]\n{frag.content}"
        )
    return "\n\n---\n\n".join(parts)


async def get_setup_range(ctx: RunContext[AgentDeps], section: str) -> str:
    """Get the valid parameter range for a setup section.

    Returns min, max, step, and default values, or 'not found' message.
    """
    pr = ctx.deps.parameter_ranges.get(section)
    if pr is None:
        return f"No range data found for section '{section}'."

    result = f"Section: {section}\nMin: {pr.min_value}\nMax: {pr.max_value}\nStep: {pr.step}"
    if pr.default_value is not None:
        result += f"\nDefault: {pr.default_value}"
    return result


async def get_current_value(ctx: RunContext[AgentDeps], section: str) -> str:
    """Get the current setup value for a section from the active setup.

    Returns the current value or 'not found' message.
    """
    params = ctx.deps.session_summary.active_setup_parameters
    if not params:
        return "No active setup parameters available."

    section_params = params.get(section)
    if section_params is None:
        return f"Section '{section}' not found in active setup."

    value = section_params.get("VALUE")
    if value is None:
        return f"No VALUE parameter in section '{section}'."

    return f"{section}.VALUE = {value}"


async def get_lap_detail(ctx: RunContext[AgentDeps], lap_number: int) -> str:
    """Get full metrics for a specific flying lap.

    Returns lap details or empty message if lap not found.
    """
    for lap in ctx.deps.session_summary.laps:
        if lap.lap_number == lap_number:
            parts = [f"Lap {lap.lap_number}: {lap.lap_time_s}s"]
            if lap.is_best:
                parts.append("(BEST LAP)")
            parts.append(f"Gap to best: +{lap.gap_to_best_s}s")
            if lap.tyre_temp_avg_c is not None:
                parts.append(f"Tyre temp avg: {lap.tyre_temp_avg_c}°C")
            if lap.understeer_ratio_avg is not None:
                parts.append(f"Understeer ratio: {lap.understeer_ratio_avg}")
            if lap.peak_lat_g is not None:
                parts.append(f"Peak lateral G: {lap.peak_lat_g}")
            if lap.peak_speed_kmh is not None:
                parts.append(f"Peak speed: {lap.peak_speed_kmh} km/h")
            return "\n".join(parts)

    return f"Lap {lap_number} not found in flying laps."


async def get_corner_metrics(
    ctx: RunContext[AgentDeps],
    corner_number: int,
    lap_number: int | None = None,
) -> str:
    """Get corner issue data for a specific corner.

    If lap_number is provided, returns data for that specific lap's corner.
    Otherwise returns aggregated data across all reported corner issues.
    Returns 'not found' message if corner has no reported issues.
    """
    issues = ctx.deps.session_summary.corner_issues

    matching = [ci for ci in issues if ci.corner_number == corner_number]
    if not matching:
        return f"No issue data for corner {corner_number}."

    parts = []
    for ci in matching:
        line = f"Corner {ci.corner_number}: {ci.issue_type} (severity: {ci.severity})"
        if ci.understeer_ratio is not None:
            line += f", understeer_ratio={ci.understeer_ratio}"
        if ci.apex_speed_loss_pct is not None:
            line += f", apex_speed_loss={ci.apex_speed_loss_pct}%"
        if ci.avg_lat_g is not None:
            line += f", avg_lat_g={ci.avg_lat_g}"
        parts.append(line)

    return "\n".join(parts)
