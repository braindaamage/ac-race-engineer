# Feature Specification: Principal Agent Narrated Analysis

**Feature Branch**: `033-principal-narrated-analysis`
**Created**: 2026-03-11
**Status**: Draft
**Input**: Phase 12 — Replace mechanical concatenation of specialist domain_summaries with principal-agent-authored summary and explanation fields; display explanation in frontend; persist explanation in database.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Coherent Analysis Summary (Priority: P1)

After running a session analysis, the driver sees a short executive summary (2–4 sentences) written in direct race-engineer language that communicates the general diagnosis and correction strategy. It does not list individual parameter changes or use raw parameter names. It names the dominant problem, mentions severity, and tells the driver what direction the proposed changes take — all in terms a driver understands (e.g., "front anti-roll bar" instead of "ARB_FRONT VALUE").

**Why this priority**: The summary is the first thing the driver reads after every analysis. A coherent, human-quality narrative is the core value of the feature and the minimum viable delivery.

**Independent Test**: Run an analysis with multiple specialist domains activated. Verify the summary is an original narrative paragraph (not a concatenation of domain_summaries), uses driver-friendly language, mentions the dominant issue, and stays within 2–4 sentences.

**Acceptance Scenarios**:

1. **Given** an analyzed session with signals in balance and tyre domains, **When** the analysis completes, **Then** the summary is an original 2–4 sentence paragraph that does not contain domain-name prefixes (e.g., "**Balance**:") and does not duplicate any specialist's domain_summary verbatim.
2. **Given** an analyzed session with only one specialist activated, **When** the analysis completes, **Then** the summary is still an original paragraph authored by the principal agent — not a pass-through of the single specialist's domain_summary.
3. **Given** an analyzed session with no flying laps, **When** the analysis completes, **Then** the summary contains an informative message appropriate to its role (headline diagnosis), distinct from the explanation's message.

---

### User Story 2 - Detailed Explanation Narrative (Priority: P1)

Below the summary, the driver can access a detailed multi-paragraph explanation that connects specialist findings into a unified narrative. It explains cause-effect relationships between proposed changes, describes trade-offs, integrates driving technique observations in context (not as a separate section), references specific corners and data when relevant, and closes with a general expectation of what the driver should feel after applying the changes.

**Why this priority**: The explanation is the second core deliverable — it gives the driver the "why" behind the changes and is equally essential to the feature's value.

**Independent Test**: Run an analysis with at least two specialist domains. Verify the explanation is a multi-paragraph narrative that connects domains causally, mentions at least one trade-off or expectation, and does not literally repeat each change's reasoning field.

**Acceptance Scenarios**:

1. **Given** an analyzed session with balance and tyre signals, **When** the analysis completes, **Then** the explanation is a multi-paragraph text that describes cause-effect relationships across domains and does not mechanically repeat individual change reasoning fields.
2. **Given** an analyzed session with driving technique observations, **When** the analysis completes, **Then** technique findings are woven into the explanation narrative — not presented as a standalone section.
3. **Given** an analyzed session, **When** the analysis completes, **Then** the explanation closes with a general expectation of what the driver should feel after applying the changes.
4. **Given** an analyzed session with no signals detected, **When** the analysis completes, **Then** the explanation contains a differentiated informative message appropriate to its role (detailed analysis), distinct from the summary's message.

---

### User Story 3 - Explanation Visible in Frontend (Priority: P1)

The explanation is displayed to the driver in the frontend. The summary remains the top-level visible text (as today). The explanation appears in an expandable or dedicated section below the summary so the driver can access the full analysis when desired.

**Why this priority**: Without frontend display, the explanation is invisible to the user and the feature delivers no value. This is a hard dependency of User Story 2.

**Independent Test**: Complete an analysis, view the recommendation card. Verify the summary is visible at the top and the explanation is accessible via an expandable section below it.

**Acceptance Scenarios**:

1. **Given** a completed analysis with a recommendation displayed, **When** the driver views the recommendation card, **Then** the summary is visible at the top level and the explanation is accessible below it in a collapsed/expandable section.
2. **Given** the explanation section is collapsed by default, **When** the driver clicks to expand it, **Then** the full multi-paragraph explanation is displayed with proper formatting (paragraphs, line breaks).
3. **Given** a recommendation where the explanation is empty (legacy or fallback data), **When** the driver views the recommendation card, **Then** the expandable section is hidden — no empty container is shown.

---

### User Story 4 - Explanation Persisted in Database (Priority: P2)

The explanation field is saved in the main SQLite database alongside the summary, so it survives cache eviction and is available whenever the recommendation is retrieved.

**Why this priority**: Currently explanation only exists in the JSON cache file. Persisting it in the database ensures durability and consistent availability. This is a structural improvement that supports User Story 3 but is lower priority than the core narrative generation.

**Independent Test**: Run an analysis, then delete the JSON cache file. Retrieve the recommendation via the API. Verify the explanation field is returned from the database.

**Acceptance Scenarios**:

1. **Given** a completed analysis, **When** the recommendation is saved, **Then** the explanation field is stored in the recommendations table in the SQLite database.
2. **Given** a recommendation exists in the database with an explanation, **When** the JSON cache file is missing, **Then** the API still returns the explanation from the database.
3. **Given** an existing database created before this feature (no explanation column), **When** the application starts, **Then** the database is migrated to include the explanation column with a default empty string — no data loss occurs.

---

### User Story 5 - Graceful Degradation on Principal Agent Failure (Priority: P2)

If the principal agent LLM call fails (network error, provider outage, malformed response), the system falls back to the current behavior: summary and explanation are set to the concatenated domain_summaries. The analysis is not lost.

**Why this priority**: Resilience is important but secondary to core functionality. The fallback ensures the system never loses an analysis due to the new principal agent step.

**Independent Test**: Simulate a principal agent LLM failure. Verify the analysis still completes with concatenated domain_summaries as summary and explanation, and no error is surfaced to the user.

**Acceptance Scenarios**:

1. **Given** specialist agents have completed successfully but the principal agent call fails, **When** the analysis pipeline handles the error, **Then** summary and explanation are set to the concatenated domain_summaries (current behavior) and the analysis completes normally.
2. **Given** a principal agent failure occurs, **When** the recommendation is returned to the user, **Then** no error message is shown — the driver sees the fallback summary as if nothing went wrong.

---

### Edge Cases

- What happens when there are zero flying laps? Summary and explanation contain differentiated informative messages appropriate to their roles (not identical text).
- What happens when no signals are detected? Summary and explanation contain differentiated informative messages (e.g., summary: short headline, explanation: expanded reasoning about the clean session).
- What happens when only one specialist domain is activated? The principal agent still produces original summary and explanation — it does not pass through the single specialist's text.
- What happens when the principal agent returns text that exceeds reasonable length? The system accepts it as-is (the prompt guides appropriate length; no hard truncation).
- What happens with legacy recommendations created before this feature? The explanation column defaults to empty string; the frontend hides the expandable section when explanation is empty.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST invoke the principal agent after all specialist agents complete, passing specialist results (domain_summaries, setup changes, driver feedback, signals addressed) as input context.
- **FR-002**: The principal agent MUST produce an original summary (2–4 sentences, executive headline style) that does not concatenate or copy specialist domain_summaries verbatim.
- **FR-003**: The principal agent MUST produce an original explanation (multi-paragraph detailed analysis) that connects specialist findings causally, describes trade-offs, integrates technique observations, and closes with expected driver feel.
- **FR-004**: Summary MUST use driver-understandable terms (e.g., "front anti-roll bar" not "ARB_FRONT VALUE"), mention severity, and name the dominant problem when one exists.
- **FR-005**: Explanation MUST NOT literally repeat each setup change's individual reasoning field — it synthesizes across domains.
- **FR-006**: The recommendations table in the database MUST include an explanation column that is populated when saving a recommendation.
- **FR-007**: The API MUST return the explanation field when serving recommendation details, preferring the database value when the JSON cache is unavailable.
- **FR-008**: The frontend MUST display the explanation in an expandable section below the summary on the recommendation card.
- **FR-009**: The expandable explanation section MUST be collapsed by default and hidden entirely when explanation is empty.
- **FR-010**: When there are no flying laps or no signals detected, summary and explanation MUST contain differentiated messages appropriate to their respective roles.
- **FR-011**: When the principal agent LLM call fails, the system MUST fall back to the current behavior (concatenated domain_summaries for both fields) without surfacing an error to the user.
- **FR-012**: The database migration MUST add the explanation column with a default empty string, preserving all existing data.
- **FR-013**: The principal agent MUST receive the same LLM provider/model configuration as the specialist agents (user-configured provider).

### Key Entities

- **EngineerResponse**: Gains differentiated summary (executive headline) and explanation (detailed narrative) fields — both authored by the principal agent instead of being identical concatenations.
- **Recommendation (DB)**: Gains an explanation column (text, default empty string) alongside the existing summary column.
- **Principal Agent**: An LLM agent invocation using the existing principal.md prompt, receiving specialist results as context and producing structured summary + explanation output.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After analysis, the summary and explanation fields contain different text — they are never identical (except in the no-flying-laps / no-signals edge cases, where they are still differentiated).
- **SC-002**: The summary is between 2 and 4 sentences and does not contain raw parameter identifiers (e.g., "ARB_FRONT", "PRESSURE_LF").
- **SC-003**: The explanation is at least 2 paragraphs when specialists produce findings across multiple domains.
- **SC-004**: The explanation is retrievable from the database even when the JSON cache file is absent.
- **SC-005**: When the principal agent call fails, 100% of analyses still complete successfully with fallback text.
- **SC-006**: The driver can view the full explanation in the frontend within one click (expand action) from the recommendation card.

## Assumptions

- The existing principal.md prompt is sufficient as the base system prompt for the principal agent. Minor adjustments to its content to support the new structured output (summary vs. explanation) are expected but are within scope as prompt refinement, not a "change to specialist agent prompts."
- The principal agent uses the same agent infrastructure already used by specialist agents.
- The principal agent call adds one additional LLM round-trip per analysis. This is acceptable given it runs once per analysis (not per specialist).
- LLM usage tracking captures the principal agent call in the same way it captures specialist calls.
- The principal agent does not need tools — it receives all necessary context as part of its prompt and produces text output only.

## Out of Scope

- Changes to specialist agent prompts or the SpecialistResult model.
- Changes to SetupChange or DriverFeedback models.
- Changes to the chat agent or how principal.md is used for follow-up conversation.
- Internationalization.
- Changes to the apply_recommendation flow.
