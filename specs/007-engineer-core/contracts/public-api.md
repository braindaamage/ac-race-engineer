# Public API Contract: Engineer Core (Phase 5.2)

**Branch**: `007-engineer-core` | **Date**: 2026-03-04

## Module: `ac_engineer.engineer`

### Public Imports

```python
from ac_engineer.engineer import (
    # Summarizer
    summarize_session,
    # Setup reader
    read_parameter_ranges,
    get_parameter_range,
    # Setup writer
    validate_changes,
    apply_changes,
    create_backup,
    # Models
    SessionSummary,
    LapSummary,
    CornerIssue,
    StintSummary,
    ParameterRange,
    ValidationResult,
    ChangeOutcome,
    SetupChange,
    DriverFeedback,
    EngineerResponse,
)
```

---

## Function Signatures

### summarizer.py

```python
def summarize_session(
    session: AnalyzedSession,
    config: ACConfig,
    *,
    max_corner_issues: int = 5,
) -> SessionSummary:
    """
    Compress an analyzed session into a compact, token-efficient summary.

    Pure function — does not mutate the input session. Deterministic: same
    input always produces identical output.

    Only flying laps (classification="flying") are included. Corner issues
    are sorted by severity descending and capped at max_corner_issues.

    Args:
        session: Fully analyzed session from the analyzer module.
        config: Application configuration (used for AC install path context).
        max_corner_issues: Maximum corner issues to include (default 5).

    Returns:
        SessionSummary with flying laps, signals, stints, and averages.

    Raises:
        Nothing — gracefully handles missing data with None fields.
    """
```

### setup_reader.py

```python
def read_parameter_ranges(
    ac_install_path: Path | None,
    car_name: str,
) -> dict[str, ParameterRange]:
    """
    Read setup parameter ranges from the car's data/setup.ini file.

    Parses the AC car data file to discover adjustable parameters and their
    min/max/step ranges.

    Args:
        ac_install_path: Path to AC installation directory (e.g., C:/Games/AC).
            If None or nonexistent, returns empty dict.
        car_name: Car folder name (e.g., "ks_bmw_m235i_racing").

    Returns:
        Dict mapping section name (e.g., "CAMBER_LF") to ParameterRange.
        Empty dict if path invalid, car not found, or data/setup.ini missing.

    Raises:
        Nothing — all errors result in empty or partial dict with logging.
    """


def get_parameter_range(
    ranges: dict[str, ParameterRange],
    section: str,
) -> ParameterRange | None:
    """
    Look up the range for a specific parameter section.

    Args:
        ranges: Dict returned by read_parameter_ranges().
        section: Section name to look up (e.g., "CAMBER_LF").

    Returns:
        ParameterRange if found, None otherwise.
    """
```

### setup_writer.py

```python
def validate_changes(
    ranges: dict[str, ParameterRange],
    proposed: list[SetupChange],
) -> list[ValidationResult]:
    """
    Validate proposed setup changes against known parameter ranges.

    Pure function — does not touch any files. Each proposal is validated
    independently and gets its own result.

    Args:
        ranges: Parameter ranges from read_parameter_ranges().
        proposed: List of SetupChange objects with section and value_after.

    Returns:
        List of ValidationResult, one per proposed change, in same order.

    Raises:
        Nothing — unknown parameters get is_valid=True with a warning.
    """


def create_backup(setup_path: Path) -> Path:
    """
    Create a timestamped backup of a setup file.

    Args:
        setup_path: Path to the .ini setup file to back up.

    Returns:
        Path to the created backup file (e.g., setup.ini.bak.20260304_153000).

    Raises:
        FileNotFoundError: If setup_path does not exist.
        OSError: If backup cannot be created.
    """


def apply_changes(
    setup_path: Path,
    changes: list[ValidationResult],
) -> list[ChangeOutcome]:
    """
    Apply validated changes to a setup .ini file atomically.

    Creates a backup first, then applies changes via atomic write
    (write to .tmp, os.replace). Preserves all unchanged sections
    and parameters.

    Args:
        setup_path: Path to the .ini setup file to modify.
        changes: List of validated changes (from validate_changes).

    Returns:
        List of ChangeOutcome showing old/new values for each change.

    Raises:
        ValueError: If changes list is empty.
        FileNotFoundError: If setup_path does not exist.
        OSError: If write fails (original file remains intact).
    """
```

---

## Integration Points

### Inputs (existing modules)

| Module | Import | Used By |
|--------|--------|---------|
| `ac_engineer.analyzer` | `AnalyzedSession`, `AnalyzedLap`, `StintMetrics`, `ConsistencyMetrics` | `summarizer.py` |
| `ac_engineer.knowledge` | `detect_signals()` | `summarizer.py` |
| `ac_engineer.config` | `ACConfig` | `summarizer.py` (second arg), `setup_reader.py` (caller passes path) |
| `ac_engineer.parser.models` | `SetupParameter` | `setup_writer.py` (for reading current values) |

### Outputs (consumed by future phases)

| Consumer | What it uses |
|----------|-------------|
| Phase 5.3 AI Agent | `SessionSummary` as context for LLM reasoning |
| Phase 5.3 AI Agent | `read_parameter_ranges()` to know valid bounds |
| Phase 5.3 AI Agent | `validate_changes()` + `apply_changes()` as Pydantic AI tools |
| Phase 6 API | All functions wrapped as FastAPI endpoints |
| Storage module | `SetupChange` / `ChangeOutcome` stored as recommendations |
