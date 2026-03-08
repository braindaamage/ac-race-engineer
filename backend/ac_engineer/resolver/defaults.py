"""Default value extraction from car configuration files."""

from __future__ import annotations

import configparser
import io
import re

# Corner suffix → axle section name in config files
CORNER_SUFFIXES: dict[str, str] = {
    "LF": "FRONT",
    "RF": "FRONT",
    "LR": "REAR",
    "RR": "REAR",
}

# Base param name → (config_filename, config_key)
CORNER_PARAMS: dict[str, tuple[str, str]] = {
    "CAMBER": ("suspensions.ini", "CAMBER"),
    "TOE_OUT": ("suspensions.ini", "TOE_OUT"),
    "SPRING_RATE": ("suspensions.ini", "SPRING_RATE"),
    "DAMP_BUMP": ("suspensions.ini", "BUMP"),
    "DAMP_FAST_BUMP": ("suspensions.ini", "FAST_BUMP"),
    "DAMP_REBOUND": ("suspensions.ini", "REBOUND"),
    "DAMP_FAST_REBOUND": ("suspensions.ini", "FAST_REBOUND"),
    "PRESSURE": ("tyres.ini", "PRESSURE_STATIC"),
}

# Section name → (config_filename, ini_section, ini_key)
DIRECT_PARAMS: dict[str, tuple[str, str, str]] = {
    "WING_0": ("aero.ini", "WING_0", "ANGLE"),
    "WING_1": ("aero.ini", "WING_1", "ANGLE"),
    "FINAL_GEAR_RATIO": ("drivetrain.ini", "GEARS", "FINAL"),
    "BRAKE_POWER_MULT": ("brakes.ini", "DATA", "BASE_LEVEL"),
    "FRONT_BIAS": ("brakes.ini", "DATA", "FRONT_SHARE"),
    "ARB_FRONT": ("suspensions.ini", "ARB", "FRONT"),
    "ARB_REAR": ("suspensions.ini", "ARB", "REAR"),
}

_GEAR_RE = re.compile(r"^GEAR_(\d+)$")


def _parse_config(text: str) -> configparser.ConfigParser:
    """Parse INI text with case-preserved keys."""
    parser = configparser.ConfigParser()
    parser.optionxform = str  # type: ignore[assignment]
    parser.read_string(text)
    return parser


def _safe_float(value: str) -> float | None:
    """Convert string to float, returning None on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _get_value(
    parsed: dict[str, configparser.ConfigParser],
    config_file: str,
    section: str,
    key: str,
) -> float | None:
    """Safely retrieve a float value from a parsed config."""
    cfg = parsed.get(config_file)
    if cfg is None:
        return None
    if not cfg.has_section(section):
        return None
    if not cfg.has_option(section, key):
        return None
    return _safe_float(cfg.get(section, key))


def extract_defaults(
    config_files: dict[str, str],
    parameter_sections: list[str],
) -> dict[str, float | None]:
    """Extract default values for setup parameters from AC car config files.

    Parameters
    ----------
    config_files:
        Mapping of filename (e.g. ``"suspensions.ini"``) to its text content.
    parameter_sections:
        List of setup.ini section names such as ``"CAMBER_LF"``, ``"WING_1"``.

    Returns
    -------
    dict mapping each section name to its default float value, or ``None``
    when the value cannot be resolved.
    """
    # Pre-parse all config files once
    parsed: dict[str, configparser.ConfigParser] = {}
    for filename, content in config_files.items():
        try:
            parsed[filename] = _parse_config(content)
        except configparser.Error:
            # Unparseable file — skip it; lookups will return None
            continue

    results: dict[str, float | None] = {}

    for section_name in parameter_sections:
        value: float | None = None

        # 1. Try corner-based parameters (e.g. CAMBER_LF, PRESSURE_RR)
        matched = False
        for suffix, axle in CORNER_SUFFIXES.items():
            if section_name.endswith(f"_{suffix}"):
                base = section_name[: -(len(suffix) + 1)]
                if base in CORNER_PARAMS:
                    config_file, config_key = CORNER_PARAMS[base]
                    value = _get_value(parsed, config_file, axle, config_key)
                    matched = True
                break  # suffix matched even if base not in CORNER_PARAMS

        # 2. Try direct parameters
        if not matched and section_name in DIRECT_PARAMS:
            config_file, ini_section, ini_key = DIRECT_PARAMS[section_name]
            value = _get_value(parsed, config_file, ini_section, ini_key)
            matched = True

        # 3. Try GEAR_N pattern
        if not matched:
            gear_match = _GEAR_RE.match(section_name)
            if gear_match:
                gear_key = f"GEAR_{gear_match.group(1)}"
                value = _get_value(parsed, "drivetrain.ini", "GEARS", gear_key)
                matched = True

        results[section_name] = value

    return results
