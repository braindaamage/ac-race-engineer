"""Pure conversion functions between AC storage formats and physical units.

Three storage conventions:
- INDEX (SHOW_CLICKS=2): physical = MIN + index * STEP
- SCALED (CAMBER, SHOW_CLICKS=0): physical = storage * scale_factor
- DIRECT (everything else): physical = storage (no conversion)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ParameterRange

# Section name prefixes that use scaled storage (value * factor).
SCALE_FACTORS: dict[str, float] = {
    "CAMBER": 0.1,
}


def _get_scale_factor(section: str) -> float | None:
    """Return the scale factor if *section* matches a known scaled prefix."""
    upper = section.upper()
    for prefix, factor in SCALE_FACTORS.items():
        if upper.startswith(prefix):
            return factor
    return None


def classify_parameter(section: str, show_clicks: int | None) -> str:
    """Classify a parameter's storage convention from car data.

    Returns ``"index"``, ``"scaled"``, or ``"direct"``.
    """
    if show_clicks is None:
        return "direct"
    if show_clicks == 2:
        return "index"
    if show_clicks == 0 and _get_scale_factor(section) is not None:
        return "scaled"
    return "direct"


def to_physical(storage_value: float, param_range: ParameterRange) -> float:
    """Convert a raw .ini VALUE to physical units."""
    convention = param_range.storage_convention
    if convention is None or convention == "direct":
        return storage_value
    if convention == "index":
        return param_range.min_value + storage_value * param_range.step
    if convention == "scaled":
        factor = _get_scale_factor(param_range.section)
        if factor is None:
            return storage_value
        return storage_value * factor
    return storage_value


def to_storage(physical_value: float, param_range: ParameterRange) -> float:
    """Convert a physical-unit value back to .ini storage format."""
    convention = param_range.storage_convention
    if convention is None or convention == "direct":
        return physical_value
    if convention == "index":
        step = param_range.step
        if step == 0:
            return physical_value
        raw_index = (physical_value - param_range.min_value) / step
        snapped = round(raw_index)
        max_index = round((param_range.max_value - param_range.min_value) / step)
        clamped = max(0, min(snapped, max_index))
        return float(clamped)
    if convention == "scaled":
        factor = _get_scale_factor(param_range.section)
        if factor is None or factor == 0:
            return physical_value
        # Round to 6 decimals first to correct IEEE 754 noise,
        # then round to nearest integer (AC stores scaled values as ints).
        raw = physical_value / factor
        return float(round(round(raw, 6)))
    return physical_value
