# Feature Specification: Domain-Scoped Setup Context

**Feature Branch**: `030-domain-scoped-setup-context`
**Created**: 2026-03-11
**Status**: Draft
**Input**: User description: "Phase 10 — Domain-Scoped Setup Context: Filter setup parameters injected into specialist agent prompts by domain relevance to reduce wasted input tokens."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reduced Token Cost Per Analysis (Priority: P1)

As a user running a session analysis, the system should send each specialist agent only the setup parameters it can act on, so that I consume fewer input tokens per analysis without any loss in recommendation quality.

**Why this priority**: This is the core value proposition — every analysis currently wastes tokens by sending irrelevant parameters to every agent. Fixing this directly reduces cost and latency for every single analysis run.

**Independent Test**: Can be tested by running an analysis and verifying that each specialist agent's prompt contains only domain-relevant parameters while producing equivalent recommendations.

**Acceptance Scenarios**:

1. **Given** a session with ~30 active setup parameters, **When** the Balance agent is invoked, **Then** its prompt contains only springs, dampers, ARBs, ride height, and brake bias parameters (not tyre pressures, camber, toe, or wing parameters).
2. **Given** a session with ~30 active setup parameters, **When** the Tyre agent is invoked, **Then** its prompt contains only pressures, camber, and toe parameters (not springs, dampers, ARBs, or wing parameters).
3. **Given** a session with ~30 active setup parameters, **When** the Aero agent is invoked, **Then** its prompt contains only wing and splitter parameters.
4. **Given** a session with ~30 active setup parameters, **When** the Technique agent is invoked, **Then** its prompt contains no setup parameters at all (it coaches driving, not setup).
5. **Given** a session with ~30 active setup parameters, **When** the Principal agent is invoked, **Then** its prompt contains no setup parameters (it synthesizes specialist results, not raw setup data).

---

### User Story 2 - Fallback Access via Tools (Priority: P2)

As a specialist agent that encounters a rare cross-domain question, the system should still allow querying any parameter via the existing `get_setup_range` tool, so that filtering does not block edge-case reasoning.

**Why this priority**: While rare, cross-domain queries are possible (e.g., a Balance agent wanting to know tyre pressures to understand weight transfer). The tool fallback ensures no degradation in recommendation quality.

**Independent Test**: Can be tested by verifying that a specialist agent can still call `get_setup_range` for a parameter outside its domain scope and receive correct data.

**Acceptance Scenarios**:

1. **Given** the Tyre agent receives only tyre-related parameters in its prompt, **When** it calls `get_setup_range` for a spring parameter, **Then** it receives the correct spring parameter value and range.
2. **Given** the Balance agent receives only balance-related parameters in its prompt, **When** it calls `get_setup_range` for a tyre pressure parameter, **Then** it receives the correct pressure value and range.

---

### User Story 3 - Mod Cars with Non-Standard Parameters (Priority: P2)

As a user with mod cars that have unusual or extra setup parameters, the system should correctly classify parameters it recognizes into the right domain and gracefully handle unrecognized parameters, so that mod car analyses work correctly.

**Why this priority**: The project explicitly supports vanilla and mod cars. Mod cars may have custom parameter names that don't match standard patterns, so the filtering logic must handle unknowns gracefully.

**Independent Test**: Can be tested by providing a setup with non-standard parameter names and verifying that recognized parameters are correctly filtered and unrecognized parameters are assigned to a sensible default domain.

**Acceptance Scenarios**:

1. **Given** a mod car with standard parameter names (e.g., PRESSURE_LF, SPRING_RATE_LF), **When** parameters are classified, **Then** each parameter is assigned to the correct domain.
2. **Given** a mod car with a custom parameter name not matching any known pattern, **When** parameters are classified, **Then** the unrecognized parameter is included in the Balance agent's scope (as the broadest mechanical domain) so it is not silently dropped.
3. **Given** a mod car with no aero-related sections, **When** the Aero agent is invoked, **Then** it receives an empty parameter set and is informed that no aero parameters are available.

---

### Edge Cases

- What happens when a car has zero active setup parameters? The agents should receive no parameter block and should be informed that no setup data is available (existing behavior preserved).
- What happens when all parameters belong to a single domain (e.g., a kart with only tyre parameters)? Only the relevant agent receives parameters; other agents receive empty sets.
- What happens when a mod car has a section name that does not match any known prefix? The parameter is assigned to the Balance domain as a fallback (per FR-009), ensuring it is not silently dropped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define a mapping from setup parameter section names to agent domains (balance, tyre, aero).
- **FR-002**: System MUST filter `active_setup_parameters` by domain before injecting them into each specialist agent's prompt.
- **FR-003**: Balance agent MUST receive only parameters from sections related to springs, dampers, anti-roll bars, ride height, and brake bias.
- **FR-004**: Tyre agent MUST receive only parameters from sections related to tyre pressures, camber, and toe alignment.
- **FR-005**: Aero agent MUST receive only parameters from sections related to wings and splitters.
- **FR-006**: Technique agent MUST receive no setup parameters in its prompt.
- **FR-007**: Principal agent MUST receive no setup parameters in its prompt.
- **FR-008**: All specialist agents MUST retain access to the `get_setup_range` tool for querying any parameter outside their domain scope.
- **FR-009**: Parameters with section names that do not match any known domain pattern MUST be assigned to the Balance domain as a fallback.
- **FR-010**: The filtering MUST happen at prompt construction time only — the `SessionSummary` model and `summarize_session()` function MUST remain unchanged.
- **FR-011**: No changes to API endpoints, API response formats, or frontend components are required.
- **FR-012**: The domain-to-parameter mapping MUST classify parameters by matching setup section names against known prefix patterns. No secondary heuristics are needed — section names in AC setup files are sufficiently descriptive for unambiguous classification.

### Key Entities

- **Domain Parameter Map**: A mapping that associates each agent domain (balance, tyre, aero) with the set of setup section name patterns that belong to it. Technique and Principal domains map to empty sets.
- **Filtered Parameter Set**: The subset of `active_setup_parameters` that is relevant to a specific specialist agent, derived by applying the domain parameter map at prompt construction time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Input tokens consumed by setup parameter context per analysis are reduced by 60–70% compared to current behavior (measured by total parameter lines across all agent prompts).
- **SC-002**: Zero additional tool calls are made in the common case — agents do not need to query parameters that were filtered out for typical analyses.
- **SC-003**: All existing tests pass without modification (zero regressions).
- **SC-004**: New tests verify that each domain receives only its expected parameters for a representative set of setup configurations.
- **SC-005**: Recommendation quality is unchanged — the same signals and setup parameters produce the same specialist agent outputs (verified by existing agent tests continuing to pass).

## Assumptions

- The existing `AERO_SECTIONS` constant already defines section names relevant to aero. A similar approach can be extended for balance and tyre domains.
- Section names in AC setup files follow recognizable patterns (e.g., `SPRING_*`, `DAMPER_*`, `PRESSURE_*`, `WING_*`) that allow reliable classification.
- The `get_setup_range` tool already supports querying any parameter regardless of what was injected in the prompt, so no tool changes are needed for fallback access.
- Unrecognized parameters are rare enough that assigning them to the Balance domain (the broadest mechanical domain) is a reasonable default.
