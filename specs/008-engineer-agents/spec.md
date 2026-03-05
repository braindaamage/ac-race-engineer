# Feature Specification: Engineer Agents

**Feature Branch**: `008-engineer-agents`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Phase 5.3 — Engineer Agents: AI-powered setup analysis for AC Race Engineer"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze a Session and Get Setup Recommendations (Priority: P1)

A driver has just finished a practice session in Assetto Corsa. They select the session and ask the system to analyze it. The system examines the session summary — which already contains detected signals like "high_understeer" or "tyre_temp_spread_high" — and produces targeted setup change recommendations with plain-language explanations. Only the relevant problem domains are analyzed; if the session shows no tyre issues, no tyre specialist runs.

**Why this priority**: This is the core value proposition — turning raw telemetry analysis into actionable, understandable setup advice. Without this, the system is just a data viewer.

**Independent Test**: Can be tested by providing a SessionSummary with known signals and verifying the system returns an EngineerResponse with appropriate setup changes, reasoning, and confidence levels.

**Acceptance Scenarios**:

1. **Given** a SessionSummary with signals `["high_understeer", "tyre_temp_spread_high"]`, **When** the system analyzes the session, **Then** it produces an EngineerResponse containing setup changes targeting understeer and tyre temperatures, each with reasoning and expected effect in plain language.
2. **Given** a SessionSummary with only the signal `["low_consistency"]`, **When** the system analyzes the session, **Then** it produces an EngineerResponse with driver feedback (technique observations) but no setup changes, since consistency is a driving issue.
3. **Given** a SessionSummary with no detected signals, **When** the system analyzes the session, **Then** it produces an EngineerResponse with a summary acknowledging no issues detected, an empty setup changes list, and optional general driving tips.

---

### User Story 2 - Receive Domain-Specific Analysis from Specialist Agents (Priority: P1)

Different car problems require different expertise. A balance problem (understeer/oversteer) needs reasoning about springs, dampers, and anti-roll bars. A tyre problem needs reasoning about pressures, camber, and toe. An aero problem needs reasoning about wing angles and ride heights. A consistency problem needs driving technique advice, not setup changes. The system routes each detected signal to the appropriate specialist and combines their outputs.

**Why this priority**: Specialist routing is what makes the advice precise rather than generic. Without it, the system would give the same boilerplate for every session.

**Independent Test**: Can be tested by providing SessionSummaries with signals from different domains and verifying that only the relevant specialists produce output.

**Acceptance Scenarios**:

1. **Given** a SessionSummary with signals `["high_understeer", "brake_balance_issue"]`, **When** the system routes to specialists, **Then** only the balance specialist runs and produces recommendations about suspension and brake settings.
2. **Given** a SessionSummary with signals `["tyre_temp_spread_high", "tyre_wear_rapid"]`, **When** the system routes to specialists, **Then** only the tyre specialist runs and produces recommendations about pressures, camber, or toe.
3. **Given** a SessionSummary with signals `["high_understeer", "tyre_temp_spread_high", "low_consistency"]`, **When** the system routes to specialists, **Then** the balance specialist, tyre specialist, and driving technique specialist all run, and their outputs are combined into a single response.
4. **Given** a car with aerodynamic parameters in its setup and signals indicating aero-related issues, **When** the system routes to specialists, **Then** the aero specialist runs and produces recommendations about wing angles or ride heights.

---

### User Story 3 - Understand Why Each Change Was Proposed (Priority: P1)

The driver is not an engineer. When they see a recommendation like "Increase front anti-roll bar from 3 to 5", they need to understand why ("Your car is understeering in mid-corner, especially in turns 3 and 7") and what they'll feel on track ("The front end will rotate more willingly into corners, reducing the push feeling"). Every recommendation must include both a reasoning and an expected effect.

**Why this priority**: Without explanations, the recommendations are no better than a lookup table. The educational aspect is what differentiates this from a simple rules engine.

**Independent Test**: Can be tested by verifying that every SetupChange in the response has non-empty `reasoning` and `expected_effect` fields written in driver-friendly language.

**Acceptance Scenarios**:

1. **Given** a setup change recommendation, **When** the driver reads it, **Then** the `reasoning` field explains the problem in terms of on-track behavior (not engineering jargon) and references specific corners or laps where the issue was observed.
2. **Given** a setup change recommendation, **When** the driver reads it, **Then** the `expected_effect` field describes what will feel different on track after applying the change.
3. **Given** a complete EngineerResponse, **When** the driver reads the summary, **Then** they get a concise overview (suitable for a UI card) of the overall session assessment and key recommendations.

---

### User Story 4 - Knowledge-Grounded Reasoning (Priority: P2)

The specialist agents consult the project's vehicle dynamics knowledge base when reasoning about setup changes. When the balance specialist needs to understand what changing the front anti-roll bar does, it queries the knowledge base rather than relying solely on general AI training. This ensures recommendations are consistent with the documented vehicle dynamics principles.

**Why this priority**: Grounding in the knowledge base prevents hallucinated physics and ensures consistency across sessions. Important but the system can deliver value with general AI knowledge alone.

**Independent Test**: Can be tested by verifying that agent tool calls include knowledge base queries and that the knowledge fragments retrieved are relevant to the signals being analyzed.

**Acceptance Scenarios**:

1. **Given** a specialist agent analyzing understeer, **When** it needs to reason about which parameters affect understeer, **Then** it queries the knowledge base for relevant setup information and incorporates the retrieved knowledge into its reasoning.
2. **Given** a specialist agent encountering a signal it needs more context about, **When** it searches the knowledge base, **Then** it receives relevant KnowledgeFragments that inform its recommendations.

---

### User Story 5 - Parameter-Safe Recommendations (Priority: P2)

Before any setup change is included in the response, it must be validated against the car's known parameter ranges. If a proposed value exceeds the car's physical limits, it is clamped to the nearest valid value. If no range data exists for a parameter, the change carries a warning but is not rejected.

**Why this priority**: Safety is critical — the system must never propose impossible values. However, validation is a mechanical check on top of already-generated recommendations.

**Independent Test**: Can be tested by providing parameter ranges and proposed changes that exceed them, then verifying all values are clamped and warnings are generated.

**Acceptance Scenarios**:

1. **Given** a proposed setup change with a value above the parameter's maximum, **When** validation runs, **Then** the value is clamped to the maximum and included in the response with the clamped value.
2. **Given** a proposed setup change for a parameter with no known range, **When** validation runs, **Then** the change is included with a warning indicating range data is unavailable.
3. **Given** all proposed changes within valid ranges, **When** validation runs, **Then** all changes pass validation without modifications or warnings.

---

### User Story 6 - Persist Analysis Results (Priority: P3)

After the engineer produces a response, the full analysis (recommendations, setup changes, driver feedback) is saved to the database so the driver can review it later or compare recommendations across sessions.

**Why this priority**: Persistence enables future features (history, comparison, learning) but the core analysis loop works without it.

**Independent Test**: Can be tested by running an analysis and then querying the database to verify the recommendation and its associated setup changes were saved.

**Acceptance Scenarios**:

1. **Given** a completed EngineerResponse, **When** the system persists it, **Then** the recommendation summary and all setup changes are retrievable from the database by session ID.
2. **Given** an analysis that produced only driver feedback (no setup changes), **When** the system persists it, **Then** the recommendation is saved with an empty changes list and the feedback is included in the summary.

---

### User Story 7 - Apply Accepted Recommendations to Setup File (Priority: P3)

After reviewing the engineer's recommendations, the driver accepts them and wants to apply the changes to their setup file. The system orchestrates the full write pipeline: validate the accepted changes against parameter ranges, create a backup of the original setup, and write the changes atomically to the .ini file.

**Why this priority**: Applying changes is the final step in the feedback loop, but the driver can also apply changes manually. The analysis and recommendations are valuable on their own.

**Independent Test**: Can be tested by providing a recommendation with setup changes and a setup file, then verifying the backup was created, values were written, and the database status updated.

**Acceptance Scenarios**:

1. **Given** an accepted EngineerResponse with 3 setup changes, **When** the system applies it, **Then** all 3 changes are written to the setup file, a backup exists, and the recommendation status is "applied" in the database.
2. **Given** an apply operation that fails mid-write, **When** the error occurs, **Then** the original setup file is intact and the recommendation status remains unchanged.

---

### Edge Cases

- What happens when the AI model is unavailable or returns an error? The system returns a graceful error response indicating the analysis could not be completed, without crashing.
- What happens when the SessionSummary has no flying laps (all laps are in/out laps)? The system returns an EngineerResponse noting insufficient data for analysis.
- What happens when the car has no setup.ini file (no parameter ranges available)? The system still produces recommendations but all changes carry "no range data" warnings.
- What happens when the AI proposes a parameter that doesn't exist in the car's setup? The change is excluded from the final response with a logged warning.
- What happens when multiple specialists recommend conflicting changes to the same parameter? The orchestrator detects the conflict and keeps the change from the higher-priority specialist, noting the conflict in the explanation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a SessionSummary and produce an EngineerResponse as the primary interface for session analysis.
- **FR-002**: System MUST route detected signals to appropriate specialist domains: balance signals to balance specialist, tyre signals to tyre specialist, aero signals to aero specialist, consistency/technique signals to driving coach.
- **FR-003**: System MUST only invoke specialist agents whose domain signals are present in the SessionSummary — specialists with no relevant signals MUST NOT run.
- **FR-004**: Each specialist agent MUST produce setup change recommendations (or driving feedback for the technique specialist) specific to its domain.
- **FR-005**: Every SetupChange MUST include a `reasoning` field explaining the problem in driver-friendly language and an `expected_effect` field describing the on-track sensation after the change.
- **FR-006**: The EngineerResponse MUST include a `summary` field with a concise overview suitable for display in a UI card.
- **FR-007**: Specialist agents MUST have access to the vehicle dynamics knowledge base via tool calls to search for relevant knowledge.
- **FR-008**: All proposed setup changes MUST be validated against the car's parameter ranges before inclusion in the response.
- **FR-009**: Out-of-range proposed values MUST be clamped to the nearest valid boundary value.
- **FR-010**: Changes to parameters with no known range data MUST be included with a warning, not rejected.
- **FR-011**: The completed EngineerResponse MUST be persisted to the database using existing storage functions.
- **FR-012**: The system MUST handle AI model errors gracefully, returning an error indication without crashing.
- **FR-013**: The system MUST handle sessions with no flying laps by returning a response indicating insufficient data.
- **FR-014**: When multiple specialists propose changes to the same parameter, the system MUST resolve the conflict deterministically (higher-priority specialist wins).
- **FR-015**: The system MUST populate `signals_addressed` in the response with the list of signals that were analyzed.
- **FR-016**: The system MUST be fully testable without a real Assetto Corsa installation, live telemetry, or live AI model calls.
- **FR-017**: System MUST expose apply_recommendation() to orchestrate validation + backup + atomic write + status update in a single call.

### Key Entities

- **EngineerResponse**: The complete output of a session analysis — contains setup changes, driver feedback, summary, confidence, and addressed signals. One response per analysis request.
- **Specialist Domain**: A category of car behavior analysis (balance, tyres, aero, driving technique). Each domain has its own reasoning logic and knowledge base queries. Maps to specific detected signals.
- **Signal-to-Domain Mapping**: The routing table that determines which signals trigger which specialist. A signal belongs to exactly one domain. A domain may have multiple signals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given a SessionSummary with detected signals, the system produces a complete EngineerResponse within 60 seconds.
- **SC-002**: Every setup change recommendation includes both a reasoning and an expected effect in plain, non-technical language.
- **SC-003**: Only specialists whose domain signals are present in the session run — zero unnecessary specialist invocations.
- **SC-004**: 100% of proposed setup change values are within the car's valid parameter ranges (clamped if necessary).
- **SC-005**: The full EngineerResponse is retrievable from the database after analysis completes.
- **SC-006**: The system handles AI model failures gracefully in 100% of error scenarios — no unhandled exceptions propagate to the caller.
- **SC-007**: All agent logic is testable with mocked AI responses — no real model calls required in the test suite.
