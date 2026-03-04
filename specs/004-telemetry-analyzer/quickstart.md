# Quickstart: Telemetry Analyzer Development

**Feature**: 004-telemetry-analyzer
**Branch**: `004-telemetry-analyzer`

## Environment Setup

```bash
# Activate conda environment (required for all Python commands)
conda activate ac-race-engineer

# Install scipy (new dependency for linear regression)
cd backend
pip install scipy

# Verify existing dependencies
python -c "import pandas, numpy, pydantic; print('OK')"
```

## Project Structure

```
backend/
  ac_engineer/
    analyzer/
      __init__.py          # Public API: analyze_session + model re-exports
      models.py            # Pydantic v2 models (AnalyzedSession, LapMetrics, etc.)
      lap_analyzer.py      # Per-lap metric computation
      corner_analyzer.py   # Per-corner metric computation
      stint_analyzer.py    # Stint aggregation, trends, cross-stint comparison
      consistency.py       # Session-wide consistency analysis
      _utils.py            # Shared helpers (NaN-safe stats, channel extraction)
  tests/
    analyzer/
      __init__.py
      conftest.py          # Programmatic fixtures (ParsedSession builders)
      test_models.py       # Model construction + validation tests
      test_lap_analyzer.py # Lap metric computation tests
      test_corner_analyzer.py
      test_stint_analyzer.py
      test_consistency.py
      test_session_analyzer.py  # Integration: full pipeline tests
      test_real_session.py      # Validation against real BMW M235i data
```

## Running Tests

```bash
# From repo root
conda run -n ac-race-engineer pytest backend/tests/analyzer/ -v

# Single test file
conda run -n ac-race-engineer pytest backend/tests/analyzer/test_lap_analyzer.py -v

# With coverage
conda run -n ac-race-engineer pytest backend/tests/analyzer/ -v --cov=ac_engineer.analyzer
```

## Usage Example

```python
from ac_engineer.parser import parse_session
from ac_engineer.analyzer import analyze_session

# Parse a session (Phase 2)
session = parse_session(csv_path, meta_path)

# Analyze it (Phase 3)
result = analyze_session(session)

# Access lap metrics
for lap in result.laps:
    print(f"Lap {lap.lap_number} ({lap.classification}): {lap.metrics.timing.lap_time_s:.3f}s")
    print(f"  Max speed: {lap.metrics.speed.max_speed:.1f} km/h")
    print(f"  Full throttle: {lap.metrics.driver_inputs.full_throttle_pct:.1f}%")

# Access corner metrics
for corner in result.laps[0].corners:
    print(f"Corner {corner.corner_number}: apex {corner.performance.apex_speed_kmh:.1f} km/h")
    print(f"  Understeer ratio: {corner.grip.understeer_ratio:.2f}")

# Access stint comparison
for comp in result.stint_comparisons:
    print(f"Stint {comp.stint_a_index} → {comp.stint_b_index}")
    print(f"  Lap time delta: {comp.metric_deltas.lap_time_delta_s:+.3f}s")
    for change in comp.setup_changes:
        print(f"  Setup: [{change.section}] {change.name}: {change.value_a} → {change.value_b}")
```

## Key Conventions

- **Wheel keys**: Always lowercase `"fl"`, `"fr"`, `"rl"`, `"rr"`
- **Units**: km/h for speeds, °C for temps, PSI for pressures, seconds for times
- **None = unavailable**: Metric is None when required channel data is NaN
- **Percentages**: 0.0–100.0 range (not 0.0–1.0)
- **Deterministic**: Same input always produces identical output
