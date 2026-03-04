# Public API Contract: `backend/ac_engineer/parser`

**Branch**: `003-telemetry-parser` | **Date**: 2026-03-03

This document defines the public Python API exposed by the parser package.
All functions listed here are importable from `ac_engineer.parser` and must
remain stable across internal refactors.

---

## Package Entry Point

```python
from ac_engineer.parser import parse_session, save_session, load_session
```

---

## Core Functions

### `parse_session`

```python
def parse_session(
    csv_path: pathlib.Path,
    meta_path: pathlib.Path,
) -> ParsedSession:
    """Parse a raw telemetry session into structured lap and corner segments.

    Reads the CSV telemetry file and its .meta.json sidecar, segments the
    continuous data stream into individual laps, classifies each lap, detects
    corners within each lap, associates setups with laps, and validates data
    quality.

    Args:
        csv_path: Absolute path to the session CSV file.
        meta_path: Absolute path to the session .meta.json sidecar.

    Returns:
        ParsedSession: Fully populated session with all laps, corners, setups,
            and quality warnings. Never raises for recoverable session-level
            issues (crash, incomplete data) — these are captured as warnings
            or incomplete lap classifications.

    Raises:
        FileNotFoundError: If csv_path or meta_path does not exist.
        ValueError: If the CSV is empty or the metadata JSON is malformed
            beyond recovery (unparseable JSON).
        ParserError: If a structural invariant is violated (e.g., lap_count
            channel missing from CSV).
    """
```

**Guarantees**:
- Never modifies `csv_path` or `meta_path`.
- Returns a result even if all laps are invalid.
- Returns a result even if `session_end`, `laps_completed`, and `total_samples`
  are `null` in the metadata (game crash recovery).
- If `session_end` is null, derives it from the last `timestamp` value in the CSV.

---

### `save_session`

```python
def save_session(
    session: ParsedSession,
    output_dir: pathlib.Path,
    base_name: str | None = None,
) -> pathlib.Path:
    """Serialize a ParsedSession to the intermediate Parquet + JSON format.

    Creates a subdirectory under output_dir named after the session, containing:
    - telemetry.parquet: full time-series data with lap_number column
    - session.json: all structured metadata, corners, setups, quality warnings

    Args:
        session: The ParsedSession to serialize.
        output_dir: Directory under which the session subdirectory will be created.
        base_name: Optional explicit subdirectory name. If None, derived from
            session.metadata.csv_filename (strip .csv extension).

    Returns:
        pathlib.Path: Path to the created session directory (containing both files).

    Raises:
        OSError: If output_dir cannot be written to.
        ValueError: If session is structurally inconsistent.
    """
```

---

### `load_session`

```python
def load_session(
    session_dir: pathlib.Path,
) -> ParsedSession:
    """Load a ParsedSession from a previously saved intermediate format.

    Reads telemetry.parquet and session.json from session_dir and reconstructs
    the full ParsedSession, structurally identical to the original parsed output.

    Args:
        session_dir: Path to the session directory (as returned by save_session).

    Returns:
        ParsedSession: Fully reconstructed session.

    Raises:
        FileNotFoundError: If session_dir, telemetry.parquet, or session.json
            is missing.
        ValueError: If the format_version in session.json is incompatible.
    """
```

---

## Models (from `ac_engineer.parser.models`)

```python
from ac_engineer.parser.models import (
    ParsedSession,
    SessionMetadata,
    LapSegment,
    CornerSegment,
    SetupEntry,
    SetupParameter,
    QualityWarning,
    LapClassification,
    WarnType,
)
```

### `LapClassification` (Literal enum)

```python
LapClassification = Literal["flying", "outlap", "inlap", "invalid", "incomplete"]
```

### `WarnType` (Literal enum)

```python
WarnType = Literal[
    "time_series_gap",
    "position_jump",
    "zero_speed_mid_lap",
    "incomplete",
    "duplicate_timestamp",
]
```

### `QualityWarning`

```python
class QualityWarning(BaseModel):
    warning_type: WarnType
    normalized_position: float   # 0.0–1.0
    description: str
```

### `SetupParameter`

```python
class SetupParameter(BaseModel):
    section: str
    name: str
    value: float | str
```

### `SetupEntry`

```python
class SetupEntry(BaseModel):
    lap_start: int               # lap number when active
    trigger: str                 # "session_start" | "pit_exit"
    confidence: str | None       # "high" | "medium" | "low" | None
    filename: str | None
    timestamp: str               # ISO 8601
    parameters: list[SetupParameter]
```

### `CornerSegment`

```python
class CornerSegment(BaseModel):
    corner_number: int           # 1-indexed, session-consistent
    entry_norm_pos: float
    apex_norm_pos: float
    exit_norm_pos: float
    apex_speed_kmh: float
    max_lat_g: float
    entry_speed_kmh: float
    exit_speed_kmh: float
```

### `LapSegment`

```python
class LapSegment(BaseModel):
    lap_number: int
    classification: LapClassification
    start_timestamp: float
    end_timestamp: float
    start_norm_pos: float
    end_norm_pos: float
    sample_count: int
    is_invalid: bool = False     # True if lap_invalid==1 on any sample or disqualifying anomaly
    data: dict[str, list]        # channel_name → list of values (NaN as None)
    corners: list[CornerSegment]
    active_setup: SetupEntry | None
    quality_warnings: list[QualityWarning]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert time-series data to a pandas DataFrame."""
        ...
```

### `SessionMetadata`

```python
class SessionMetadata(BaseModel):
    car_name: str
    track_name: str
    track_config: str
    track_length_m: float | None
    session_type: str
    tyre_compound: str
    driver_name: str
    air_temp_c: float | None
    road_temp_c: float | None
    session_start: str
    session_end: str | None
    laps_completed: int | None
    total_samples: int | None
    sample_rate_hz: float | None
    channels_available: list[str]
    channels_unavailable: list[str]
    sim_info_available: bool
    reduced_mode: bool
    csv_filename: str
    app_version: str
```

### `ParsedSession`

```python
class ParsedSession(BaseModel):
    metadata: SessionMetadata
    setups: list[SetupEntry]
    laps: list[LapSegment]

    @property
    def flying_laps(self) -> list[LapSegment]:
        """Return laps classified as 'flying'."""
        ...

    def lap_by_number(self, n: int) -> LapSegment | None:
        """Return the lap segment with the given lap number."""
        ...
```

---

## Internal Module APIs

These are NOT public API — they are implementation details callable from tests
but not guaranteed stable across refactors.

### `lap_segmenter.segment_laps(df: pd.DataFrame) -> list[pd.DataFrame]`

Splits the full session DataFrame by `lap_count` transitions.

### `lap_segmenter.classify_lap(lap_df: pd.DataFrame, is_last: bool) -> LapClassification`

Classifies a single lap DataFrame.

### `corner_detector.build_reference_map(reference_lap_df: pd.DataFrame, sample_rate: float) -> list[float]`

Returns ordered list of apex `normalized_position` values for the reference lap.

### `corner_detector.detect_corners(lap_df: pd.DataFrame, reference_apexes: list[float], g_threshold: float, steer_threshold: float) -> list[CornerSegment]`

Detects corners in a lap and aligns them to the reference map.

### `setup_parser.parse_ini(ini_text: str) -> list[SetupParameter]`

Parses raw INI text into a list of parameters.

### `quality_validator.validate_lap(lap_df: pd.DataFrame, sample_rate: float) -> list[QualityWarning]`

Returns all quality warnings for a single lap DataFrame.

---

## Error Types

```python
from ac_engineer.parser import ParserError

class ParserError(Exception):
    """Raised for unrecoverable structural errors in session data."""
    pass
```

---

## Usage Example

```python
from pathlib import Path
from ac_engineer.parser import parse_session, save_session, load_session

# Parse from raw files
session = parse_session(
    csv_path=Path("data/sessions/2026-03-02_1430_ks_ferrari_488_gt3_monza.csv"),
    meta_path=Path("data/sessions/2026-03-02_1430_ks_ferrari_488_gt3_monza.meta.json"),
)

# Inspect results
print(f"Flying laps: {len(session.flying_laps)}")
for lap in session.flying_laps:
    print(f"  Lap {lap.lap_number}: {len(lap.corners)} corners, "
          f"{len(lap.quality_warnings)} warnings")

# Save intermediate format
saved_dir = save_session(session, output_dir=Path("data/sessions"))

# Load it back (identical result)
reloaded = load_session(saved_dir)
```
