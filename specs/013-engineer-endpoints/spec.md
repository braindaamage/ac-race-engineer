# Feature Specification: Engineer Endpoints

**Feature Branch**: `013-engineer-endpoints`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Build the Engineer Endpoints for AC Race Engineer (Phase 6.4) — connect the AI engineer layer to the API, enabling the desktop app to request setup recommendations, apply them to .ini files, and have a conversation with the AI race engineer."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the AI Engineer (Priority: P1)

The user opens the desktop app, navigates to an analyzed session, and clicks "Ask Engineer". The backend loads the cached analysis, summarizes it, detects driving signals, routes them to the appropriate specialist agents (balance, tyre, aero, technique), combines the results, and persists a recommendation with setup changes and driver feedback. The user watches real-time progress updates throughout the process. When the job completes, the session state advances to "engineered" and the recommendation is available for review.

**Why this priority**: This is the core value proposition — without AI analysis, there are no recommendations to view, apply, or discuss.

**Independent Test**: Can be fully tested by triggering the engineer on an analyzed session and verifying that a recommendation is created in the database, the session state advances to "engineered", and progress updates are emitted during the job.

**Acceptance Scenarios**:

1. **Given** a session in "analyzed" state, **When** the user triggers the engineer, **Then** a background job is created, progress updates are emitted (loading analysis, detecting signals, running specialists, combining results, saving recommendation, done), and the session state advances to "engineered" upon completion.
2. **Given** a session in "engineered" state, **When** the user triggers the engineer again, **Then** a new recommendation is created (multiple recommendations per session are valid) and the session remains in "engineered" state.
3. **Given** a session in "discovered" or "parsed" state, **When** the user triggers the engineer, **Then** the request is rejected with a conflict error indicating the session must be analyzed first.
4. **Given** a session that does not exist, **When** the user triggers the engineer, **Then** a not-found error is returned.
5. **Given** the LLM provider is unreachable or the API key is not configured, **When** the user triggers the engineer, **Then** the job fails with a clear error message identifying the LLM connectivity issue.
6. **Given** an analyzed session with zero flying laps, **When** the user triggers the engineer, **Then** the job completes successfully with an empty recommendation (no setup changes, no driver feedback) and the session state still advances.

---

### User Story 2 - View Recommendations (Priority: P2)

After the engineer has run, the user views a list of all recommendations for the session. Each recommendation shows its status (proposed/applied/rejected), a plain-language summary, and when it was created. The user can drill into any recommendation to see the full details: proposed setup changes (section, parameter, old value, new value, reasoning, expected effect), driver feedback (area, observation, suggestion, affected corners), and the engineer's overall explanation.

**Why this priority**: Viewing results is the immediate follow-up to running the engineer and must work before the user can decide to apply or discuss changes.

**Independent Test**: Can be tested by running the engineer on a session, then querying the recommendation list and detail endpoints, verifying all fields are populated and match the persisted data.

**Acceptance Scenarios**:

1. **Given** a session with one or more recommendations, **When** the user requests the recommendation list, **Then** all recommendations are returned with their status, summary, and creation timestamp, ordered by creation time.
2. **Given** a specific recommendation ID, **When** the user requests its details, **Then** the full recommendation is returned including setup changes with section, parameter, old value, new value, reasoning, and expected effect, plus driver feedback items.
3. **Given** a recommendation ID that does not exist, **When** the user requests its details, **Then** a not-found error is returned.
4. **Given** a session with no recommendations, **When** the user requests the recommendation list, **Then** an empty list is returned.
5. **Given** a session that does not exist, **When** the user requests recommendations, **Then** a not-found error is returned.

---

### User Story 3 - Apply a Recommendation (Priority: P3)

The user reviews a recommendation and decides to apply it. They click "Apply" and the backend writes the proposed setup changes to the .ini file, creating an automatic timestamped backup first. The recommendation status changes from "proposed" to "applied". The user receives confirmation that changes were written and can see the backup file path.

**Why this priority**: Applying recommendations is the primary action that delivers tangible value — actual setup file modifications. However, it depends on viewing recommendations first.

**Independent Test**: Can be tested by creating a recommendation, then calling the apply endpoint with a valid setup file path, verifying the backup was created, the .ini file was modified, and the recommendation status changed to "applied".

**Acceptance Scenarios**:

1. **Given** a recommendation in "proposed" status, **When** the user applies it with a valid setup file path, **Then** a timestamped backup is created, the changes are written to the .ini file, the recommendation status changes to "applied", and the response includes the backup path and change outcomes.
2. **Given** a recommendation that has already been applied, **When** the user tries to apply it again, **Then** a conflict error is returned indicating it has already been applied.
3. **Given** a recommendation ID that does not exist, **When** the user tries to apply it, **Then** a not-found error is returned.
4. **Given** a setup file path that does not exist or cannot be resolved, **When** the user tries to apply a recommendation, **Then** an error is returned identifying the missing file.
5. **Given** a recommendation whose proposed values fall outside the valid parameter ranges, **When** the user applies it, **Then** the values are clamped to valid ranges and the response includes warnings about the adjustments.

---

### User Story 4 - Chat with the Engineer (Priority: P4)

The user wants to ask follow-up questions about a session. They type a message in the chat interface, and the AI engineer responds with context-aware answers drawing on the session's analysis data. The conversation history is maintained across messages so the engineer remembers what was discussed. The user can also clear the conversation to start fresh.

**Why this priority**: Chat enhances the experience by allowing interactive exploration, but the core analyze-recommend-apply workflow functions without it.

**Independent Test**: Can be tested by sending a chat message for an analyzed session, verifying the AI response is saved, then sending a follow-up and confirming the history is included in context. Also testable by clearing the conversation and verifying messages are deleted.

**Acceptance Scenarios**:

1. **Given** an analyzed session, **When** the user sends a chat message, **Then** a background job is created for the AI response, the user message is saved immediately, and the AI response is saved upon job completion.
2. **Given** a session with existing chat history, **When** the user sends a new message, **Then** the full conversation history is included in the AI request so the engineer maintains context.
3. **Given** a session with chat messages, **When** the user requests the conversation history, **Then** all messages are returned in chronological order with role (user/assistant), content, and timestamp.
4. **Given** a session with chat messages, **When** the user clears the conversation, **Then** all messages for that session are deleted and subsequent history requests return an empty list.
5. **Given** a session in "discovered" or "parsed" state, **When** the user tries to chat, **Then** a conflict error is returned indicating the session must be analyzed first.
6. **Given** a session that does not exist, **When** the user tries to chat, **Then** a not-found error is returned.
7. **Given** the LLM provider is unreachable, **When** the user sends a chat message, **Then** the user message is still saved but the job fails with a clear error message.

---

### Edge Cases

- What happens when the engineer is triggered while a previous engineer job is still running for the same session? The second request is rejected with a conflict error (job already in progress).
- What happens when the LLM returns an empty or malformed response? The job fails with a descriptive error; no recommendation is saved, and the session state does not advance.
- What happens when the setup file has been externally modified between recommendation creation and application? The apply operation reads the current file state, creates a backup of the current version, and writes the changes. The old values in the recommendation may differ from the current file values.
- What happens when the user clears chat messages for one session? Only that session's messages are deleted; other sessions' conversations are unaffected.
- What happens when chat is attempted on a session with no prior engineer run (but the session is analyzed)? Chat works — having run the engineer is not a prerequisite for chatting, only having analysis data is.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an endpoint that triggers the AI engineer pipeline as a tracked background job for a given session.
- **FR-002**: System MUST emit real-time progress updates during the engineer job: loading analysis, detecting signals, running specialist agents, combining results, saving recommendation, done.
- **FR-003**: System MUST advance the session state to "engineered" upon successful completion of the engineer job.
- **FR-004**: System MUST persist the engineer's output (setup changes, driver feedback, explanation) as a recommendation in the database.
- **FR-005**: System MUST support multiple recommendations per session — re-running the engineer creates a new recommendation without overwriting previous ones.
- **FR-006**: System MUST reject engineer requests for sessions that have not been analyzed (state must be "analyzed" or "engineered"), returning a conflict error.
- **FR-007**: System MUST provide an endpoint to list all recommendations for a session, returning status, summary, and creation timestamp.
- **FR-008**: System MUST provide an endpoint to retrieve the full details of a single recommendation, including setup changes and driver feedback.
- **FR-009**: System MUST provide an endpoint that applies a recommendation's setup changes to a .ini file, with automatic timestamped backup creation.
- **FR-010**: System MUST update the recommendation status to "applied" after successful application.
- **FR-011**: System MUST reject apply requests for recommendations that have already been applied, returning a conflict error.
- **FR-012**: System MUST reject apply requests for recommendation IDs that do not exist, returning a not-found error.
- **FR-013**: System MUST provide an endpoint that accepts a user chat message for a session and triggers an AI response as a background job.
- **FR-014**: System MUST persist both user messages and AI responses in the database, scoped by session.
- **FR-015**: System MUST include the full conversation history in each new AI chat request so the engineer maintains context.
- **FR-016**: System MUST provide an endpoint to retrieve the conversation history for a session in chronological order.
- **FR-017**: System MUST provide an endpoint to clear the conversation history for a session.
- **FR-018**: System MUST reject chat requests for sessions that have not been analyzed, returning a conflict error.
- **FR-019**: All engineer endpoints MUST return a not-found error if the referenced session does not exist.
- **FR-020**: System MUST use the LLM provider and model from the user's configuration — no hardcoded provider or model.
- **FR-021**: System MUST fail the job with a clear error message if the LLM API key is not configured or the provider is unreachable.

### Key Entities

- **Recommendation**: A set of proposed setup changes and driver feedback generated by the AI engineer for a specific session. Has a lifecycle status: proposed, applied, or rejected. Multiple recommendations can exist per session.
- **Setup Change**: A single parameter modification within a recommendation, including section, parameter name, old value, new value, reasoning, and expected effect.
- **Driver Feedback**: A driving technique observation including the area of concern, what was observed, a coaching suggestion, affected corners, and severity.
- **Chat Message**: A single turn in a user-engineer conversation, scoped to a session. Has a role (user or assistant), content, and timestamp.
- **Engineer Job**: A background operation that runs the AI pipeline (summarize, detect signals, route to specialists, combine, persist). Tracked by the existing job system with progress updates.
- **Chat Job**: A background operation that generates an AI response to a user chat message. Uses the session's analysis context and conversation history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can trigger the AI engineer on an analyzed session and receive a recommendation with setup change suggestions and driver feedback.
- **SC-002**: Users see at least 5 distinct progress updates during the engineer job, providing continuous feedback on what the system is doing.
- **SC-003**: Users can view all recommendations for a session and drill into any recommendation to see the full details of each proposed change.
- **SC-004**: Users can apply a recommendation to a setup file with one action, and the system creates an automatic backup before making changes.
- **SC-005**: Users can have a multi-turn conversation with the AI engineer about a session, with the engineer maintaining full context of the discussion.
- **SC-006**: Clearing a session's chat history does not affect other sessions' conversations.
- **SC-007**: All error conditions (session not found, session not analyzed, recommendation already applied, LLM unreachable) produce clear, user-understandable error messages.
- **SC-008**: Re-running the engineer on a session creates a new recommendation without destroying previous recommendations.

## Assumptions

- The existing `analyze_with_engineer()` function (Phase 5.3) is stable and handles the full specialist orchestration internally. This phase wraps it in a job-based API endpoint without modifying its internals.
- The existing `apply_recommendation()` function (Phase 5.3) handles backup creation, validation, and .ini file writing. This phase exposes it via an API endpoint.
- The existing job system (Phase 6.1) handles background task execution, progress tracking via WebSocket, and job lifecycle management. This phase creates jobs through that system.
- The existing storage module (Phase 5.1) provides all necessary CRUD operations for recommendations, messages, and sessions. No schema changes are needed.
- The analysis cache (`analyzed.json`) from Phase 6.3 is loaded via `load_analyzed_session()` to reconstruct the AnalyzedSession for summarization.
- Chat AI responses use the same LLM provider and model as the engineer pipeline, configured via ACConfig.
- The `summarize_session()` function compresses the AnalyzedSession into a token-efficient SessionSummary before passing it to the AI agents.

## Out of Scope

- Modifications to the Phase 5 engineer internals (agents, tools, skills, summarizer)
- Frontend UI components — this phase is backend-only
- Real-time telemetry streaming — all analysis is post-session
- Multi-user or authentication — single-user localhost app
- Streaming LLM responses (chat responses are delivered as complete messages when the job finishes)
- Recommendation rejection workflow (the user can manually set status to "rejected" but there is no dedicated reject endpoint in this phase — the status update is handled by the existing storage function)
