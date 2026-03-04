# Quickstart: Engineer Core (Phase 5.2)

**Branch**: `007-engineer-core` | **Date**: 2026-03-04

## Prerequisites

```bash
conda activate ac-race-engineer
# No new dependencies to install — stdlib + pydantic only
```

## Usage Examples

### 1. Summarize a Session

```python
from ac_engineer.analyzer import analyze_session
from ac_engineer.parser import parse_session
from ac_engineer.engineer import summarize_session

# Parse and analyze
parsed = parse_session("data/sessions/session_001.csv", "data/sessions/session_001.meta.json")
analyzed = analyze_session(parsed)

# Summarize for LLM consumption
summary = summarize_session(analyzed)

print(summary.car_name)           # "ks_bmw_m235i_racing"
print(summary.flying_lap_count)   # 10
print(summary.best_lap_time_s)    # 92.345
print(summary.signals)            # ["high_understeer", "tyre_temp_spread_high"]

# Token-efficient JSON for LLM
json_str = summary.model_dump_json(exclude_none=True)
```

### 2. Read Parameter Ranges

```python
from pathlib import Path
from ac_engineer.engineer import read_parameter_ranges, get_parameter_range

# Discover what this car supports
ranges = read_parameter_ranges(
    ac_install_path=Path("C:/Games/Assetto Corsa"),
    car_name="ks_bmw_m235i_racing",
)

# Look up a specific parameter
camber = get_parameter_range(ranges, "CAMBER_LF")
if camber:
    print(f"Camber LF: {camber.min} to {camber.max}, step {camber.step}")

# AC not installed? No problem — empty dict
ranges = read_parameter_ranges(ac_install_path=None, car_name="any_car")
assert ranges == {}
```

### 3. Validate and Apply Changes

```python
from pathlib import Path
from ac_engineer.engineer import (
    read_parameter_ranges,
    validate_changes,
    apply_changes,
)

# Get ranges for this car
ranges = read_parameter_ranges(Path("C:/Games/AC"), "ks_bmw_m235i_racing")

# Validate proposed changes
results = validate_changes(ranges, [
    ("CAMBER_LF", -2.5),   # Within range → valid
    ("CAMBER_RF", -7.0),   # Out of range → clamped to min
    ("CUSTOM_MOD", 42.0),  # No range data → no_range warning
])

for r in results:
    print(f"{r.section}: {r.status} → {r.accepted_value}")

# Apply validated changes to setup file
setup_path = Path("C:/Users/me/Documents/Assetto Corsa/setups/ks_bmw_m235i_racing/monza/race.ini")
outcomes = apply_changes(setup_path, results)

for o in outcomes:
    print(f"{o.section}: {o.old_value} → {o.new_value}")
# Backup created at: race.ini.bak.20260304_153000
```

## Running Tests

```bash
conda activate ac-race-engineer

# All engineer tests
pytest backend/tests/engineer/ -v

# Individual test modules
pytest backend/tests/engineer/test_models.py -v
pytest backend/tests/engineer/test_summarizer.py -v
pytest backend/tests/engineer/test_setup_reader.py -v
pytest backend/tests/engineer/test_setup_writer.py -v

# Full test suite (all phases)
pytest backend/tests/ -v
```

## Module Structure

```
backend/ac_engineer/engineer/
├── __init__.py          # Public exports (all functions + models)
├── models.py            # 12 Pydantic v2 models
├── summarizer.py        # summarize_session()
├── setup_reader.py      # read_parameter_ranges(), get_parameter_range()
└── setup_writer.py      # validate_changes(), apply_changes(), create_backup()
```
