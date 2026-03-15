# Research: Fix Setup Value Domain Conversion

**Feature Branch**: `034-fix-setup-value-domains` | **Date**: 2026-03-11

## R1: SHOW_CLICKS Field Behavior in Assetto Corsa

**Decision**: SHOW_CLICKS=2 means INDEX, SHOW_CLICKS=0 means DIRECT or SCALED (based on section name prefix "CAMBER"), all others default to DIRECT.

**Rationale**: Assetto Corsa's setup.ini uses SHOW_CLICKS to control how the in-game UI displays parameter adjustments. SHOW_CLICKS=2 means the UI shows raw click counts (indices), which maps 1:1 to the stored VALUE being a 0-based index into a range defined by MIN + INDEX × STEP. SHOW_CLICKS=0 means the UI shows the actual value. SHOW_CLICKS=1 exists but only affects display formatting (shows click count alongside value) — it does not change storage semantics.

**Alternatives considered**:
- Detecting INDEX vs DIRECT by comparing VALUE against [MIN, MAX] range: Rejected because it requires user session data at classification time, which is unavailable during resolver-only resolution. Also fragile — a coincidental in-range value would be misclassified.
- Reading SHOW_CLICKS at apply time instead of resolver time: Rejected because the resolver already reads the car's setup.ini and caches the result. Adding SHOW_CLICKS there is natural and avoids re-reading the file.

## R2: CAMBER Scale Factor Detection

**Decision**: Detect SCALED parameters by section name prefix "CAMBER" (case-insensitive match on the section name). Hardcode scale factor 0.1 for camber.

**Rationale**: In all known Assetto Corsa cars (vanilla and mods), camber is the only parameter type where SHOW_CLICKS=0 but the stored value is in a different unit than the range. Camber values are stored in tenths of a degree (e.g., -18 = -1.8°) while MIN/MAX are in degrees. The scale factor is consistently 0.1 across all tested cars. No other parameter type exhibits this behavior.

**Alternatives considered**:
- Auto-detecting scale factor by comparing value magnitude to range: Rejected because it requires user values and is heuristic-based.
- Making scale factor configurable per-parameter: Over-engineering for a single known case. The lookup table pattern allows easy addition if new cases are discovered.
- Using SHOW_CLICKS=3 or other values for scaled: Not how AC works. Scaled parameters use SHOW_CLICKS=0.

## R3: Conversion Insertion Points

**Decision**: Two boundaries — inbound conversion in summarizer (storage→physical for current values), outbound conversion in setup_writer (physical→storage for proposed values).

**Rationale**: The summarizer's `summarize_session()` is where raw .ini VALUES first enter the pipeline. The private `_parse_setup_ini()` function (line 353) parses the .ini and returns a dict — conversion is applied after it returns, in `summarize_session()` (line ~79-80), before the dict is stored in `SessionSummary.active_setup_parameters`. This keeps the parser pure and the conversion explicit. The setup_writer's `apply_changes()` is where proposed values are written to .ini files — the natural place to convert physical→storage. The agent tools (`get_setup_range`) already return physical-unit ranges from the resolver, so no conversion needed there.

**Alternatives considered**:
- Converting in the agent tools instead of summarizer: Would leave `active_setup_parameters` in raw storage format, which leaks storage details into the SessionSummary model.
- Converting in the API pipeline: Violates Principle IX (separation of concerns) — conversion is business logic, not HTTP transport.

## R4: Cache Staleness Detection

**Decision**: Detect stale cache entries by checking if any ParameterRange in the cached result has `show_clicks is None`. If so, return None from `get_cached_parameters()` to trigger lazy re-resolution.

**Rationale**: Before this fix, ParameterRange has no `show_clicks` field. After adding it with `default=None`, old cached entries deserialized from JSON will have `show_clicks=None` for all parameters. Checking for None is a reliable staleness indicator. Lazy invalidation (check at load time) avoids requiring a migration script or startup routine.

**Alternatives considered**:
- Adding a cache version number: Over-engineering — the None check is simpler and doesn't require schema changes to the parameter_cache table.
- Eagerly invalidating all caches at startup: Slower startup, requires knowing when the app was updated, and doesn't handle the case where the cache is loaded mid-session.
- Adding a migration in storage/db.py: The cache table stores JSON blobs, not individual columns, so SQL migrations don't help.
- Checking tier != 3 before staleness detection: Unnecessary — the DB schema has `CHECK(tier IN (1, 2))`, so Tier 3 results are never cached. Any cached entry with `show_clicks is None` is genuinely stale.

## R5: Round-Trip Integrity for INDEX Parameters

**Decision**: When converting physical→storage for INDEX parameters, snap to the nearest valid index using `round((physical - min) / step)`, then clamp to [0, max_index]. The physical value after round-trip is `min + snapped_index * step`.

**Rationale**: The LLM may propose values not exactly on step boundaries (e.g., 31000 when valid values are 25500, 30000, 34500). Rounding to nearest index preserves intent while maintaining valid storage values. Clamping ensures we never write negative indices or exceed the valid range.

**Alternatives considered**:
- Truncating (floor) instead of rounding: Biased toward lower values. Rounding better preserves the LLM's intent.
- Rejecting off-step values: Too strict. The LLM reasons about physical quantities, not discrete steps.
- Validating at the physical level before conversion: Already happens — `validate_changes()` operates on physical ranges and clamps there first. The to_storage conversion only handles the domain translation.

## R6: value_before Population for Display

**Decision**: `value_before` in SetupChange is populated from `active_setup_parameters` (which will be in physical units after the summarizer fix). `value_after` is the LLM's proposed physical value. Both are in physical units by the time they reach the API/UI.

**Rationale**: The LLM tools already set `value_before` from `active_setup_parameters` when proposing changes. Once the summarizer converts these to physical units, `value_before` is automatically correct. No separate conversion needed for display.

**Alternatives considered**:
- Adding a separate display conversion layer in the API: Unnecessary if source data is already physical.
- Storing both storage and physical values: Over-engineering. The frontend only needs physical values.
