# Implementation Plan: Telemetry Parser

**Branch**: `003-telemetry-parser` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-telemetry-parser/spec.md`

---

## Summary

Build `backend/ac_engineer/parser/` — a pure-computation Python package that
reads raw session CSV files (82 channels, ~22–25 Hz) and `.meta.json` sidecars
produced by the Phase 1/1.5 in-game capture app, and returns a fully structured
`ParsedSession` Pydantic model containing per-lap segments (with time-series
data, lap classification, active setup, and quality warnings) and per-corner
segments (with consistent session-wide numbering).

The intermediate representation (Parquet + JSON sidecar) enables downstream
consumers (Analyzer, AI Engineer, Desktop App) to access parsed data without
re-parsing the raw CSV.

---

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: `pandas` (CSV I/O, time-series slicing), `numpy`
(percentile thresholds, NaN handling), `pyarrow` (Parquet I/O),
`pydantic` v2 (model definitions and validation)
**Storage**: Parquet (per-session time series) + JSON sidecar (structured
metadata, corners, setups, quality warnings); source CSV and `.meta.json`
are read-only inputs
**Testing**: `pytest` in `backend/tests/parser/`; unit tests per module,
integration tests with fixture session files
**Target Platform**: Windows 11 (development), same as AC game environment
**Project Type**: Python library module (no HTTP, no CLI, pure computation)
**Performance Goals**: 20-lap session parsed in < 5 seconds (per SC-001)
**Constraints**: Read-only on source files; no HTTP imports; no hardcoded
car/track/parameter names; must work without a running FastAPI server
**Scale/Scope**: Single-session files; one Parquet output per session;
no real-time or streaming operation

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | ✅ PASS | Source files never modified; bad laps flagged with warnings, never dropped; NaN channels marked unavailable |
| II. Car-Agnostic Design | ✅ PASS | Zero hardcoded car names; `.ini` parser is generic; corner detection is percentile-based (self-calibrating) |
| III. Setup File Autonomy | ✅ PASS | Parser reads `.ini` via `setup_history.contents` (already in memory from metadata); no direct `.ini` file writes in parser scope |
| IV. LLM as Interpreter | ✅ PASS | Parser is pure deterministic computation; no LLM calls anywhere in this module |
| V. Educational Explanations | N/A | Parser produces data structures, not user-facing explanations |
| VI. Incremental Changes | N/A | Parser reads, does not write setups |
| VII. CLI-First MVP | ✅ PASS | Library module is CLI-callable without server; no desktop GUI dependency |
| VIII. API-First Design | ✅ PASS | All logic in `ac_engineer/parser/`; zero HTTP imports; FastAPI routes (Phase 6) will call `parse_session()` as a thin wrapper |
| IX. Separation of Concerns | ✅ PASS | Parser is pure `ac_engineer/` computation; no `api/` imports; no frontend concerns |
| X. Desktop App Stack | N/A | Phase 7; parser is agnostic to how its output is displayed |
| XI. LLM Provider Abstraction | N/A | No LLM calls in parser |

**Constitution gate: PASS.** No violations. No complexity tracking required.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-telemetry-parser/
├── plan.md              # This file
├── research.md          # Phase 0 — schema, algorithms, format decisions
├── data-model.md        # Phase 1 — entity definitions, relationships, invariants
├── contracts/
│   └── public-api.md    # Phase 1 — public Python API contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (all pass)
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   ├── __init__.py
│   └── parser/
│       ├── __init__.py          # Exports: parse_session, save_session, load_session
│       ├── models.py            # Pydantic models: ParsedSession, LapSegment, etc.
│       ├── session_parser.py    # Main entry point; orchestrates the pipeline
│       ├── lap_segmenter.py     # Lap splitting by lap_count + classification logic
│       ├── corner_detector.py   # Percentile-based corner detection + reference map
│       ├── setup_parser.py      # .ini text → list[SetupParameter]
│       ├── quality_validator.py # Time-series quality checks → list[QualityWarning]
│       └── cache.py             # save_session / load_session (Parquet + JSON)
└── tests/
    └── parser/
        ├── __init__.py
        ├── conftest.py           # Shared fixtures: session DataFrames, metadata dicts
        ├── fixtures/             # Sample CSV and .meta.json files for integration tests
        │   ├── minimal_session.csv
        │   ├── minimal_session.meta.json
        │   └── ...
        ├── test_models.py        # Pydantic model validation tests
        ├── test_lap_segmenter.py # Segmentation + classification unit tests
        ├── test_corner_detector.py
        ├── test_setup_parser.py
        ├── test_quality_validator.py
        ├── test_cache.py
        └── test_session_parser.py  # Integration: CSV + JSON → ParsedSession
```

**Structure Decision**: Single `backend/` top-level following CLAUDE.md
architecture. The existing `src/` directory contains empty stubs from an earlier
scaffolding phase and is not touched by this feature. `backend/ac_engineer/` is
the authoritative Python package location per the project constitution.

**Note**: The repository root `pyproject.toml` is currently empty. The first
implementation task must add `backend/` to the Python path (via `pyproject.toml`
or a `backend/pyproject.toml`) so `import ac_engineer.parser` resolves correctly
from `backend/tests/`.

---

## Pipeline Design

The `parse_session()` function executes this pipeline sequentially:

```
CSV file + .meta.json
         │
         ▼
1. MetadataReader          Read .meta.json; detect v1.0 vs v2.0; derive null fields
         │                 from CSV if needed (crash recovery)
         ▼
2. CSVReader               Read CSV with pandas; validate required columns present;
         │                 detect channels_unavailable (all-NaN columns)
         ▼
3. LapSegmenter            Group rows by lap_count; produce list of per-lap DataFrames
         │
         ▼
4. LapClassifier           Apply classification rules (outlap/inlap/invalid/flying/incomplete)
         │                 per lap DataFrame
         ▼
5. QualityValidator        Per-lap quality checks → attach QualityWarning list
         │
         ▼
6. SetupParser             Parse each setup_history[].contents → list[SetupParameter]
         │
         ▼
7. SetupAssociator         For each lap N, find most recent entry with lap_start ≤ N
         │
         ▼
8. CornerDetector          Compute session-wide thresholds; detect corners per lap;
         │                 build reference map from first flying lap; assign
         │                 session-consistent corner numbers
         ▼
9. ModelAssembler          Convert DataFrames to dict[str, list]; build Pydantic models
         │
         ▼
ParsedSession
```

---

## Module Responsibilities

### `models.py`
- Defines all Pydantic v2 models: `QualityWarning`, `SetupParameter`,
  `SetupEntry`, `CornerSegment`, `LapSegment`, `SessionMetadata`, `ParsedSession`
- `LapSegment.to_dataframe()`: reconstructs `pd.DataFrame` from `data` dict
- `ParsedSession.flying_laps`, `ParsedSession.lap_by_number(n)` convenience props
- `ParserError` exception class

### `session_parser.py`
- `parse_session(csv_path, meta_path) -> ParsedSession` — public entry point
- Orchestrates all other modules in pipeline order
- Handles top-level error translation (FileNotFoundError, ValueError, ParserError)
- Graceful crash recovery: if `session_end`/`laps_completed`/`total_samples` are
  null, derives them from the CSV after reading

### `lap_segmenter.py`
- `segment_laps(df: pd.DataFrame) -> list[pd.DataFrame]`
  Groups rows by `lap_count` value; preserves temporal order
- `classify_lap(lap_df: pd.DataFrame, is_first: bool, is_last: bool) -> LapClassification`
  Applies the 5-rule classification state machine (see data-model.md)
- Handles edge cases: zero-row DataFrames, single-row laps, lap_count column missing

### `corner_detector.py`
- `compute_session_thresholds(session_df: pd.DataFrame, sample_rate: float) -> dict`
  Returns `{"g_threshold": float, "steer_threshold": float}` from 80th/70th
  percentiles of the full session data
- `build_reference_map(lap_df: pd.DataFrame, thresholds: dict, sample_rate: float) -> list[float]`
  Returns ordered apex `normalized_position` values for the reference lap
- `detect_corners(lap_df: pd.DataFrame, reference_apexes: list[float], thresholds: dict, sample_rate: float) -> list[CornerSegment]`
  Runs the cornering-sample detection, merging, filtering, and reference alignment
- Reduced-mode fallback: if `g_lat` column is all NaN, uses `steering` only

### `setup_parser.py`
- `parse_ini(ini_text: str) -> list[SetupParameter]`
  Parses raw INI text generically; no hardcoded parameter names
  Returns empty list for None/empty input (not an error)
- `associate_setup(lap_number: int, setup_entries: list[SetupEntry]) -> SetupEntry | None`
  Lookup: most recent entry where `lap_start <= lap_number`

### `quality_validator.py`
- `validate_lap(lap_df: pd.DataFrame, sample_rate: float, is_last: bool) -> list[QualityWarning]`
  Returns all quality warnings for one lap DataFrame
- Checks (configurable constants at module level for testing):
  - `TIME_GAP_THRESHOLD = 0.5` seconds
  - `POSITION_JUMP_THRESHOLD = 0.05` normalized units
  - `ZERO_SPEED_THRESHOLD = 1.0` km/h, `ZERO_SPEED_DURATION = 3.0` seconds
  - Zero-speed window: norm_pos between `ZERO_SPEED_MIN = 0.10` and `ZERO_SPEED_MAX = 0.90`

### `cache.py`
- `save_session(session: ParsedSession, output_dir: Path, base_name: str | None = None) -> Path`
  Writes `telemetry.parquet` and `session.json` to a subdirectory
- `load_session(session_dir: Path) -> ParsedSession`
  Reads both files and reconstructs the full model
- Parquet schema: `lap_number` (int32) + 82 channel columns
- JSON schema: `format_version`, `session`, `setups`, `laps` (without `data`)

---

## Key Design Decisions

### D1: DataFrame → `dict[str, list]` in Pydantic model

Pydantic v2 cannot natively serialize `pd.DataFrame`. Storing lap time series
as `dict[str, list]` keeps models fully JSON-serializable and enables clean
Parquet round-trips via `pd.DataFrame(lap.data)`.

### D2: Single Parquet file per session (not per lap)

One Parquet file with a `lap_number` column is simpler than N per-lap files:
fewer filesystem operations, no glob logic, easier Analyzer consumption via
`df.groupby("lap_number")` or `df[df.lap_number == N]`.

### D3: Session-wide corner thresholds (not per-lap)

Computing `g_lat` percentiles across the entire session (not per-lap) gives
stable, consistent thresholds unaffected by individual lap data quality issues.
An invalid lap with unusual G-forces does not distort the thresholds.

### D4: Reference corner map from first flying lap

If no flying lap exists, fall back to first outlap. If no flying or outlap
exists (pure pit session), corner detection is skipped and all laps have
`corners = []`. This is not an error.

### D5: `is_invalid` boolean field alongside `classification`

`LapSegment` carries both `classification` (pit-lane logic: outlap/inlap/incomplete/invalid/flying)
and `is_invalid: bool` (data-quality flag: True whenever any sample has `lap_invalid==1` or a
disqualifying anomaly is detected, regardless of classification).

The priority order (outlap/inlap > incomplete > invalid > flying) means an outlap where the driver
cuts a lap is `classification="outlap"`, `is_invalid=True`. The `invalid` classification is reserved
for non-pit laps with no closing transition where `lap_invalid` was set. This dual-field approach
gives downstream consumers independent access to lap type and data quality without ambiguity.

### D6: pyproject.toml setup

A `backend/pyproject.toml` using `hatchling` (or `setuptools`) will be created
with `packages = ["ac_engineer"]` and `src_layout = false`. Tests are run from
the `backend/` directory: `conda run -n ac-race-engineer pytest tests/`.

---

## Dependency Installation

```bash
conda activate ac-race-engineer
pip install pandas numpy pyarrow pydantic
```

All four dependencies are already listed in the project constitution's technology
stack (`pandas`, `numpy`) or implied by the Parquet decision (`pyarrow`,
`pydantic`). No new dependencies require constitution amendment.

---

## Testing Strategy

### Unit Tests (per module)

| File | Coverage target |
|------|----------------|
| `test_lap_segmenter.py` | Segmentation boundaries, each classification type, edge cases (0 rows, 1 row, all-same lap_count) |
| `test_corner_detector.py` | Threshold computation, merge logic, chicane separation, oval (2 corners), reduced mode fallback |
| `test_setup_parser.py` | Standard INI, sections only, no values, non-numeric values, empty/None input, mod parameters |
| `test_quality_validator.py` | Each of the 5 warning types, threshold boundary values, no warnings on clean data |
| `test_cache.py` | Round-trip save/load identity for all model fields, NaN preservation, format_version check |
| `test_models.py` | Pydantic validation (type coercion, field constraints), `to_dataframe()`, `flying_laps` property |

### Integration Tests (`test_session_parser.py`)

Using fixture CSV + meta.json files in `tests/parser/fixtures/`:

| Fixture | Scenario |
|---------|----------|
| `minimal_session` | 1 outlap + 1 flying lap + 1 inlap, clean data |
| `all_invalid` | All laps flagged invalid by AC |
| `zero_laps` | Driver quit immediately (0 lap_count transitions) |
| `crash_session` | session_end/laps_completed/total_samples all null in meta |
| `legacy_v1_meta` | Flat setup fields instead of setup_history array |
| `multi_setup` | 3 setup changes across 15 laps |
| `reduced_mode` | 28 channels all NaN (sim_info unavailable) |
| `data_gaps` | Intentional time gap + position jump inserted into CSV |

### Test Fixtures Strategy

Fixture CSV files are generated programmatically in `conftest.py` using known
inputs (not captured from the game). This makes tests deterministic and
independent of AC installation. Real session files in `data/sessions/` are used
only for optional smoke tests that are skipped in CI.

---

## Out of Scope

- FastAPI endpoint wrapping `parse_session()` — Phase 6
- CLI command for parsing — Phase 7 (CLI-first)
- Real-time/streaming operation — explicitly excluded (constitution §VIII)
- Writing/modifying setup `.ini` files — Phase 5 (Engineer)
- Metric computation from lap segments — Phase 3 (Analyzer)
- Migrating or removing the existing `src/` stubs — separate cleanup task

---

## Complexity Tracking

No constitution violations. Section not required.
