# Feature Specification: Usage Storage

**Feature Branch**: `023-usage-storage`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Sub-phase 9.1 — Usage Storage. Add two new SQLite tables to persist LLM agent token consumption data. Data infrastructure only — no endpoints or UI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save Agent Execution Usage (Priority: P1)

After the AI engineer pipeline runs one or more specialist agents (balance, tyre, aero, technique, principal), the system persists a usage record for each agent execution capturing the model used, token counts, tool call count, turn count, duration, and its relationship to the recommendation.

**Why this priority**: Without the ability to save usage records, no downstream feature (cost dashboards, budgets, analytics) can exist.

**Independent Test**: Can be fully tested by calling the save function with valid data and verifying the record is retrievable from the database.

**Acceptance Scenarios**:

1. **Given** a completed agent execution with known token counts, **When** the save function is called, **Then** a new row exists in the agent usage table with all fields populated and a generated primary key.
2. **Given** a recommendation ID that does not exist, **When** the save function is called referencing it, **Then** a foreign key error is raised and no row is created.
3. **Given** an existing usage record, **When** any update is attempted, **Then** there is no update function available — records are write-once.

---

### User Story 2 - Save Tool Call Details (Priority: P1)

For each agent execution, the system persists individual tool call records capturing the tool name, token cost, and timestamp, linked to the parent usage record.

**Why this priority**: Tool-level granularity is essential for understanding which tools drive token consumption.

**Independent Test**: Can be fully tested by saving a usage record, then saving tool call records against it, and verifying retrieval.

**Acceptance Scenarios**:

1. **Given** a saved usage record, **When** tool call details are saved referencing it, **Then** new rows exist in the tool calls table with correct foreign key linkage.
2. **Given** a usage record ID that does not exist, **When** a tool call detail is saved referencing it, **Then** a foreign key error is raised.
3. **Given** a usage record with multiple tool calls, **When** tool calls are saved in a single transaction, **Then** all rows are persisted atomically.

---

### User Story 3 - Retrieve Usage Records (Priority: P2)

A caller can retrieve all usage records for a given recommendation, with their associated tool call details populated.

**Why this priority**: Reading stored data is needed by future phases but is secondary to the write path for this data-infrastructure sub-phase.

**Independent Test**: Can be tested by saving known data and verifying the retrieval function returns complete, correctly structured results.

**Acceptance Scenarios**:

1. **Given** a recommendation with two agent executions (each with tool calls), **When** the retrieval function is called, **Then** it returns two usage records ordered by creation time, each with their tool calls populated.
2. **Given** a recommendation with no usage records, **When** the retrieval function is called, **Then** it returns an empty list.

---

### Edge Cases

- What happens when the database is freshly created (no prior tables)? The migration must create the new tables alongside existing ones.
- What happens when the migration runs on an existing database that already has the new tables? It must be a no-op (idempotent).
- What happens when a recommendation is deleted? The usage records and their tool call details should cascade-delete via foreign keys.
- What happens when very large token counts are stored (millions)? SQLite INTEGER handles up to 2^63, so no issue.
- What happens when `duration_ms` is zero (instant execution)? Valid — no minimum enforced.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create an `agent_usage` table during database initialization, with columns: `usage_id` (TEXT PK), `recommendation_id` (TEXT FK → recommendations), `domain` (TEXT, constrained to known values), `model` (TEXT), `input_tokens` (INTEGER), `output_tokens` (INTEGER), `tool_call_count` (INTEGER), `turn_count` (INTEGER), `duration_ms` (INTEGER), `created_at` (TEXT).
- **FR-002**: System MUST create a `tool_call_details` table during database initialization, with columns: `detail_id` (TEXT PK), `usage_id` (TEXT FK → agent_usage), `tool_name` (TEXT), `token_count` (INTEGER), `called_at` (TEXT).
- **FR-003**: The `tool_call_details.usage_id` foreign key MUST reference `agent_usage.usage_id` with ON DELETE CASCADE.
- **FR-004**: The `agent_usage.recommendation_id` foreign key MUST reference `recommendations.recommendation_id` with ON DELETE CASCADE.
- **FR-005**: The migration MUST be additive and idempotent, using `CREATE TABLE IF NOT EXISTS` in the `_MIGRATIONS` list of `storage/db.py`.
- **FR-006**: System MUST provide a `save_agent_usage` function that persists a usage record and its associated tool call details in a single transaction, generating UUIDs for all primary keys.
- **FR-007**: System MUST provide a `get_agent_usage` function that retrieves all usage records for a given recommendation, each with tool call details populated, ordered by `created_at` ascending.
- **FR-008**: System MUST define Pydantic v2 models `AgentUsage` and `ToolCallDetail` in `storage/models.py`, following the existing model conventions.
- **FR-009**: The `domain` column MUST be constrained via CHECK to: `'balance'`, `'tyre'`, `'aero'`, `'technique'`.
- **FR-010**: All numeric fields (`input_tokens`, `output_tokens`, `tool_call_count`, `turn_count`, `duration_ms`, `token_count`) MUST be non-negative (≥ 0).
- **FR-011**: No update or delete functions MUST be provided for usage records — they are immutable once written.
- **FR-012**: New functions and models MUST be exported from `storage/__init__.py`.

### Key Entities

- **AgentUsage**: A record of a single specialist agent execution — tracks which recommendation it belongs to, the agent domain, LLM model identifier, token input/output counts, number of tool calls, number of conversation turns, execution duration in milliseconds, and creation timestamp.
- **ToolCallDetail**: A record of an individual tool invocation within an agent execution — tracks which usage record it belongs to, the tool function name, the tokens consumed by the tool's response, and the timestamp of the call.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All new storage functions are covered by automated tests with ≥ 95% line coverage.
- **SC-002**: Database initialization on a fresh database creates all 7 tables (5 existing + 2 new) without errors.
- **SC-003**: Database initialization on an existing database with all tables completes without errors (idempotent).
- **SC-004**: Saving a usage record with 10 tool call details completes in a single transaction — either all rows are persisted or none are.
- **SC-005**: Retrieving usage records for a recommendation returns correctly structured data with tool call details nested inside each usage record.
- **SC-006**: Cascade deletion of a recommendation removes all associated usage records and tool call details.

## Assumptions

- The `domain` values cover the four specialist agents only (`balance`, `tyre`, `aero`, `technique`). The principal agent is an orchestrator that combines specialist results and does not have its own independent token consumption tracked.
- Tool call `token_count` represents the number of tokens in the tool's response (output), not the prompt tokens used to call it.
- The `model` field stores the full model identifier string (e.g., `"claude-sonnet-4-20250514"`, `"gemini-2.0-flash"`).
- UUIDs are generated as 32-character hex strings (matching the `uuid.uuid4().hex` pattern used elsewhere).
- The `created_at` and `called_at` timestamps use ISO 8601 format in UTC (matching existing convention).
