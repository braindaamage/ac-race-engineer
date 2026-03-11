# Feature Specification: Agent Diagnostic Traces

**Feature Branch**: `032-agent-diagnostic-traces`
**Created**: 2026-03-11
**Status**: Draft
**Input**: User description: "Phase 11.2 — Agent Diagnostic Traces"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable Diagnostic Mode (Priority: P1)

A developer or advanced user suspects the AI engineer is producing suboptimal setup recommendations. They navigate to Settings, find the Advanced section, and toggle on a "Diagnostic Mode" option. From this point forward, every engineer analysis and chat interaction captures a complete trace of the agent's internal conversation. When they are done debugging, they toggle it off and the system stops capturing traces — no ongoing storage or performance cost.

**Why this priority**: Without the toggle, no traces are captured. This is the prerequisite for all other functionality.

**Independent Test**: Can be fully tested by toggling the setting on/off and verifying the configuration persists and is readable by the backend.

**Acceptance Scenarios**:

1. **Given** diagnostic mode is off (default), **When** the user opens Settings, **Then** the diagnostic mode toggle is visible in the Advanced section and shows "off".
2. **Given** the user is on the Settings screen, **When** they toggle diagnostic mode on and save, **Then** the configuration persists and the backend reads diagnostic_mode as enabled.
3. **Given** diagnostic mode is on, **When** the user toggles it off and saves, **Then** the system stops capturing traces for subsequent interactions.

---

### User Story 2 - Inspect Engineer Analysis Trace (Priority: P1)

Diagnostic mode is on. The user runs an engineer analysis on a session. After the analysis completes and produces a recommendation, the user sees an indicator next to the recommendation signaling that a diagnostic trace is available. They click on it and see the full multi-agent conversation: the system prompt each specialist received, the user prompt with metrics, every tool call with its parameters and response, every assistant reasoning message, and the final structured result. All specialist agents from the analysis are grouped together in one trace.

**Why this priority**: This is the core debugging capability — understanding why the AI made specific setup recommendations.

**Independent Test**: Can be fully tested by enabling diagnostic mode, running an engineer analysis, and then viewing the trace for the resulting recommendation.

**Acceptance Scenarios**:

1. **Given** diagnostic mode is on, **When** an engineer analysis completes successfully, **Then** a trace file is created and associated with the generated recommendation.
2. **Given** a recommendation has an associated trace, **When** the user views the recommendation in the frontend, **Then** a visual indicator shows that a trace is available.
3. **Given** the user clicks the trace indicator, **Then** the full formatted trace content is displayed, showing all specialist agents' conversations grouped together.
4. **Given** the trace is displayed, **Then** it includes for each specialist: system prompt, user prompt, all assistant messages, all tool calls with parameters, all tool responses, and the final structured result.
5. **Given** diagnostic mode is off, **When** an engineer analysis completes, **Then** no trace file is created and no trace indicator appears on the recommendation.

---

### User Story 3 - Inspect Chat Message Trace (Priority: P2)

Diagnostic mode is on. The user sends a chat message to the engineer. After the assistant responds, the user sees a trace indicator on the assistant's message. They click on it and see the complete conversation: the system prompt, the user message, any tool calls made by the chat agent, tool responses, and the assistant's reasoning and final text response.

**Why this priority**: Chat traces follow the same mechanism as analysis traces but for a simpler single-agent flow. Important for debugging chat quality but secondary to the multi-agent analysis case.

**Independent Test**: Can be fully tested by enabling diagnostic mode, sending a chat message, and viewing the trace for the assistant's response.

**Acceptance Scenarios**:

1. **Given** diagnostic mode is on, **When** the chat agent responds to a user message, **Then** a trace file is created and associated with the generated assistant message.
2. **Given** a message has an associated trace, **When** the user views the message in the engineer chat, **Then** a trace indicator is visible on the assistant message.
3. **Given** the user clicks the trace indicator on a message, **Then** the full formatted trace content is displayed for the chat agent's conversation.
4. **Given** diagnostic mode is off, **When** the chat agent responds, **Then** no trace file is created and no trace indicator appears.

---

### User Story 4 - Traces Are Independent of Normal Operation (Priority: P1)

A user who has never enabled diagnostic mode, or who enabled it and then deleted trace files manually, experiences no difference in application behavior. All existing features — analysis, chat, recommendations, settings — work identically regardless of whether trace files exist or not. The API gracefully reports "no trace available" when queried for a non-existent trace.

**Why this priority**: The feature must not break existing functionality. This is a critical safety requirement.

**Independent Test**: Can be tested by running the full application workflow with diagnostic mode off and verifying all features work normally, then querying the trace API for a recommendation that has no trace and verifying a clean "not available" response.

**Acceptance Scenarios**:

1. **Given** diagnostic mode has never been enabled, **When** the user runs an engineer analysis, **Then** the analysis completes normally with no errors or performance degradation.
2. **Given** a recommendation exists without a trace, **When** the frontend queries for its trace, **Then** the API returns a response indicating no trace is available (not an error).
3. **Given** a trace file was manually deleted, **When** the frontend queries for it, **Then** the API returns "no trace available" without errors.

---

### Edge Cases

- What happens when diagnostic mode is toggled mid-analysis? The toggle state at the moment the agent pipeline starts determines whether traces are captured for that run. Toggling during execution does not affect an in-progress analysis.
- What happens when the trace storage directory does not exist? The system creates it automatically when writing the first trace.
- What happens when disk space is insufficient to write a trace? The trace write failure is logged but does not interrupt the analysis or chat pipeline. The recommendation or message is still saved normally.
- What happens when a trace file is corrupted or contains invalid content? The API returns the raw file content as-is or reports "trace unavailable" if the file cannot be read. The frontend displays what it can or shows an error state.
- What happens when multiple analyses run concurrently with diagnostic mode on? Each analysis writes its own trace file keyed by its unique recommendation ID, so there are no conflicts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `diagnostic_mode` configuration field that defaults to `false`.
- **FR-002**: System MUST NOT capture, persist, or expose any trace data when diagnostic mode is off.
- **FR-003**: When diagnostic mode is on and an engineer analysis runs, the system MUST capture the complete multi-turn conversation for every specialist agent that participates, including: system prompt, user prompt, all assistant messages, all tool calls with parameters, all tool responses, and the final structured output.
- **FR-004**: All agent traces from a single analysis run MUST be grouped together in one trace associated with the recommendation that was generated.
- **FR-005**: When diagnostic mode is on and a chat message is answered, the system MUST capture the complete conversation trace for the chat agent, associated with the assistant message that was generated.
- **FR-006**: Traces MUST be persisted as human-readable files on disk, not in the database.
- **FR-007**: Trace files MUST be inspectable without special tooling — a developer should be able to open the file in a text editor and understand the full agent interaction.
- **FR-008**: The system MUST expose an endpoint to retrieve a trace for a given recommendation ID.
- **FR-009**: The system MUST expose an endpoint to retrieve a trace for a given message ID.
- **FR-010**: When no trace exists for a recommendation or message, the trace retrieval endpoint MUST return a response indicating "no trace available" (not an error status).
- **FR-011**: The frontend MUST display a visual indicator when a diagnostic trace is available for a recommendation or assistant message.
- **FR-012**: The frontend MUST allow the user to view the formatted trace content when they interact with the trace indicator.
- **FR-013**: The diagnostic mode toggle MUST be accessible from the Settings screen in the Advanced section.
- **FR-014**: Trace capture failures MUST NOT interrupt or degrade the engineer analysis or chat pipeline. Failures are logged but the primary operation completes normally.
- **FR-015**: All existing functionality MUST work identically regardless of whether traces are present, absent, or diagnostic mode is on or off.

### Key Entities

- **Diagnostic Trace**: A human-readable record of the complete multi-turn conversation between the system and one or more AI agents during a single engineer analysis or chat interaction. Contains system prompts, user prompts, assistant messages, tool calls, tool responses, and structured outputs. Associated with exactly one recommendation (for analysis traces) or one message (for chat traces). Stored as a file on disk, not in the database.
- **Diagnostic Mode**: A boolean configuration setting that controls whether the system captures trace data. Off by default. When off, the system has zero trace-related overhead.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When diagnostic mode is on, 100% of engineer analyses produce a corresponding trace file that contains the complete conversation for every specialist agent involved.
- **SC-002**: When diagnostic mode is on, 100% of chat interactions produce a corresponding trace file for the chat agent.
- **SC-003**: When diagnostic mode is off, zero trace files are created during any number of analyses or chat interactions.
- **SC-004**: A developer can open any trace file in a text editor and identify within 30 seconds: which agent(s) participated, what tools were called, and what the final result was.
- **SC-005**: The presence or absence of trace files has no observable effect on application behavior — all features work identically in both states.
- **SC-006**: Trace capture adds no measurable overhead to the critical path of analysis or chat operations — trace writing happens after the primary result is obtained and failures do not propagate.
