"""Validate and apply setup changes with atomic writes and backups."""

from __future__ import annotations

import configparser
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from .models import ChangeOutcome, ParameterRange, SetupChange, ValidationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation (US3)
# ---------------------------------------------------------------------------


def validate_changes(
    ranges: dict[str, ParameterRange],
    proposed: list[SetupChange],
) -> list[ValidationResult]:
    """Validate proposed setup changes against known parameter ranges.

    Pure function — no file I/O. Returns results in same order as input.
    """
    results: list[ValidationResult] = []

    for change in proposed:
        pr = ranges.get(change.section)
        if pr is None:
            results.append(ValidationResult(
                section=change.section,
                parameter=change.parameter,
                proposed_value=change.value_after,
                clamped_value=None,
                is_valid=True,
                warning=f"No range data for section '{change.section}'",
            ))
            continue

        value = change.value_after
        if value < pr.min_value:
            results.append(ValidationResult(
                section=change.section,
                parameter=change.parameter,
                proposed_value=value,
                clamped_value=pr.min_value,
                is_valid=False,
                warning=f"Value {value} below minimum {pr.min_value}",
            ))
        elif value > pr.max_value:
            results.append(ValidationResult(
                section=change.section,
                parameter=change.parameter,
                proposed_value=value,
                clamped_value=pr.max_value,
                is_valid=False,
                warning=f"Value {value} above maximum {pr.max_value}",
            ))
        else:
            results.append(ValidationResult(
                section=change.section,
                parameter=change.parameter,
                proposed_value=value,
                clamped_value=None,
                is_valid=True,
            ))

    return results


# ---------------------------------------------------------------------------
# Backup (US4)
# ---------------------------------------------------------------------------


def create_backup(setup_path: Path) -> Path:
    """Create a timestamped backup of a setup file.

    Raises FileNotFoundError if setup_path does not exist.
    """
    setup_path = Path(setup_path)
    if not setup_path.is_file():
        raise FileNotFoundError(f"Setup file not found: {setup_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = setup_path.with_name(f"{setup_path.name}.bak.{timestamp}")
    shutil.copy2(str(setup_path), str(backup_path))
    logger.info("Backup created: %s", backup_path)
    return backup_path


# ---------------------------------------------------------------------------
# Apply changes (US4)
# ---------------------------------------------------------------------------


def apply_changes(
    setup_path: Path,
    changes: list[ValidationResult],
) -> list[ChangeOutcome]:
    """Apply validated changes to a setup .ini file atomically.

    Creates backup first, then writes via .tmp + os.replace.
    """
    if not changes:
        raise ValueError("Changes list must not be empty")

    setup_path = Path(setup_path)
    if not setup_path.is_file():
        raise FileNotFoundError(f"Setup file not found: {setup_path}")

    # Backup
    create_backup(setup_path)

    # Read original
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(str(setup_path), encoding="utf-8")

    # Deduplicate: last change wins per section
    change_map: dict[str, ValidationResult] = {}
    for c in changes:
        change_map[c.section] = c

    # Apply and collect outcomes
    existing_sections = set(cp.sections())
    outcomes: list[ChangeOutcome] = []
    for section, vr in change_map.items():
        # Skip sections that don't exist in the target file
        if section not in existing_sections:
            logger.warning(
                "Section '%s' not found in setup file, skipping change", section
            )
            outcomes.append(ChangeOutcome(
                section=section,
                parameter="VALUE",
                old_value="",
                new_value=str(vr.clamped_value if (not vr.is_valid and vr.clamped_value is not None) else vr.proposed_value),
                status="skipped",
                reason=f"Section '{section}' not found in setup file",
            ))
            continue

        # Determine effective value
        effective = vr.clamped_value if (not vr.is_valid and vr.clamped_value is not None) else vr.proposed_value

        old_value = ""
        if cp.has_option(section, "VALUE"):
            old_value = cp.get(section, "VALUE")

        new_val_str = str(effective)
        cp.set(section, "VALUE", new_val_str)

        outcomes.append(ChangeOutcome(
            section=section,
            parameter="VALUE",
            old_value=old_value,
            new_value=new_val_str,
        ))

    # Atomic write
    tmp_path = setup_path.with_suffix(".tmp")
    try:
        with open(str(tmp_path), "w", encoding="utf-8") as f:
            cp.write(f)
        os.replace(str(tmp_path), str(setup_path))
    except Exception:
        # Clean up tmp on error
        if tmp_path.is_file():
            tmp_path.unlink()
        raise

    return outcomes
