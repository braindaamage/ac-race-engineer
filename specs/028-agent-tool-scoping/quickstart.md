# Quickstart: Agent Tool Scoping

**Date**: 2026-03-10

## What changes

1. **`backend/ac_engineer/engineer/agents.py`** — Add `DOMAIN_TOOLS` constant and update `_build_specialist_agent()` to use it
2. **`backend/ac_engineer/engineer/__init__.py`** — Export `DOMAIN_TOOLS`
3. **`backend/tests/engineer/test_agents.py`** — Update `test_agent_registers_4_tools` to assert per-domain tool sets

## How to verify

```bash
# Run all engineer tests
conda run -n ac-race-engineer pytest backend/tests/engineer/ -v

# Run full backend test suite
conda run -n ac-race-engineer pytest backend/tests/ -v
```

## Key constraint

The `DOMAIN_TOOLS` mapping must exactly match what each `skills/*.md` file documents:

| Domain    | search_kb | get_setup_range | get_lap_detail | get_corner_metrics |
|-----------|-----------|-----------------|----------------|--------------------|
| balance   | yes       | yes             | —              | yes                |
| tyre      | yes       | yes             | yes            | —                  |
| aero      | yes       | yes             | —              | yes                |
| technique | yes       | —               | yes            | yes                |
| principal | —         | —               | yes            | yes                |
