# Research: Domain-Scoped Setup Context

**Feature**: 030-domain-scoped-setup-context
**Date**: 2026-03-11

## R1: AC Setup Section Name Patterns

**Decision**: Classify setup parameters by matching section names against known prefix strings.

**Rationale**: AC setup `.ini` files use section names like `SPRING_RATE_LF`, `PRESSURE_RF`, `WING_1`, `DAMP_BUMP_RL`, etc. The section name prefix unambiguously identifies the parameter type. The existing `AERO_SECTIONS` constant already uses this approach for wing/ride-height detection.

**Alternatives considered**:
- Parameter name matching (rejected: all parameters are named `VALUE`, so section name is the only discriminator)
- TAB field from `data/setup.ini` (rejected: requires reading the car's data files at prompt time; section prefixes are already available in `active_setup_parameters`)

## R2: Domain-to-Prefix Mapping

**Decision**: Map three setup domains to section name prefixes. Use `str.startswith()` for matching.

| Domain | Section Prefixes |
|--------|-----------------|
| balance | `SPRING_RATE`, `DAMP_BUMP`, `DAMP_FAST_BUMP`, `DAMP_REBOUND`, `DAMP_FAST_REBOUND`, `ARB_`, `RIDE_HEIGHT`, `BRAKE_POWER`, `BRAKE_BIAS` |
| tyre | `PRESSURE_`, `CAMBER_`, `TOE_OUT_`, `TOE_IN_` |
| aero | `WING_`, `SPLITTER_` |
| technique | *(empty — no setup params)* |
| principal | *(empty — no setup params)* |

**Rationale**: These prefixes cover all standard AC vanilla car sections. The existing `AERO_SECTIONS` set includes `RIDE_HEIGHT_*` in the aero domain for routing purposes, but for parameter *filtering*, ride height is a balance concern (it affects mechanical grip and contact patch). The aero routing detection (`AERO_SECTIONS`) and parameter filtering (`DOMAIN_PARAMS`) serve different purposes and can have different section assignments.

**Alternatives considered**:
- Include `RIDE_HEIGHT` in aero domain params (rejected: ride height adjustments affect mechanical balance more than aerodynamics; the aero agent's role is wing/splitter tuning)
- Use exact set matching like `AERO_SECTIONS` (rejected: prefix matching is more resilient to mod variations like `SPRING_RATE_FRONT_LEFT`)

## R3: Fallback for Unrecognized Sections

**Decision**: Sections not matching any domain prefix are included in the balance domain's filtered set.

**Rationale**: Balance is the broadest mechanical domain and the highest-priority domain (DOMAIN_PRIORITY=1). Including unknowns there ensures no parameter is silently dropped. This is consistent with FR-009 in the spec.

**Alternatives considered**:
- Include unknowns in all domains (rejected: defeats the purpose of filtering)
- Drop unknowns entirely (rejected: could hide mod-specific parameters)
- Create an "other" domain (rejected: adds complexity; balance agent is the best default recipient)

## R4: Filtering Implementation Location

**Decision**: Add a `domain` parameter to `_build_user_prompt()` and filter inside it. The caller (`analyze_with_engineer`) passes the current domain.

**Rationale**: `_build_user_prompt()` already handles the setup parameters serialization (lines 354-373). Adding filtering there is minimal and keeps the logic co-located. The `analyze_with_engineer()` loop already knows the domain variable.

**Alternatives considered**:
- Standalone `filter_params_for_domain()` function (rejected: over-engineering for a single call site; can be extracted later if needed)
- Filter in `analyze_with_engineer()` before calling `_build_user_prompt()` (rejected: would require mutating the summary or creating a copy; filtering inside the prompt builder keeps the summary immutable)

## R5: Existing Test Impact

**Decision**: Existing `_build_user_prompt` tests do not pass a `domain` parameter. The function will default `domain=None`, meaning "include all parameters" (backward compatible).

**Rationale**: Three existing tests in `TestBuildUserPromptKnowledge` call `_build_user_prompt(summary, signals, fragments)` without a domain. A default of `None` means no filtering — preserving current behavior for all existing call sites except the main orchestrator loop.

**Alternatives considered**:
- Make `domain` required (rejected: breaks existing tests and the chat agent call site in `api/engineer/pipeline.py`)
- Default to `"balance"` (rejected: would change behavior for existing callers)
