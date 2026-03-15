# Quickstart: Fix Setup Value Domain Conversion

**Feature Branch**: `034-fix-setup-value-domains` | **Date**: 2026-03-11

## Overview

This fix adds a pure-function conversion layer between AC's storage-format setup values and the physical-unit values that the LLM sees. It touches 7 existing files and adds 1 new module.

## Prerequisites

- conda env `ac-race-engineer` activated
- All 1410+ existing tests passing: `conda run -n ac-race-engineer pytest backend/tests/ -v`

## Files Changed

### New File
| File | Purpose |
|------|---------|
| `backend/ac_engineer/engineer/conversion.py` | Pure conversion functions: classify_parameter, to_physical, to_storage |

### Modified Files
| File | Change |
|------|--------|
| `backend/ac_engineer/engineer/models.py` | Add `show_clicks` and `storage_convention` fields to ParameterRange |
| `backend/ac_engineer/resolver/resolver.py` | Read SHOW_CLICKS in `_parse_setup_ini()`, set storage_convention |
| `backend/ac_engineer/resolver/cache.py` | Detect stale cache entries (missing show_clicks) |
| `backend/ac_engineer/engineer/summarizer.py` | Convert raw VALUES to physical units in `summarize_session()` after `_parse_setup_ini()` returns |
| `backend/ac_engineer/engineer/setup_writer.py` | Convert physical values back to storage in `apply_changes()` |
| `backend/ac_engineer/engineer/agents.py` | Pass parameter_ranges to summarizer for conversion; ensure value_before/value_after are physical |
| `backend/ac_engineer/engineer/__init__.py` | Export new conversion functions |

### New Test Files
| File | Purpose |
|------|---------|
| `backend/tests/engineer/test_conversion.py` | Unit tests for classify_parameter, to_physical, to_storage, round-trip |

## Data Flow (After Fix)

```
Car's setup.ini ──[resolver reads SHOW_CLICKS]──> ParameterRange (with show_clicks + storage_convention)
                                                          │
User's setup.ini ──[summarizer reads VALUE]──> raw storage value
                                                          │
                                               to_physical(raw, range)
                                                          │
                                                   physical value ──> SessionSummary.active_setup_parameters
                                                          │
                                                   LLM sees physical ──> proposes physical value_after
                                                          │
                                               validate_changes() ──> clamp in physical space
                                                          │
                                               to_storage(physical, range)
                                                          │
                                                   storage value ──> written to user's .ini
```

## Key Design Decisions

1. **Conversion is at boundaries, not pervasive**: Only two conversion points (summarizer inbound, writer outbound). All internal pipeline operates in physical units.
2. **Classification from car data only**: SHOW_CLICKS + section name prefix. No user values needed.
3. **Backward compatible**: New ParameterRange fields default to None. Old caches auto-invalidate lazily.
4. **Pure functions**: conversion.py has no I/O, no database, no LLM. Easily testable.

## Running Tests

```bash
# All existing tests (must still pass)
conda run -n ac-race-engineer pytest backend/tests/ -v

# Just conversion tests
conda run -n ac-race-engineer pytest backend/tests/engineer/test_conversion.py -v

# Just resolver tests (cache staleness)
conda run -n ac-race-engineer pytest backend/tests/resolver/ -v
```
