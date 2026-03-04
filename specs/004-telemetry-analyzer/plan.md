# Implementation Plan: Telemetry Analyzer

**Branch**: `004-telemetry-analyzer` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-telemetry-analyzer/spec.md`

## Summary

Build a pure-computation analyzer module (`backend/ac_engineer/analyzer/`) that takes ParsedSession objects from the Phase 2 parser and produces AnalyzedSession objects containing structured performance metrics at four levels: per-lap, per-corner, per-stint (with trends and cross-stint comparison), and session-wide consistency. Uses Pydantic v2 models, numpy/pandas for computation, and scipy.stats.linregress for trend analysis.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: pandas, numpy, scipy (new), pydantic>=2.0
**Storage**: N/A (pure computation, no I/O)
**Testing**: pytest with programmatic fixtures + real session validation
**Target Platform**: Windows (dev), cross-platform compatible
**Project Type**: Library module within backend package
**Performance Goals**: Process a 5-lap session in < 1 second
**Constraints**: No I/O, no HTTP, no LLM calls, deterministic output
**Scale/Scope**: ~82 channels × ~3000 samples/lap × 5-15 laps typical

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Data Integrity First | PASS | Analyzer validates channel availability, marks unavailable metrics as None (FR-021) |
| II. Car-Agnostic Design | PASS | No hardcoded car logic, generic channel names only (FR-022) |
| III. Setup File Autonomy | N/A | Analyzer does not read/write setup files |
| IV. LLM as Interpreter | PASS | Pure deterministic Python computation, no LLM calls (FR-024) |
| V. Educational Explanations | N/A | Analyzer computes metrics; explanations are Phase 5 |
| VI. Incremental Changes | N/A | Analyzer does not modify setups |
| VII. CLI-First MVP | PASS | Library module callable from CLI, API, or tests |
| VIII. API-First Design | PASS | Pure Python functions in ac_engineer/, no HTTP awareness (FR-023) |
| IX. Separation of Concerns | PASS | Analyzer is pure computation layer, imports only from parser models |
| X. Desktop App Stack | N/A | No desktop app work |
| XI. LLM Provider Abstraction | N/A | No LLM usage |

**Post-design re-check**: All gates still pass. The data model uses only Pydantic v2 models and numpy/pandas/scipy for computation. No constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-telemetry-analyzer/
├── plan.md              # This file
├── research.md          # Phase 0: technical decisions
├── data-model.md        # Phase 1: all entity definitions
├── quickstart.md        # Phase 1: developer quickstart
├── contracts/
│   └── public-api.md    # Phase 1: public API contract
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    parser/              # Existing — Phase 2 (read-only dependency)
      models.py          # ParsedSession, LapSegment, CornerSegment, etc.
    analyzer/            # NEW — Phase 3
      __init__.py        # Public API: analyze_session + re-exports
      models.py          # Pydantic v2 models (AnalyzedSession hierarchy)
      lap_analyzer.py    # Per-lap metric computation (FR-002 through FR-010)
      corner_analyzer.py # Per-corner metric computation (FR-011 through FR-015)
      stint_analyzer.py  # Stint grouping, aggregation, trends, comparison (FR-016 through FR-018)
      consistency.py     # Session-wide consistency analysis (FR-019)
      _utils.py          # Shared helpers: NaN-safe stats, channel extraction
  tests/
    analyzer/            # NEW
      __init__.py
      conftest.py        # Programmatic ParsedSession/LapSegment builders
      test_models.py     # Model construction and validation
      test_lap_analyzer.py
      test_corner_analyzer.py
      test_stint_analyzer.py
      test_consistency.py
      test_session_analyzer.py  # Full pipeline integration tests
      test_real_session.py      # Validation with real BMW M235i data
```

**Structure Decision**: Follows the same pattern as `parser/` — one module per responsibility, shared models in `models.py`, public API via `__init__.py`. Test structure mirrors source structure with a dedicated `conftest.py` for fixtures.

## Module Responsibilities

### `_utils.py` — Shared Computation Helpers

Internal module providing NaN-safe statistical functions and channel data extraction.

- `safe_mean(series)` → `float | None`: Returns None if all NaN
- `safe_max(series)` → `float | None`: Returns None if all NaN
- `safe_min(series)` → `float | None`: Returns None if all NaN
- `channel_available(df, column)` → `bool`: True if column exists and has non-NaN data
- `extract_corner_data(df, entry_pos, exit_pos)` → `DataFrame`: Filters DataFrame by normalized position range (handles wrap-around)
- `compute_trend_slope(values)` → `float | None`: Linear regression slope via scipy.stats.linregress; None if < 2 points

### `models.py` — Pydantic v2 Data Models

All output models as defined in [data-model.md](data-model.md). Follows same patterns as `parser/models.py`:
- `from __future__ import annotations`
- Modern union syntax: `float | None`
- `BaseModel` with default values
- No methods beyond standard Pydantic

### `lap_analyzer.py` — Per-Lap Metrics

Single function: `analyze_lap(lap: LapSegment, metadata: SessionMetadata) -> LapMetrics`

Computes all lap-level metric groups by extracting the lap's DataFrame and applying statistical aggregations:
- TimingMetrics: timestamp subtraction + sector boundary interpolation
- TyreMetrics: per-wheel, per-zone temp stats + pressure + wear + balance
- GripMetrics: slip angle/ratio stats + G-force peaks
- DriverInputMetrics: threshold-based percentages + gear distribution
- SpeedMetrics: max/min/avg with pit filter
- FuelMetrics: start/end delta (or None)
- SuspensionMetrics: per-wheel travel stats

### `corner_analyzer.py` — Per-Corner Metrics

Single function: `analyze_corner(corner: CornerSegment, lap_df: DataFrame) -> CornerMetrics`

Extracts the corner's time series window and computes:
- CornerPerformance: speeds at entry/apex/exit positions, duration
- CornerGrip: lateral G stats, understeer ratio
- CornerTechnique: brake/throttle application points, trail braking
- CornerLoading: peak wheel loads (or None)

### `stint_analyzer.py` — Stint Analysis

Three functions:
- `group_stints(laps: list[AnalyzedLap]) -> list[StintMetrics]`: Groups laps by active_setup identity
- `compute_stint_trends(stint: StintMetrics, laps: list[AnalyzedLap]) -> StintTrends | None`: Linear trends within a stint
- `compare_stints(stint_a: StintMetrics, stint_b: StintMetrics, setup_a: SetupEntry | None, setup_b: SetupEntry | None) -> StintComparison`: Cross-stint metric deltas + setup parameter diffs

### `consistency.py` — Consistency Analysis

Single function: `compute_consistency(laps: list[AnalyzedLap]) -> ConsistencyMetrics | None`

Operates on flying laps only. Computes:
- Lap time statistics (stddev, best, worst, trend)
- Per-corner variance (apex speed, brake point) across laps

### `__init__.py` — Public API

Orchestrates the full pipeline:
```python
def analyze_session(session: ParsedSession) -> AnalyzedSession:
    # 1. Analyze each lap (lap_analyzer + corner_analyzer)
    # 2. Group into stints (stint_analyzer)
    # 3. Compute consistency (consistency)
    # 4. Assemble AnalyzedSession
```

Re-exports all public models.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
