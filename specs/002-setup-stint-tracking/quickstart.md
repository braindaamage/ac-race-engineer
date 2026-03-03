# Quickstart: Setup Stint Tracking

**Feature**: 002-setup-stint-tracking

This feature modifies the existing telemetry capture app. It changes two behaviors:
1. How setup confidence is scored (location-first, not timestamp-first)
2. What setup data is written to the metadata JSON (history list, not flat fields)

No installation changes are needed if you already have feature 001 installed.

## What Changes

### Metadata Schema Change (Breaking)

The `.meta.json` sidecar no longer contains `setup_filename`, `setup_contents`, or `setup_confidence` as top-level fields. These are replaced by `setup_history`:

**Before (v1.0)**:
```json
{
  "setup_filename": "my_setup.ini",
  "setup_contents": "[TYRES]\n...",
  "setup_confidence": "low"
}
```

**After (v2.0)**:
```json
{
  "setup_history": [
    {
      "timestamp": "2026-03-03T14:30:00",
      "trigger": "session_start",
      "lap": 0,
      "filename": "my_setup.ini",
      "contents": "[TYRES]\n...",
      "confidence": "high"
    }
  ]
}
```

### Confidence Scoring Change

A setup file saved in `Documents/Assetto Corsa/setups/{car}/{track}/` will now always receive `"high"` confidence when it is the only file in that folder, regardless of age. Previously, files older than 60 seconds were penalized.

### Pit Stop Tracking (New Behavior)

When the driver pits and changes their setup, a second entry appears in `setup_history` on the next metadata write:

```json
{
  "setup_history": [
    {
      "timestamp": "2026-03-03T14:30:00",
      "trigger": "session_start",
      "lap": 0,
      "filename": "qualifying_setup.ini",
      "contents": "...",
      "confidence": "high"
    },
    {
      "timestamp": "2026-03-03T14:52:11",
      "trigger": "pit_exit",
      "lap": 8,
      "filename": "race_setup.ini",
      "contents": "...",
      "confidence": "high"
    }
  ]
}
```

## Files Changed

| File | Change Type | Description |
|---|---|---|
| `ac_app/ac_race_engineer/modules/setup_reader.py` | Modified | Confidence scoring rewritten (location-first) |
| `ac_app/ac_race_engineer/ac_race_engineer.py` | Modified | Pit exit detection; setup history building; updated metadata dict |
| `tests/telemetry_capture/unit/test_setup_reader.py` | Modified | Updated tests for new confidence rules |
| `tests/telemetry_capture/unit/test_setup_history.py` | New | Tests for pit exit detection and history accumulation |
| `specs/001-telemetry-capture/contracts/meta-json.md` | Updated | Deprecated note pointing to v2.0 contract |

## Running Tests

```bash
conda activate ac-race-engineer
cd /path/to/ac-race-engineer
pytest tests/telemetry_capture/unit/test_setup_reader.py -v
pytest tests/telemetry_capture/unit/test_setup_history.py -v
```

## Verifying Confidence Fix

1. Save a setup to `Documents/Assetto Corsa/setups/ks_ferrari_488_gt3/monza/race_v1.ini`
2. Drive a session
3. Open the resulting `.meta.json`
4. Confirm `setup_history[0]["confidence"]` is `"high"` (was `"low"` or `"medium"` before)

## Verifying Pit Stop Capture

1. Start a race or practice session
2. Return to pits
3. Open the setup screen and change at least one value
4. Save the setup (same or different name)
5. Exit the pits and continue driving
6. End the session
7. Open `.meta.json` — `setup_history` should contain 2+ entries

If you pit without changing anything, `setup_history` will still have only one entry. This is correct behavior (deduplication).

## Querying Per-Stint Setup

To find the setup that was active at a specific lap:

```python
import json

with open("session.meta.json") as f:
    meta = json.load(f)

def active_setup_at_lap(meta, lap):
    result = None
    for entry in meta["setup_history"]:
        if entry["lap"] <= lap:
            result = entry
    return result

# Which setup was active at lap 10?
print(active_setup_at_lap(meta, 10))
```
