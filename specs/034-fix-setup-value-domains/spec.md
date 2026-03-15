# Feature Specification: Fix Setup Value Domain Conversion

**Feature Branch**: `034-fix-setup-value-domains`
**Created**: 2026-03-11
**Status**: Draft
**Input**: User description: "Fix the setup parameter value generation pipeline. The system currently mixes two incompatible value domains — storage indices and physical units — causing the LLM to propose nonsensical setup values that get clamped to range extremes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct Setup Recommendations for Index Parameters (Priority: P1)

When the AI engineer analyzes a session and recommends setup changes for parameters stored as indices (e.g., anti-roll bars, dampers, ride height), the recommended values must be meaningful physical quantities that, when applied, produce the correct storage values in the setup file.

**Why this priority**: This is the most common failure mode. INDEX parameters (SHOW_CLICKS=2) are the majority of setup parameters in most cars. Without this fix, every INDEX-based recommendation corrupts the setup file by writing physical-unit values where AC expects integer indices.

**Independent Test**: Can be tested by running the engineer pipeline on a session with a car that has INDEX parameters (e.g., ks_mazda_mx5_cup), verifying the LLM sees physical-unit current values, and confirming the written .ini file contains valid index values.

**Acceptance Scenarios**:

1. **Given** a car with ARB_FRONT configured as SHOW_CLICKS=2, MIN=25500, MAX=43500, STEP=4500, and a user setup with VALUE=2 (index), **When** the system presents data to the LLM, **Then** the LLM sees "current: 34500" and range "25500–43500" (all in physical units).
2. **Given** the LLM proposes ARB_FRONT = 30000 (physical), **When** the system writes the change to the .ini file, **Then** VALUE=1 is written (index = (30000−25500)/4500 = 1, rounded to nearest valid index).
3. **Given** the LLM proposes a physical value not exactly on a step boundary, **When** the system converts to storage, **Then** the value is snapped to the nearest valid index (e.g., 31000 → index 1 → physical 30000).

---

### User Story 2 - Correct Setup Recommendations for Scaled Parameters (Priority: P1)

When the AI engineer recommends changes for parameters stored in a scaled format (e.g., camber in tenths of a degree), the recommended values must be in the human-readable physical unit (degrees), and the system must convert back to the scaled storage format when writing.

**Why this priority**: Scaled parameters like camber are critical to car handling. Writing unscaled physical values (e.g., -2.2 degrees) where AC expects scaled storage values (e.g., -22 tenths) causes extreme and dangerous setup corruption.

**Independent Test**: Can be tested by running the engineer pipeline on a car with camber parameters, verifying the LLM sees degree values, and confirming the .ini file receives correctly scaled values.

**Acceptance Scenarios**:

1. **Given** CAMBER_LR with SHOW_CLICKS=0, VALUE=-18 (tenths of degree), MIN=-2.2, MAX=1.5 (degrees), **When** the system presents data to the LLM, **Then** the LLM sees "current: -1.8°" and range "-2.2–1.5".
2. **Given** the LLM proposes CAMBER_LR = -1.0 (degrees), **When** the system writes the change, **Then** VALUE=-10 is written (= -1.0 / 0.1).

---

### User Story 3 - Direct Parameters Continue Working (Priority: P2)

Parameters that are already stored in physical units (SHOW_CLICKS=0, value within range) must continue to work exactly as they do today — no conversion applied.

**Why this priority**: These parameters currently work correctly by coincidence. The fix must not regress them.

**Independent Test**: Can be tested by running the pipeline on a car with direct parameters (e.g., tyre pressure, spring rate) and verifying no conversion is applied — the value flows through unchanged.

**Acceptance Scenarios**:

1. **Given** PRESSURE_LF with SHOW_CLICKS=0, VALUE=18, MIN=15, MAX=40, **When** the system presents data to the LLM, **Then** the LLM sees "current: 18" and range "15–40".
2. **Given** the LLM proposes PRESSURE_LF = 16, **When** the system writes the change, **Then** VALUE=16 is written. No conversion occurs.

---

### User Story 4 - Physical-Unit Display in UI (Priority: P2)

The value_before and value_after fields shown to the user in recommendation cards must display physical-unit values, so the user sees meaningful numbers (e.g., "34500 → 30000 N·m/rad") rather than raw indices (e.g., "2 → 1").

**Why this priority**: Even if the backend conversion is correct, showing raw storage values to the user makes recommendations incomprehensible.

**Independent Test**: Can be tested by checking the EngineerResponse payload — value_before and value_after must be in physical units for all parameter types.

**Acceptance Scenarios**:

1. **Given** an INDEX parameter with value_before as index 2 (physical: 34500) changed to index 1 (physical: 30000), **When** the recommendation is displayed, **Then** the user sees value_before=34500 and value_after=30000.
2. **Given** a SCALED parameter with value_before as -18 (physical: -1.8°) changed to -10 (physical: -1.0°), **When** the recommendation is displayed, **Then** the user sees value_before=-1.8 and value_after=-1.0.

---

### User Story 5 - Stale Parameter Cache Invalidation (Priority: P3)

Existing cached parameter data that was resolved before this fix (and therefore lacks storage convention metadata) must be automatically invalidated so that fresh resolution includes the new metadata.

**Why this priority**: Without invalidation, cached parameters would continue producing incorrect conversions until the cache naturally expires or is manually cleared.

**Independent Test**: Can be tested by pre-populating a parameter cache without storage convention data, running the pipeline, and verifying the cache is re-resolved with the new metadata.

**Acceptance Scenarios**:

1. **Given** a parameter cache entry that lacks storage convention metadata, **When** the system loads parameters for that car, **Then** the stale cache is invalidated and parameters are re-resolved from the car's data files.
2. **Given** a freshly resolved parameter cache with storage convention metadata, **When** the system loads parameters for that car again, **Then** the cache is used without re-resolution.

---

### Edge Cases

- What happens when STEP is 0 or missing for an INDEX parameter? The system must treat it as a DIRECT parameter (no index conversion possible without a valid step).
- What happens when a SCALED parameter has a scale factor that cannot be auto-detected? The system must fall back to DIRECT treatment and log a warning.
- What happens when the LLM proposes a physical value that, after conversion, would produce a non-integer index? The system must snap to the nearest valid index.
- What happens when a parameter's SHOW_CLICKS value is something other than 0 or 2 (e.g., 1)? The system must handle unknown SHOW_CLICKS values gracefully, defaulting to DIRECT treatment.
- What happens with Tier 3 (session fallback) resolution where SHOW_CLICKS is unavailable? Values pass through without conversion since no authoritative range data exists.
- What happens with round-trip precision? Converting physical → storage → physical must produce the original physical value within floating-point tolerance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST classify each setup parameter into one of three storage conventions based solely on the car's data/setup.ini metadata (no user values required): SHOW_CLICKS=2 → INDEX; SHOW_CLICKS=0 and section name starts with "CAMBER" → SCALED (factor 0.1); SHOW_CLICKS=0 otherwise → DIRECT; any other or missing SHOW_CLICKS → DIRECT.
- **FR-002**: The system MUST convert INDEX parameter values from storage indices to physical units (physical = MIN + INDEX × STEP) before presenting them to the LLM or the user.
- **FR-003**: The system MUST convert SCALED parameter values from storage format to physical units (physical = storage_value × scale_factor) before presenting them to the LLM or the user.
- **FR-004**: The system MUST convert LLM-proposed physical values back to storage format before writing to the setup .ini file — index = round((physical − MIN) / STEP) for INDEX parameters, storage = physical / scale_factor for SCALED parameters.
- **FR-005**: The system MUST snap converted INDEX values to the nearest valid index (0 to N where N = (MAX − MIN) / STEP), clamping at boundaries.
- **FR-006**: The system MUST preserve DIRECT parameter behavior — no conversion applied when SHOW_CLICKS=0 and the stored value falls within the parameter's [MIN, MAX] range.
- **FR-007**: The resolver MUST read and persist the SHOW_CLICKS field from the car's data/setup.ini for each parameter during Tier 1 and Tier 2 resolution.
- **FR-008**: The system MUST populate value_before and value_after in recommendation responses using physical-unit values, not raw storage values.
- **FR-009**: The system MUST detect stale parameter cache entries (those lacking storage convention metadata) at load time and re-resolve them transparently. This is a lazy invalidation — stale entries are re-resolved when first accessed, not eagerly at application startup.
- **FR-010**: The conversion logic MUST be deterministic pure functions with no LLM involvement — computed from SHOW_CLICKS, MIN, MAX, STEP, and known scale factors.
- **FR-011**: The system MUST maintain round-trip integrity: converting a physical value to storage and back MUST produce the original value within floating-point tolerance (±1e-9).
- **FR-012**: For unknown or missing SHOW_CLICKS values, the system MUST default to DIRECT treatment (no conversion).
- **FR-013**: For Tier 3 (session fallback) parameters where SHOW_CLICKS is unavailable, the system MUST pass values through without conversion.

### Key Entities

- **StorageConvention**: Classification of a parameter's storage format — INDEX (SHOW_CLICKS=2), DIRECT (SHOW_CLICKS=0, non-CAMBER section), or SCALED (SHOW_CLICKS=0, section name starts with "CAMBER"). Determined per-parameter from the car's data/setup.ini metadata and section name alone — no user setup values are consulted.
- **ParameterRange** (extended): Existing model gains a storage convention field and the original SHOW_CLICKS value, enabling the conversion layer to operate.
- **Scale Factor**: A known multiplier for SCALED parameters (e.g., 0.1 for camber in tenths of degree). Maintained as a deterministic lookup, not inferred at runtime.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every INDEX parameter, the value presented to the LLM differs from the raw storage value by the correct physical offset (MIN + INDEX × STEP), and the value written back to the .ini is a valid integer index — verified across all three example cars in the test suite.
- **SC-002**: For every SCALED parameter (camber), the value presented to the LLM is in degrees (not tenths), and the value written back is in the scaled storage format — verified with round-trip tests.
- **SC-003**: For every DIRECT parameter, the value flows through unchanged in both directions — no regressions from the current behavior.
- **SC-004**: All 1410+ existing tests continue to pass without modification (conversion functions are additive, not breaking).
- **SC-005**: Round-trip conversion (physical → storage → physical) produces identical values within ±1e-9 for all valid inputs — verified by parametric tests.
- **SC-006**: The real-world failure cases documented in the problem statement (ks_mazda_mx5_cup ARB_FRONT, CAMBER_LR) produce correct results when replayed through the fixed pipeline — replayed using deterministic test models (TestModel/FunctionModel), not real LLM calls.

## Assumptions

- SHOW_CLICKS=2 always indicates an INDEX parameter where VALUE is a 0-based index. This is consistent with all known Assetto Corsa cars (vanilla and mods).
- The only known SCALED parameter type is camber (SHOW_CLICKS=0, stored in tenths of degree, range in degrees). The scale factor 0.1 is hardcoded for camber. Detection is based on section name prefix ("CAMBER"), not on comparing user values against ranges. This makes classification deterministic from car data alone, without requiring session context. Verified across 4 Kunos cars (MX5 Cup, BMW M4, Porsche 911 GT3 R, Ferrari 488 GT3). If other scaled parameters are discovered in the future, new scale factors can be added to the lookup table.
- SHOW_CLICKS values other than 0 and 2 (e.g., 1) are treated as DIRECT. SHOW_CLICKS=1 exists in AC but only affects UI display (shows click count), not the storage format.
- Tier 3 (session fallback) resolution does not have access to SHOW_CLICKS data, so no conversion is attempted for Tier 3 parameters. This is acceptable because Tier 3 already produces single-point ranges that bypass clamping.
- The frontend does not need changes — it already displays whatever value_before/value_after the backend provides. The fix is entirely backend-side.
