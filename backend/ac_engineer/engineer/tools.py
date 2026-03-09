"""Pydantic AI tool implementations for specialist agents.

All tools receive RunContext[AgentDeps] and return strings for the LLM.
"""

from __future__ import annotations

from pydantic_ai import RunContext

from ac_engineer.knowledge.search import search_knowledge

from .models import AgentDeps


async def search_kb(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search the vehicle dynamics knowledge base for supplementary information.

    Primary knowledge is already pre-loaded in your context. Use this only if
    you need additional details not covered above. Returns up to 2 fragments
    with source attribution.
    """
    fragments = search_knowledge(query)
    if not fragments:
        return "No relevant knowledge found."

    parts = []
    for frag in fragments[:2]:  # Limit to top 2
        parts.append(
            f"[Source: {frag.source_file} > {frag.section_title}]\n{frag.content}"
        )
    return "\n\n---\n\n".join(parts)


async def get_setup_range(ctx: RunContext[AgentDeps], sections: list[str]) -> str:
    """Get the valid parameter ranges for one or more setup sections.

    Returns min, max, step, and default values for each section.
    Sections not found get a 'not found' line. Empty list returns empty string.
    """
    if not sections:
        return ""

    blocks = []
    for section in sections:
        pr = ctx.deps.parameter_ranges.get(section)
        if pr is None:
            blocks.append(f"No range data found for section '{section}'.")
            continue

        result = f"Section: {section}\nMin: {pr.min_value}\nMax: {pr.max_value}\nStep: {pr.step}"
        if pr.default_value is not None:
            result += f"\nDefault: {pr.default_value}"
        blocks.append(result)

    return "\n\n".join(blocks)


async def get_lap_detail(ctx: RunContext[AgentDeps], lap_numbers: list[int]) -> str:
    """Get full metrics for one or more flying laps.

    Returns lap details for each requested lap number.
    Laps not found get a 'not found' line. Empty list returns empty string.
    """
    if not lap_numbers:
        return ""

    blocks = []
    for lap_number in lap_numbers:
        found = False
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
                blocks.append("\n".join(parts))
                found = True
                break

        if not found:
            blocks.append(f"Lap {lap_number} not found in flying laps.")

    return "\n\n".join(blocks)


async def get_corner_metrics(
    ctx: RunContext[AgentDeps],
    corner_numbers: list[int],
    lap_number: int | None = None,
) -> str:
    """Get corner issue data for one or more corners.

    If lap_number is provided, filters by that specific lap.
    Returns data for each requested corner number.
    Corners with no issues get a 'not found' line. Empty list returns empty string.
    """
    if not corner_numbers:
        return ""

    issues = ctx.deps.session_summary.corner_issues

    blocks = []
    for corner_number in corner_numbers:
        matching = [ci for ci in issues if ci.corner_number == corner_number]
        if not matching:
            blocks.append(f"No issue data for corner {corner_number}.")
            continue

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
        blocks.append("\n".join(parts))

    return "\n\n".join(blocks)
