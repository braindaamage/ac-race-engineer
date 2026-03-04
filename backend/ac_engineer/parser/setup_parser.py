"""Setup .ini parsing and lap-to-setup association.

Provides generic INI text parsing (no hardcoded parameter names) and
the association algorithm that maps each lap to its active SetupEntry.
"""

from __future__ import annotations

import configparser
import io

from ac_engineer.parser.models import SetupEntry, SetupParameter


def parse_ini(ini_text: str | None) -> list[SetupParameter]:
    """Parse raw .ini text into a list of SetupParameter objects.

    Extracts all [section] + key=value pairs generically. Values are cast
    to float if possible; otherwise stored as str. Comments and blank lines
    are ignored. Section and parameter names preserve original casing.

    Args:
        ini_text: Raw .ini file contents as a string, or None.

    Returns:
        List of SetupParameter objects. Returns empty list for None or empty input.
    """
    if not ini_text or not ini_text.strip():
        return []

    parameters: list[SetupParameter] = []

    # Use configparser with case-sensitive keys (override optionxform)
    parser = configparser.RawConfigParser()
    parser.optionxform = str  # preserve original casing

    try:
        parser.read_string(ini_text)
    except configparser.Error:
        # Fallback: manual line parsing for non-standard INI files
        return _parse_ini_manual(ini_text)

    for section in parser.sections():
        for name, raw_value in parser.items(section):
            value: float | str
            stripped = raw_value.strip()
            try:
                value = float(stripped)
            except (ValueError, TypeError):
                value = stripped
            parameters.append(SetupParameter(
                section=section.strip(),
                name=name.strip(),
                value=value,
            ))

    return parameters


def _parse_ini_manual(ini_text: str) -> list[SetupParameter]:
    """Manual fallback INI parser for non-standard files."""
    parameters: list[SetupParameter] = []
    current_section = ""

    for line in ini_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";") or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1].strip()
        elif "=" in stripped and current_section:
            name, _, raw_value = stripped.partition("=")
            name = name.strip()
            raw_value = raw_value.strip()
            # Strip inline comments
            if ";" in raw_value:
                raw_value = raw_value[: raw_value.index(";")].strip()
            value: float | str
            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                value = raw_value
            parameters.append(SetupParameter(
                section=current_section,
                name=name,
                value=value,
            ))

    return parameters


def associate_setup(
    lap_number: int,
    setup_entries: list[SetupEntry],
) -> SetupEntry | None:
    """Return the SetupEntry active at the given lap number.

    Finds the entry with the highest ``lap_start`` that is ≤ ``lap_number``.

    Args:
        lap_number: The lap number to look up.
        setup_entries: List of SetupEntry objects ordered by lap_start (or not —
            the function handles unsorted input).

    Returns:
        The matching SetupEntry, or None if setup_entries is empty or no entry
        has lap_start ≤ lap_number.
    """
    if not setup_entries:
        return None

    best: SetupEntry | None = None
    for entry in setup_entries:
        if entry.lap_start <= lap_number:
            if best is None or entry.lap_start > best.lap_start:
                best = entry

    return best
