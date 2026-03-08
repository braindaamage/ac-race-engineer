# Quickstart: ACD File Reader

**Feature**: 021-acd-reader | **Date**: 2026-03-08

## Prerequisites

- Python 3.11+ in conda env `ac-race-engineer`
- No additional packages required (stdlib only)

## Setup

No setup required. The module has zero external dependencies.

```bash
conda activate ac-race-engineer
```

## Usage

```python
from pathlib import Path
from ac_engineer.acd_reader import read_acd

# Read a car's data.acd
result = read_acd(
    Path("C:/Games/Assetto Corsa/content/cars/ks_ferrari_488_gt3/data.acd"),
    "ks_ferrari_488_gt3"
)

if result.ok:
    # result.files is dict[str, bytes]
    for name, content in result.files.items():
        print(f"  {name}: {len(content)} bytes")

    # Decode a specific file
    if "car.ini" in result.files:
        car_ini = result.files["car.ini"].decode("utf-8")
        print(car_ini)
else:
    print(f"Failed: {result.error}")
```

## Running Tests

```bash
conda activate ac-race-engineer
pytest backend/tests/acd_reader/ -v
```

## File Layout

```
backend/ac_engineer/acd_reader/
├── __init__.py      # Public exports: read_acd, AcdResult
└── reader.py        # Implementation

backend/tests/acd_reader/
├── conftest.py      # Test fixtures (ACD archive builder)
└── test_reader.py   # All tests
```
