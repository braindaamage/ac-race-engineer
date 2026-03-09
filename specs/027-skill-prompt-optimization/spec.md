# Feature Specification: Skill Prompt Optimization

**Feature Branch**: `027-skill-prompt-optimization`
**Created**: 2026-03-09
**Status**: Draft
**Input**: User description: "Skill prompt optimization for AI race engineer agents. Currently the AI agents that analyze telemetry sessions produce setup recommendations that are 3-5x more verbose than necessary."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Concise Setup Recommendations (Priority: P1)

A driver completes a session and requests an AI analysis. The engineer produces setup change recommendations where each change cites one concrete telemetry data point (e.g., "avg understeer ratio 0.73 in turns 3, 7") and states one driver-felt effect (e.g., "car will rotate more on entry"). The total number of setup changes per domain is limited to 3, ensuring only the most impactful findings are surfaced.

**Why this priority**: This is the core problem — excess verbosity in setup change output accounts for the majority of wasted tokens. Fixing this alone would reduce output by ~60%.

**Independent Test**: Can be tested by running an analysis on any session and verifying each setup change has exactly one data citation and one effect statement, and no domain exceeds 3 changes.

**Acceptance Scenarios**:

1. **Given** a session with multiple balance issues detected, **When** the balance specialist produces recommendations, **Then** it outputs at most 3 setup changes, each with a one-sentence reasoning referencing specific data and a one-sentence expected effect.
2. **Given** a session where a signal appears in only 1 out of 10 laps, **When** the specialist evaluates the signal, **Then** it omits the finding as unconfirmed across multiple laps.
3. **Given** a session with issues spanning multiple domains, **When** the full analysis completes, **Then** the total output contains no repeated vehicle dynamics theory explanations.

---

### User Story 2 - Focused Driving Technique Feedback (Priority: P2)

A driver receives driving technique observations that are structured and brief. Each observation names the technique area, states the observation in one sentence backed by data, and provides a one-to-two sentence actionable suggestion. No filler explanations or physics theory accompany the feedback.

**Why this priority**: Technique feedback is the second-largest source of verbosity, with agents producing paragraph-length observations when a few sentences suffice.

**Independent Test**: Can be tested by running an analysis on a session with consistency or technique signals and verifying each feedback entry follows the constrained format.

**Acceptance Scenarios**:

1. **Given** a session with braking consistency issues in corners 3 and 7, **When** the technique specialist produces feedback, **Then** the observation is one sentence citing the data (e.g., braking point variance) and the suggestion is one to two sentences.
2. **Given** a session with no significant technique issues, **When** the technique specialist runs, **Then** it produces no feedback entries rather than marginal observations.

---

### User Story 3 - Lean Orchestrator Synthesis (Priority: P2)

The orchestrator (principal agent) synthesizes specialist findings into a final summary without re-explaining the physics or reasoning behind each recommendation. The summary references each domain's key finding in one sentence and provides an overall assessment of the car's behavior.

**Why this priority**: The orchestrator currently duplicates specialist explanations, adding redundant content. A concise synthesis reduces the final response size and improves readability.

**Independent Test**: Can be tested by analyzing the final combined summary and verifying it does not contain vehicle dynamics theory that duplicates specialist reasoning fields.

**Acceptance Scenarios**:

1. **Given** specialist results from balance and tyre domains, **When** the orchestrator combines them, **Then** the summary contains one sentence per domain describing the key finding, without repeating the physics explanations already present in each change's reasoning.
2. **Given** three specialists each producing 2-3 changes, **When** the orchestrator produces the final response, **Then** the combined summary is no longer than one short paragraph (roughly 3-5 sentences).

---

### User Story 4 - Multi-Lap Signal Confirmation (Priority: P3)

Setup changes are only proposed when the underlying signal is confirmed across multiple laps, filtering out noise and one-off anomalies. Agents explicitly evaluate signal consistency before proposing a change.

**Why this priority**: Eliminating marginal findings reduces both verbosity and recommendation noise, improving recommendation quality.

**Independent Test**: Can be tested by providing a session where a signal (e.g., high understeer) appears in only one lap and verifying no change is proposed for it.

**Acceptance Scenarios**:

1. **Given** a session where high understeer occurs in 1 of 8 flying laps, **When** the balance specialist analyzes it, **Then** no understeer-related setup change is proposed.
2. **Given** a session where high tyre temperatures appear consistently in 6 of 8 laps, **When** the tyre specialist analyzes it, **Then** it proposes a change citing the multi-lap pattern.

---

### Edge Cases

- What happens when a session has very few laps (e.g., 2 flying laps)? The multi-lap confirmation threshold should be relaxed — with 2 laps, both showing the signal counts as confirmed.
- What happens when all signals are marginal and no changes meet the confirmation threshold? The response should explicitly state the car appears well-balanced with no actionable changes, rather than producing empty results silently.
- What happens when a specialist domain has more than 3 strong signals? The specialist should prioritize the 3 most impactful changes (highest severity, most laps affected) and omit the rest.
- How are out-of-domain findings handled? If a specialist detects an issue outside its domain (e.g., tyre specialist noticing aero-related speed loss), it must omit the finding entirely rather than cross-recommending.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each specialist agent MUST produce at most 3 setup changes per analysis, prioritized by severity and multi-lap consistency.
- **FR-002**: Each setup change's reasoning field MUST contain exactly one concrete data citation (metric name + value + affected corners/laps) in one sentence.
- **FR-003**: Each setup change's expected_effect field MUST contain exactly one sentence describing what the driver will feel or notice.
- **FR-004**: Each driving technique feedback observation MUST be one sentence citing specific data evidence.
- **FR-005**: Each driving technique feedback suggestion MUST be one to two sentences of actionable advice.
- **FR-006**: Specialist agents MUST evaluate signal consistency before proposing a change. A signal is confirmed when it appears in at least 2 flying laps. For sessions with more than 3 flying laps, the signal must appear in the majority of them. This evaluation is expressed as a prompt instruction to the agent, not as code logic.
- **FR-007**: Specialist agents MUST omit findings outside their declared domain, even if the data suggests an issue in another domain.
- **FR-008**: The orchestrator summary MUST NOT re-explain vehicle dynamics theory or physics already present in individual change reasoning fields.
- **FR-009**: The orchestrator summary MUST be a short paragraph (3-5 sentences maximum) referencing each domain's key finding in one sentence.
- **FR-010**: The technique specialist MUST produce at most 3 driving feedback entries per analysis.
- **FR-011**: Domain summaries produced by each specialist MUST be one to two sentences maximum.

### Key Entities

- **SetupChange**: A proposed modification to a car setup parameter, with constrained reasoning (one data citation) and expected_effect (one driver-felt sentence).
- **DriverFeedback**: A driving technique observation with constrained observation (one sentence + data) and suggestion (one to two sentences).
- **SpecialistResult**: Output from one domain agent, containing at most 3 setup changes or 3 feedback entries, plus a one-to-two sentence domain summary.
- **EngineerResponse**: Combined output from all specialists, with a lean orchestrator summary that synthesizes without duplicating.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total output token count for a typical analysis is reduced by at least 50% compared to the current baseline (from ~14,400 tokens to under 7,000 tokens on the same session with the same model).
- **SC-002**: No setup change reasoning exceeds two sentences.
- **SC-003**: No driving technique feedback observation exceeds one sentence.
- **SC-004**: No specialist produces more than 3 setup changes or 3 feedback entries in a single analysis.
- **SC-005**: 100% of setup change reasoning fields contain at least one specific data reference (metric + value).
- **SC-006**: The orchestrator summary does not exceed 5 sentences.
- **SC-007**: Actionable content quality is preserved — the same core recommendations (parameter + direction of change) appear in the optimized output as in the verbose baseline for sessions with clear signals.

## Assumptions

- The current data model structure (SetupChange, DriverFeedback, SpecialistResult, EngineerResponse) does not need schema changes — the optimization is achieved through prompt instructions that constrain how agents fill the existing fields.
- The 3-change-per-domain limit is sufficient for all practical sessions; edge cases with 4+ equally critical issues in one domain are rare enough to accept the trade-off.
- Multi-lap confirmation uses the threshold defined in FR-006: at least 2 flying laps, or the majority for sessions longer than 3 flying laps.
- Token reduction targets are based on the Gemini 2.5 Flash baseline of ~14,400 output tokens; other models may show different absolute reductions but the same relative improvement.
