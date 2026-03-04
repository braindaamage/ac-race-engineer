"""Read parameter ranges from AC car data/setup.ini files."""

from __future__ import annotations

import configparser
import logging
from pathlib import Path

from .models import ParameterRange

logger = logging.getLogger(__name__)


def read_parameter_ranges(
    ac_install_path: Path | None,
    car_name: str,
) -> dict[str, ParameterRange]:
    """Read setup parameter ranges from the car's data/setup.ini file.

    Returns dict mapping section name to ParameterRange.
    Empty dict if path invalid, car not found, or data/setup.ini missing.
    """
    if ac_install_path is None:
        return {}

    setup_ini = Path(ac_install_path) / "content" / "cars" / car_name / "data" / "setup.ini"
    if not setup_ini.is_file():
        logger.debug("setup.ini not found: %s", setup_ini)
        return {}

    cp = configparser.ConfigParser()
    cp.optionxform = str  # Preserve case
    try:
        cp.read(str(setup_ini), encoding="utf-8")
    except Exception:
        logger.warning("Failed to parse %s", setup_ini, exc_info=True)
        return {}

    ranges: dict[str, ParameterRange] = {}

    for section in cp.sections():
        try:
            min_val = float(cp.get(section, "MIN"))
            max_val = float(cp.get(section, "MAX"))
            step_val = float(cp.get(section, "STEP"))
        except (configparser.NoOptionError, ValueError):
            logger.debug("Skipping section %s: missing or invalid MIN/MAX/STEP", section)
            continue

        if step_val <= 0:
            logger.debug("Skipping section %s: step <= 0", section)
            continue

        if min_val > max_val:
            logger.debug("Skipping section %s: min > max", section)
            continue

        default_val = None
        try:
            default_val = float(cp.get(section, "DEFAULT"))
        except (configparser.NoOptionError, ValueError):
            pass

        ranges[section] = ParameterRange(
            section=section,
            parameter="VALUE",
            min_value=min_val,
            max_value=max_val,
            step=step_val,
            default_value=default_val,
        )

    return ranges


def get_parameter_range(
    ranges: dict[str, ParameterRange],
    section: str,
) -> ParameterRange | None:
    """Look up the range for a specific parameter section."""
    return ranges.get(section)
