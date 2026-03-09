# Feature Specification: Usage Capture

**Feature Branch**: `024-usage-capture`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Sub-phase 9.2 — Usage Capture: instrument the agent pipeline to capture token usage after each specialist agent execution and expose it via a new API endpoint."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Usage Tracking After Analysis (Priority: P1)

When a developer or user runs the AI engineer pipeline (triggering specialist agents to analyze a session and produce setup recommendations), the system automatically captures how many tokens each specialist agent consumed, how many tool calls it made, how long it ran, and the token cost of each individual tool call. This data is persisted to the database without any additional user action.

**Why this priority**: This is the core instrumentation that enables all observability. Without capturing the data, neither the endpoint nor the logs are useful.

**Independent Test**: Can be fully tested by running an engineer analysis and then querying the database to verify that usage records exist for each specialist agent that ran, with correct token counts, tool call details, and timing information.

**Acceptance Scenarios**:

1. **Given** the engineer pipeline runs an analysis that routes to two specialist agents (e.g., balance and tyre), **When** both agents complete successfully, **Then** two usage records are persisted to the database — one per agent — each containing the agent's domain name, input token count, output token count, tool call count, turn count, and execution duration.
2. **Given** a specialist agent makes three tool calls during execution, **When** the agent completes, **Then** three tool call detail records are persisted, each containing the tool name and the token count of that tool's response.
3. **Given** a specialist agent completes execution, **When** the system attempts to persist usage data but the database write fails, **Then** the pipeline continues normally and delivers the recommendation to the user without error.
4. **Given** the engineer pipeline runs an analysis, **When** each specialist agent completes, **Then** a log entry is written summarizing that agent's domain name, input tokens, output tokens, tool call count, and execution duration.

---

### User Story 2 - Retrieve Usage Data for a Recommendation (Priority: P2)

A developer queries a dedicated endpoint with a recommendation identifier and receives a complete breakdown of the token usage for that analysis: an aggregated total across all agents plus per-agent detail including individual tool call information.

**Why this priority**: This is the consumption side of the data captured in P1. It enables cost monitoring and debugging without direct database access.

**Independent Test**: Can be fully tested by querying the endpoint for a recommendation that has usage records and verifying the response contains correct aggregated totals and per-agent breakdowns.

**Acceptance Scenarios**:

1. **Given** a recommendation exists with usage records for three specialist agents, **When** a client requests usage data for that recommendation, **Then** the response contains an aggregated total (sum of input tokens, sum of output tokens, total tool calls across all agents) and a per-agent breakdown with each agent identified by its domain name (balance, tyre, aero, or technique).
2. **Given** a recommendation identifier that does not exist in the system, **When** a client requests usage data for that identifier, **Then** the system responds with a not-found error.
3. **Given** a recommendation exists but no usage records were captured for it (e.g., usage capture failed or the recommendation predates this feature), **When** a client requests usage data, **Then** the response contains zero totals and an empty agent breakdown.

---

### Edge Cases

- What happens when the agent pipeline captures usage for some agents but fails for others? The successfully captured records are preserved; the failed ones are simply missing from the aggregation.
- What happens when a specialist agent makes zero tool calls? The usage record shows tool_call_count as zero and the tool call details list is empty.
- What happens when the Pydantic AI result object contains unexpected or missing token data? The system uses zero as the default for missing numeric values and logs a warning.
- What happens when a recommendation was created before this feature existed? The endpoint returns zero totals and an empty breakdown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST capture token usage data (input tokens, output tokens) from each specialist agent's execution result after it completes.
- **FR-002**: The system MUST capture the number of tool calls made by each specialist agent.
- **FR-003**: The system MUST capture the name and token count of each individual tool call, extracted from the agent's message history after execution.
- **FR-004**: The system MUST capture the number of conversation turns for each specialist agent.
- **FR-005**: The system MUST capture the wall-clock execution duration (in milliseconds) for each specialist agent.
- **FR-006**: The system MUST persist all captured usage data to the database using the existing storage functions before the pipeline moves on to the next agent or to result combination.
- **FR-007**: If capturing or persisting usage data fails for any reason, the system MUST continue the pipeline normally and deliver recommendations without interruption.
- **FR-008**: The system MUST write a structured log entry for each specialist agent after it completes, summarizing its domain name, input tokens, output tokens, tool call count, and execution duration.
- **FR-009**: The system MUST expose a read endpoint that accepts a recommendation identifier and returns aggregated usage data (total input tokens, total output tokens, total tool calls) alongside a per-agent breakdown.
- **FR-010**: The per-agent breakdown MUST identify each agent by its domain name (balance, tyre, aero, technique), not by internal identifiers.
- **FR-011**: The endpoint MUST return a not-found error when the recommendation identifier does not exist.
- **FR-012**: The endpoint MUST return zero totals and an empty breakdown when a recommendation exists but has no usage records.

### Key Entities

- **Agent Usage Record**: Represents one specialist agent's resource consumption for a single analysis run. Contains domain, token counts (input/output), tool call count, turn count, execution duration, and a link to the recommendation it belongs to.
- **Tool Call Detail**: Represents one tool invocation within an agent's execution. Contains the tool name and the token count of the tool's response. Belongs to an Agent Usage Record.
- **Usage Aggregation**: A computed view that sums token counts and tool calls across all Agent Usage Records for a given recommendation, presented alongside the individual breakdowns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After every successful engineer analysis, 100% of specialist agents that ran have a corresponding usage record in the database with non-zero token counts.
- **SC-002**: A failure in usage capture or persistence never prevents the user from receiving their setup recommendation.
- **SC-003**: The usage endpoint returns the complete breakdown for any recommendation within 500 milliseconds.
- **SC-004**: Developers can identify per-agent token costs from the application logs without querying the database.
- **SC-005**: The usage endpoint returns correct aggregated totals that equal the sum of individual agent records.

## Assumptions

- The agent execution framework exposes token usage data (input tokens, output tokens) via a documented attribute after each agent completes. The exact attribute path will be determined during implementation planning.
- The existing storage functions for agent usage (from sub-phase 9.1) are stable and ready for use.
- The recommendation record is persisted before usage capture occurs, so the foreign key relationship is valid.
- Tool call token counts are approximated from the message history content; exact per-tool token accounting depends on what the execution framework exposes.
- The log format follows the project's existing logging conventions.
