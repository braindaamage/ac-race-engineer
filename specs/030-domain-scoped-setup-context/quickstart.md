# Quickstart: Domain-Scoped Setup Context

**Feature**: 030-domain-scoped-setup-context
**Date**: 2026-03-11

## What Changes

One file modified: `backend/ac_engineer/engineer/agents.py`
One test file modified: `backend/tests/engineer/test_agents.py`

## How to Implement

### Step 1: Add DOMAIN_PARAMS constant

In `agents.py`, after the existing `DOMAIN_TOOLS` constant (line ~86), add:

```python
DOMAIN_PARAMS: dict[str, tuple[str, ...]] = {
    "balance": (
        "SPRING_RATE", "DAMP_BUMP", "DAMP_FAST_BUMP", "DAMP_REBOUND",
        "DAMP_FAST_REBOUND", "ARB_", "RIDE_HEIGHT", "BRAKE_POWER", "BRAKE_BIAS",
    ),
    "tyre": ("PRESSURE_", "CAMBER_", "TOE_OUT_", "TOE_IN_"),
    "aero": ("WING_", "SPLITTER_"),
    "technique": (),
    "principal": (),
}
```

### Step 2: Add domain parameter to _build_user_prompt

Change the function signature to accept `domain: str | None = None`.

Before the setup parameters serialization block (line ~354), add filtering logic:

- If `domain` is not None and `DOMAIN_PARAMS[domain]` is empty → skip the setup parameters block entirely
- If `domain` is not None → filter `active_setup_parameters` to only sections matching the domain's prefixes; if domain is `"balance"`, also include sections not matching any domain's prefixes
- If `domain` is None → include all parameters (backward compatible)

### Step 3: Pass domain from analyze_with_engineer

In the specialist loop (line ~574), change:
```python
user_prompt = _build_user_prompt(summary, domain_signals, domain_fragments)
```
to:
```python
user_prompt = _build_user_prompt(summary, domain_signals, domain_fragments, domain=domain)
```

### Step 4: Add tests

Add a `TestDomainScopedParams` class to `test_agents.py` with tests for:
- Each domain receives only its expected sections
- Technique/principal domains receive no setup parameters
- Unrecognized sections fall back to balance
- SessionSummary is not mutated
- `domain=None` preserves all parameters (backward compat)
- Empty active_setup_parameters preserves existing behavior

## How to Test

```bash
conda activate ac-race-engineer
pytest backend/tests/engineer/test_agents.py -v
pytest backend/tests/engineer/ -v  # full engineer suite for regression
```

## Dependencies

None. No new packages, no API changes, no frontend changes.
