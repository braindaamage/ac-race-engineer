# Feature Specification: LLM Tracking Redesign + Chat Fixes

**Feature Branch**: `029-llm-tracking-redesign`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Phase 9.7 — LLM Tracking Redesign + Chat Fixes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decoupled LLM Usage Storage (Priority: P1)

The system stores LLM usage data (tokens, tool calls, timing) in a generic structure that is not tied to any specific feature origin. Both analysis recommendations and chat messages can have associated usage records without schema changes. The existing analysis usage display (summary bar, detail modal) continues to work unchanged after the storage redesign.

**Why this priority**: This is the foundational change that all other stories depend on. Without decoupled storage, chat tracking cannot be added.

**Independent Test**: Can be fully tested by running an analysis job and verifying that usage data is stored in the new tables and displayed correctly in the UI — identical behavior to the current system.

**Acceptance Scenarios**:

1. **Given** the database is freshly created, **When** the system initializes storage, **Then** it creates `llm_events` and `llm_tool_calls` tables (not `agent_usage` / `tool_call_details`).
2. **Given** an analysis job completes with LLM usage data, **When** the system persists the usage, **Then** each specialist agent's usage is stored as an `llm_events` row with `event_type="analysis"`, the agent's domain as `agent_name`, and `context_type="recommendation"` with the recommendation ID as `context_id`.
3. **Given** an analysis recommendation has stored usage data, **When** the user views the recommendation in the Engineer view, **Then** the UsageSummaryBar displays the same token counts, tool call count, and agent count as before the redesign.
4. **Given** an analysis recommendation has stored usage data, **When** the user clicks "Details" on the UsageSummaryBar, **Then** the UsageDetailModal shows per-agent breakdowns with tool call details, identical to the current behavior.

---

### User Story 2 - Chat Message Token Tracking (Priority: P2)

When the user sends a chat message and the AI responds, the system captures the principal agent's token usage and tool calls. The user can see how many tokens each chat response consumed, giving visibility into LLM costs across all interaction types.

**Why this priority**: This is the primary new capability enabled by the decoupled storage. It fills a visibility gap where chat usage was invisible.

**Independent Test**: Can be tested by sending a chat message in the Engineer view and verifying that token usage appears below the assistant's response.

**Acceptance Scenarios**:

1. **Given** a user sends a chat message in the Engineer view, **When** the AI responds successfully, **Then** the system stores an `llm_events` row with `event_type="chat"`, `agent_name="principal"`, `context_type="message"`, and `context_id` equal to the saved message ID.
2. **Given** the principal agent uses tools (e.g., `get_lap_detail`, `get_corner_metrics`) during a chat response, **When** usage is captured, **Then** each tool call is stored as an `llm_tool_calls` row linked to the chat event.
3. **Given** LLM usage capture fails during a chat job, **When** the failure occurs, **Then** the assistant message is still saved and delivered to the user — tracking failure does not block the chat response.
4. **Given** an assistant message has associated usage data, **When** the user views the conversation in the Engineer view, **Then** a UsageSummaryBar appears below the assistant message showing token totals and tool call count.
5. **Given** an assistant message has associated usage data, **When** the frontend requests usage for that message, **Then** the system returns the usage data via `GET /sessions/{id}/messages/{message_id}/usage` in the same response schema used for recommendation usage.

---

### User Story 3 - Driver Feedback Display Fix (Priority: P3)

Driver feedback items associated with a recommendation appear only once in the conversation — inside the recommendation card. Currently, feedback items are rendered both inside the recommendation card and again in the parent message list, causing visual duplication.

**Why this priority**: This is a UI bug fix with no dependencies. Lower priority because it is cosmetic, but straightforward to resolve.

**Independent Test**: Can be tested by viewing a recommendation with driver feedback in the Engineer view and counting that each feedback item appears exactly once.

**Acceptance Scenarios**:

1. **Given** a recommendation with driver feedback items exists, **When** the user views it in the Engineer view message list, **Then** each feedback item appears exactly once, inside the RecommendationCard.
2. **Given** a recommendation with multiple driver feedback items, **When** displayed in the message list, **Then** the feedback items maintain their existing visual style and order within the RecommendationCard.

---

### Edge Cases

- What happens when a chat message is sent but the LLM returns zero tool calls? The `llm_events` row is still created with `tool_call_count=0` and no `llm_tool_calls` rows.
- What happens when usage capture partially fails (event saved but tool calls fail)? The event row is kept; missing tool call details are acceptable since tracking is non-critical.
- What happens when the frontend requests usage for a message that has no usage record? The endpoint returns an empty/null response and the UI does not render the UsageSummaryBar for that message.
- What happens when an analysis job produces multiple recommendations? Each recommendation gets its own set of `llm_events` rows, as before.
- What happens when a chat response references a session that no longer exists? The `session_id` field allows orphaned records — no cascading deletion is required for usage data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the `agent_usage` and `tool_call_details` tables with `llm_events` and `llm_tool_calls` tables.
- **FR-002**: The `llm_events` table MUST include: `id`, `session_id`, `event_type` (with initial values "analysis" and "chat"), `agent_name`, `model`, `input_tokens`, `output_tokens`, `request_count`, `tool_call_count`, `duration_ms`, `created_at`, `context_type` (nullable, with initial values "recommendation" and "message"), and `context_id` (nullable). These fields MUST NOT use database-level CHECK constraints — new event types or context types must be addable without schema changes.
- **FR-003**: The `llm_tool_calls` table MUST include: `id`, `event_id` (foreign key to `llm_events`), `tool_name`, `response_tokens`, and `call_index`.
- **FR-004**: The analysis pipeline MUST persist usage data to the new tables with `event_type="analysis"` and `context_type="recommendation"`.
- **FR-005**: The chat pipeline MUST capture token usage from the principal agent's response and persist it to the new tables with `event_type="chat"`, `agent_name="principal"`, `context_type="message"`, and `context_id` set to the saved message's ID.
- **FR-006**: The chat pipeline MUST capture tool call details (tool name, response tokens, call index) for any tools invoked by the principal agent during chat.
- **FR-007**: Chat message saving MUST NOT fail if usage capture encounters an error. Usage tracking is non-critical.
- **FR-008**: System MUST expose `GET /sessions/{id}/messages/{message_id}/usage` returning the same response schema as the existing recommendation usage endpoint.
- **FR-009**: The existing recommendation usage endpoint (`GET /sessions/{id}/recommendations/{rec_id}/usage`) MUST continue to return correct data from the new tables.
- **FR-010**: The UsageSummaryBar component MUST appear below each assistant chat message that has associated usage data.
- **FR-011**: The UsageSummaryBar MUST NOT appear below assistant messages that have no usage data.
- **FR-012**: The duplicate driver feedback rendering in the message list MUST be removed. DriverFeedbackCard components MUST only be rendered inside RecommendationCard.

### Key Entities

- **LLM Event**: A record of one agent invocation — captures the agent identity, token counts, timing, and an optional link to the originating context (recommendation or message).
- **LLM Tool Call**: A record of a single tool invocation within an LLM event — captures the tool name, response size, and call order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing analysis usage features (UsageSummaryBar, UsageDetailModal) display identical information after the storage redesign — zero regressions in displayed data.
- **SC-002**: Every chat response from the AI has a corresponding usage record accessible via the message usage endpoint — 100% capture rate when the LLM call succeeds.
- **SC-003**: Chat messages are delivered to the user even when usage capture fails — message delivery is never blocked by tracking errors.
- **SC-004**: Each driver feedback item appears exactly once in the Engineer view conversation — zero duplicate renders.
- **SC-005**: All existing tests continue to pass after the storage migration, and new tests cover the new tables, chat tracking, message usage endpoint, and the feedback render fix.

## Assumptions

- The database is deleted and recreated from scratch — no data migration is needed.
- The existing `UsageTotals` and `AgentUsageDetail` response models are sufficient for the message usage endpoint (same schema, different context).
- The principal agent is the only agent used in chat jobs — no specialist agents are involved in chat.
- The `request_count` field in `llm_events` corresponds to the number of LLM API requests made during the agent run (may be >1 if the agent loops with tool calls).
- The `call_index` field in `llm_tool_calls` is a zero-based ordinal indicating the order in which tool calls were made within a single event.
- The `event_type` and `context_type` fields in `llm_events` use open string values, not database-level CHECK constraints. Validation of allowed values is the responsibility of the application layer, not the schema.
