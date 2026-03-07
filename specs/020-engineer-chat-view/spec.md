# Feature Specification: Engineer Chat View

**Feature Branch**: `020-engineer-chat-view`
**Created**: 2026-03-06
**Status**: Draft
**Input**: Phase 7.6 — Engineer Chat view for the AC Race Engineer desktop application

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trigger Full Session Analysis (Priority: P1)

The driver has completed a practice session and the telemetry has been analyzed. They navigate to the Engineer view to understand what the AI race engineer thinks about their driving and setup. They see the conversation area is empty with a clear prompt to start the analysis. They click a button to trigger a full session analysis. A progress indicator shows the engineer is working. When the analysis completes, the engineer's response appears in the conversation as a combination of plain-text explanation, structured setup recommendation cards, and driving technique observations. The driver can read the engineer's reasoning and understand what changes are suggested and why.

**Why this priority**: This is the core value proposition of the entire application — getting AI-powered setup advice from telemetry. Without this, the Engineer view has no purpose.

**Independent Test**: Can be fully tested by selecting an analyzed session, triggering analysis, and verifying the engineer response renders with recommendation cards and technique feedback.

**Acceptance Scenarios**:

1. **Given** a session in "analyzed" state is selected, **When** the driver opens the Engineer view, **Then** they see an empty conversation area with a prompt to start analysis and a button to trigger it.
2. **Given** the driver triggers a full analysis, **When** the engineer job is running, **Then** a progress indicator is visible showing the current step and percentage.
3. **Given** the engineer job completes, **When** the response is rendered, **Then** setup recommendations appear as structured cards showing parameter, current value, proposed value, and reasoning.
4. **Given** the engineer job completes, **When** the response includes driving technique feedback, **Then** technique observations appear with the area, observation, suggestion, and affected corners.
5. **Given** the engineer job fails, **When** the error is reported, **Then** the driver sees a clear error message and can retry.

---

### User Story 2 - Ask Follow-Up Questions (Priority: P2)

After the initial analysis (or instead of it), the driver wants to ask the engineer a specific question — for example, "I feel understeer in Turn 3, what can I do?" or "Can you explain why you want to increase front ARB?". They type their question in an input field and submit it. The engineer processes the question with the full session context and responds in the conversation. The driver can continue asking follow-up questions in a natural back-and-forth flow.

**Why this priority**: Follow-up conversation transforms the tool from a one-shot report into an interactive engineering session, which is far more valuable for learning and iterating on setup.

**Independent Test**: Can be tested by selecting an analyzed session, typing a question, submitting it, and verifying the assistant response appears in the conversation thread.

**Acceptance Scenarios**:

1. **Given** the Engineer view is open with an analyzed session, **When** the driver types a message and submits it, **Then** the message appears in the conversation as a user bubble.
2. **Given** a user message has been submitted, **When** the chat job is running, **Then** a typing indicator shows the engineer is generating a response.
3. **Given** the chat job completes, **When** the response is rendered, **Then** the assistant message appears in the conversation below the user message.
4. **Given** the driver has already received a response, **When** they type another question and submit, **Then** the new exchange appends to the existing conversation thread.
5. **Given** the chat job fails, **When** the error is reported, **Then** the driver sees an error message and the input field remains enabled for retry.

---

### User Story 3 - Apply Setup Recommendations (Priority: P2)

The engineer has recommended changes to the car setup (e.g., increase front anti-roll bar by 2 clicks). The driver sees each recommendation as a card in the conversation with a clear "Apply" action. Before applying, the driver sees a confirmation showing exactly what will be written to the .ini file (parameter, section, old value, new value). After confirming, the changes are applied to the setup file and a backup of the original is created. The card updates to reflect the applied status.

**Why this priority**: Applying changes closes the loop from analysis to action. Without this, the driver would need to manually edit .ini files, which defeats the purpose of the tool.

**Independent Test**: Can be tested by triggering an analysis that produces setup changes, clicking apply on a recommendation card, confirming the changes, and verifying the setup file is modified and the card shows "applied" status.

**Acceptance Scenarios**:

1. **Given** the conversation contains a recommendation with setup changes, **When** the driver clicks "Apply" on the recommendation card, **Then** a confirmation dialog appears showing each change (section, parameter, current value, new value).
2. **Given** the confirmation dialog is open, **When** the driver confirms, **Then** the changes are applied to the setup .ini file and a backup is created.
3. **Given** the changes have been applied, **When** the operation succeeds, **Then** the recommendation card updates to show "Applied" status and the apply button is disabled.
4. **Given** the confirmation dialog is open, **When** the driver cancels, **Then** no changes are made and the recommendation remains in "proposed" status.
5. **Given** a recommendation has already been applied, **When** the driver views it, **Then** the apply button is disabled and the card shows "Applied" status.

---

### User Story 4 - Persistent Conversation History (Priority: P3)

The driver has had a conversation with the engineer about a particular session. They navigate away to look at lap data or compare setups, then return to the Engineer view for the same session. The full conversation history is still there — all messages, recommendation cards, and technique feedback — exactly as they left it.

**Why this priority**: Persistence prevents loss of valuable analysis and allows the driver to reference previous advice across app sessions. Important for usability but not a blocker for core functionality.

**Independent Test**: Can be tested by having a conversation, navigating away, returning to the Engineer view for the same session, and verifying all messages and recommendation cards are restored.

**Acceptance Scenarios**:

1. **Given** a conversation exists for a session, **When** the driver navigates away and returns to the Engineer view for the same session, **Then** the full conversation history is displayed in chronological order.
2. **Given** a conversation exists with applied recommendations, **When** the history is loaded, **Then** recommendation cards show their current status (proposed, applied, or rejected).
3. **Given** the driver switches to a different session, **When** the Engineer view loads, **Then** the conversation for the new session is shown (or empty state if no conversation exists).

---

### User Story 5 - Progress and Status Indicators (Priority: P3)

While the engineer is working — either on a full analysis or a chat response — the driver sees clear visual feedback. For a full analysis, a progress bar shows the current step (loading session, summarizing, analyzing, etc.) with a percentage. For a chat response, a typing indicator (animated dots or similar) appears at the bottom of the conversation. The driver always knows whether the system is working, idle, or encountered an error.

**Why this priority**: Feedback during async operations is essential for trust and usability, but the actual analysis and chat features work without it.

**Independent Test**: Can be tested by triggering an analysis or chat job and verifying progress indicators appear, update, and disappear when the job completes.

**Acceptance Scenarios**:

1. **Given** a full analysis job is running, **When** the job progresses, **Then** a progress bar with step description and percentage is visible in the conversation area.
2. **Given** a chat response job is running, **When** the job is in the "generate" step, **Then** a typing indicator appears at the bottom of the conversation.
3. **Given** any job completes, **When** the result is rendered, **Then** the progress or typing indicator disappears.
4. **Given** the driver submits a message while a job is already running, **When** they try to submit, **Then** the input is disabled to prevent overlapping requests.

---

### Edge Cases

- What happens when the driver opens the Engineer view for a session that is not yet analyzed? They see an informative empty state directing them to process the session first.
- What happens when the driver tries to apply a recommendation but the setup file no longer exists (was moved or deleted)? An error message explains the file was not found and the recommendation remains in "proposed" status.
- What happens when applying a recommendation and a parameter value is outside the valid range? The validation step catches it and the confirmation dialog warns the driver before applying.
- What happens when the driver has no internet connection or LLM API key is not configured? The analysis/chat job fails with a clear error explaining the issue.
- What happens when the conversation history is very long (many messages)? The conversation scrolls, and the view auto-scrolls to the latest message. Older messages remain accessible by scrolling up.
- What happens when the driver triggers a full analysis on a session that already has an engineer response? The new analysis starts a fresh conversation, with a confirmation prompt to avoid accidental overwrites.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The view MUST display an empty state with a call-to-action when no conversation exists for the selected session.
- **FR-002**: The view MUST provide a button to trigger a full AI session analysis that creates an engineer job.
- **FR-003**: The view MUST render the engineer's analysis response in the conversation thread, including plain-text summary and explanation.
- **FR-004**: The view MUST render setup change recommendations as structured cards showing: section, parameter name, current value, proposed value, confidence level, reasoning, and expected effect.
- **FR-005**: The view MUST render driving technique feedback as distinct observations showing: area, observation, suggestion, affected corners, and severity.
- **FR-006**: The view MUST provide a text input for the driver to type and submit free-form questions to the engineer.
- **FR-007**: The view MUST display user messages and assistant messages in a chronological conversation thread.
- **FR-008**: Each recommendation card MUST have an "Apply" action that opens a confirmation step before writing changes to the setup file.
- **FR-009**: The confirmation step MUST show all changes that will be written: section, parameter, old value, and new value.
- **FR-010**: After successful application, the recommendation card MUST update its visual status to "Applied" and disable the apply action.
- **FR-011**: The view MUST load and display the full conversation history when the driver returns to the Engineer view for a session that has prior messages.
- **FR-012**: The view MUST show a progress indicator with step description and percentage during a full analysis job.
- **FR-013**: The view MUST show a typing indicator when the engineer is generating a chat response.
- **FR-014**: The text input MUST be disabled while a job (analysis or chat) is in progress to prevent overlapping requests.
- **FR-015**: The view MUST auto-scroll to the latest message when new content is added to the conversation.
- **FR-016**: The view MUST display an informative empty state when the selected session has not been analyzed yet.
- **FR-017**: The view MUST handle job failures by displaying a clear error message and allowing the driver to retry.
- **FR-018**: Recommendation cards for already-applied changes MUST show "Applied" status and have the apply action disabled on load.
- **FR-019**: The view MUST warn the driver before triggering a new full analysis on a session that already has an existing conversation, to prevent accidental loss of context.

### Key Entities

- **Conversation Message**: A single exchange in the chat thread — has a role (user or assistant), text content, and timestamp. Messages are ordered chronologically and persist across app sessions.
- **Recommendation Card**: A structured representation of one AI-generated recommendation within the conversation — contains a group of setup changes with a summary, current status (proposed, applied, rejected), and an apply action.
- **Setup Change**: A single parameter modification within a recommendation — identifies the setup section and parameter, shows current and proposed values, and includes the engineer's reasoning and expected effect.
- **Driving Technique Observation**: A non-setup feedback item from the engineer — describes a driving behavior area, what was observed, what to improve, which corners are affected, and severity.
- **Engineer Job**: An asynchronous background task that runs the full AI analysis pipeline — tracks progress through steps (loading, summarizing, analyzing) and produces an engineer response.
- **Chat Job**: An asynchronous background task that generates a single assistant response to a user question — tracks progress and produces a text response persisted as a message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The driver can go from selecting an analyzed session to reading the engineer's full analysis (with recommendation cards and technique feedback) in a single interaction flow.
- **SC-002**: The driver can ask at least 5 consecutive follow-up questions in a single conversation and receive contextually relevant responses each time.
- **SC-003**: 100% of setup recommendation cards display all required fields: parameter name, current value, proposed value, reasoning, and confidence level.
- **SC-004**: The driver can apply a recommendation to the setup file in 2 actions or fewer (click Apply, confirm).
- **SC-005**: Conversation history is fully preserved when the driver navigates away and returns to the Engineer view for the same session — zero message loss.
- **SC-006**: Progress indicators are visible within 1 second of a job starting, and disappear within 1 second of a job completing.
- **SC-007**: The driver always knows the current system state: idle, working (with progress), or error — there is no ambiguous "stuck" state.
- **SC-008**: Applied recommendation cards are visually distinct from proposed ones, and cannot be re-applied.

### Assumptions

- The backend API endpoints for engineer analysis, chat, recommendations, and message history already exist and are fully functional (Phase 6).
- The WebSocket job progress infrastructure is in place and working for both engineer and chat jobs.
- The driver must have a valid LLM API key configured before using the Engineer view; the view does not handle API key setup (that is the Settings/Onboarding flow).
- Setup files referenced by the session exist on disk at the expected path when applying recommendations.
- The conversation for a session is a single linear thread (no branching or parallel conversations per session).
- The "clear conversation" action (deleting all messages) is not part of this phase's scope; the existing backend endpoint exists but the UI does not expose it.
