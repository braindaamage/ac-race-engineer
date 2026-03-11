# Data Model: Domain-Scoped Setup Context

**Feature**: 030-domain-scoped-setup-context
**Date**: 2026-03-11

## Entities

### DOMAIN_PARAMS (new constant)

A module-level dictionary mapping each agent domain to a tuple of section name prefixes.

```
DOMAIN_PARAMS: dict[str, tuple[str, ...]]

Keys: "balance", "tyre", "aero", "technique", "principal"
Values: tuple of string prefixes used with str.startswith()

balance  → ("SPRING_RATE", "DAMP_BUMP", "DAMP_FAST_BUMP", "DAMP_REBOUND",
            "DAMP_FAST_REBOUND", "ARB_", "RIDE_HEIGHT", "BRAKE_POWER", "BRAKE_BIAS")
tyre     → ("PRESSURE_", "CAMBER_", "TOE_OUT_", "TOE_IN_")
aero     → ("WING_", "SPLITTER_")
technique → ()
principal → ()
```

### _build_user_prompt (modified function signature)

```
Before: _build_user_prompt(summary, domain_signals, knowledge_fragments=None)
After:  _build_user_prompt(summary, domain_signals, knowledge_fragments=None, domain=None)
```

When `domain` is `None`: no filtering (all parameters included — backward compatible).
When `domain` is a string: filter `summary.active_setup_parameters` to include only sections matching `DOMAIN_PARAMS[domain]` prefixes, plus any unrecognized sections if domain is `"balance"`.

## State Transitions

N/A — no stateful entities. `DOMAIN_PARAMS` is an immutable constant. Filtering produces a local dict subset without mutating `SessionSummary`.

## Validation Rules

- `domain` parameter must be `None` or a key in `DOMAIN_PARAMS`
- Filtering never mutates the input `SessionSummary.active_setup_parameters`
- Domains with empty prefix tuples produce no "Current Setup Parameters" section in the prompt
