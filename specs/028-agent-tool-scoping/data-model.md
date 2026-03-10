# Data Model: Agent Tool Scoping

**Date**: 2026-03-10

## Entities

### DOMAIN_TOOLS (new constant)

A module-level dictionary mapping each agent domain to its permitted tool functions.

| Domain    | Tools                                        |
|-----------|----------------------------------------------|
| balance   | get_setup_range, get_corner_metrics, search_kb |
| tyre      | get_setup_range, get_lap_detail, search_kb     |
| aero      | get_setup_range, get_corner_metrics, search_kb |
| technique | get_lap_detail, get_corner_metrics, search_kb  |
| principal | get_lap_detail, get_corner_metrics             |

**Type**: `dict[str, list[Callable]]` — keys are domain name strings, values are lists of async tool functions from `tools.py`.

**Location**: `backend/ac_engineer/engineer/agents.py`, at module level after the existing `AERO_SECTIONS` constant.

**Validation**: If `_build_specialist_agent()` receives a domain not in `DOMAIN_TOOLS`, it raises `KeyError` (Python's default dict behavior — no silent fallback).

## No Schema Changes

- No database schema changes
- No API contract changes
- No new Pydantic models
- No frontend changes
