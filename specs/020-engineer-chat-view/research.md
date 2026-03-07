# Research: Engineer Chat View

**Branch**: `020-engineer-chat-view` | **Date**: 2026-03-06

## R1: Chat Message Rendering Strategy

**Decision**: Render conversation as a flat, chronological list of typed message bubbles. Each message has a `role` ("user" or "assistant") and `content`. After an engineer analysis completes, fetch the recommendation detail and interleave structured recommendation/feedback cards within the assistant message that produced them.

**Rationale**: The backend stores messages as simple role+content pairs in SQLite. Recommendations are a separate entity linked to the session, not to individual messages. The frontend must bridge these two: when an assistant message is rendered after an engineer analysis, the recommendation detail (setup changes + driver feedback) is fetched and rendered as structured cards inline below that assistant message's text.

**Alternatives considered**:
- Separate recommendations panel alongside chat: Rejected per user requirement ("recommendation cards should be distinct message types within the chat, not separate UI sections").
- Embed recommendation data in message content as JSON: Rejected because backend stores plain text content; structured data lives in the recommendations table.

## R2: Rendering Recommendations in the Conversation Feed

**Decision**: The conversation feed is a merge-sorted chronological list of two independent entity types: `MessageResponse[]` (from GET /messages) and `RecommendationSummary[]` (from GET /recommendations). Both have a `created_at` timestamp. The frontend merges them into a single `FeedItem[]` array sorted by `created_at` ascending. Each item is either a `{ type: "message", data: MessageResponse }` or `{ type: "recommendation", data: RecommendationDetailResponse }`.

**Rationale**: The backend engineer analysis job (POST /engineer) saves a Recommendation to the DB but does NOT save any assistant message. The chat job (POST /messages) saves messages but does NOT produce recommendations. These are completely independent entities — there is no message_id on recommendations and no recommendation_id on messages. The original timestamp-proximity approach was based on a false assumption that both entities are produced together. The merge-sorted feed is simpler, more correct, and requires no fuzzy matching.

**Implementation approach**:
1. Fetch messages (GET /messages) and recommendation summaries (GET /recommendations) in parallel.
2. For each recommendation summary, also fetch the recommendation detail (GET /recommendations/{recId}) to get setup_changes and driver_feedback.
3. Merge all items into a single array sorted by created_at.
4. Render each item based on its type: message items render as UserMessage or AssistantMessage bubbles; recommendation items render as RecommendationCard + DriverFeedbackCard.

**Alternatives considered**:
- Timestamp proximity matching: Rejected — the engineer job produces no message, so there is no message to attach the recommendation to.
- Separate recommendations panel alongside chat: Rejected per user requirement (recommendation cards should appear inline in the conversation timeline).

## R3: Job Flow — Engineer Analysis vs Chat

**Decision**: Two distinct job types use the same `useJobProgress` hook and `jobWSManager`:
- **Engineer analysis**: POST `/sessions/{id}/engineer` returns `{ job_id, session_id }`. Progress streams via WS. On completion, refetch messages + recommendations.
- **Chat message**: POST `/sessions/{id}/messages` with `{ content }` returns `{ job_id, message_id }`. The user message is saved immediately by the backend. Progress streams via WS. On completion, refetch messages.

**Rationale**: Both job types follow the same pattern established in Phase 7.3. The `jobWSManager` singleton handles WebSocket lifecycle. The `useJobProgress` hook provides reactive progress state.

## R4: Apply Recommendation Flow

**Decision**: Apply flow uses a Modal confirmation dialog:
1. Driver clicks "Apply" on a recommendation card.
2. Modal opens showing a summary table of all changes (section, parameter, old value, new value).
3. The `setup_path` is taken from the session's active setup or the session record's associated setup path.
4. Driver confirms -> POST `/sessions/{id}/recommendations/{recId}/apply` with `{ setup_path }`.
5. On success, update recommendation status locally to "applied", show success notification.
6. On error, show error notification, recommendation stays "proposed".

**Rationale**: The backend `apply_recommendation` endpoint handles validation, backup creation, and atomic file writes. The frontend only needs to confirm the intent and pass the setup path.

**Alternatives considered**:
- Inline confirmation (expand card to show details): Rejected because the Modal component already exists and provides a cleaner UX for destructive actions.

## R5: State Management Layers

**Decision**: Follow existing Phase 7.1-7.5 patterns exactly:
- **TanStack Query**: Messages list, recommendations list, recommendation detail (server state).
- **Zustand**: Active job ID tracking (engineerJobId, chatJobId) in a local store or component state. Session selection from sessionStore.
- **React useState**: Input text, modal open/close, scroll position.

**Rationale**: Constitution Principle XII mandates these three layers and forbids mixing them.

## R6: Conversation Persistence

**Decision**: Conversation persistence is handled entirely by the backend (SQLite messages table). The frontend simply fetches messages on view mount with TanStack Query. No localStorage or sessionStorage (forbidden by constitution).

**Rationale**: Messages are already persisted by the backend on every POST. The GET /messages endpoint returns the full history in chronological order. TanStack Query caching provides in-memory persistence during the session.

## R7: Auto-Scroll Behavior

**Decision**: Use a `useRef` on the conversation container and scroll to bottom on:
- Initial message load completes
- New message added (user or assistant)
- Job completes (new content rendered)

Exception: If the user has manually scrolled up (reading history), do NOT auto-scroll. Track scroll position to detect this.

**Rationale**: Standard chat UX pattern. Prevents disorienting scroll jumps when the user is reading earlier messages.

## R8: Re-Analysis Warning

**Decision**: When the driver triggers a full analysis on a session that already has messages (conversation exists), show a confirmation Modal warning that existing conversation context may be replaced by new analysis results. The backend does not clear messages on re-analysis, so the old conversation is preserved, but the new analysis response appends as additional messages.

**Rationale**: FR-019 requires a warning before re-analysis. Since the backend appends rather than replaces, this is informational rather than destructive.

## R9: Typing Indicator Design

**Decision**: A lightweight animated indicator (three pulsing dots) rendered as a pseudo-message bubble at the bottom of the conversation thread when a chat job is running. It appears in the assistant's column and disappears when the job completes.

**Rationale**: Standard chat UX convention. The indicator is purely visual — it's driven by the job progress state (status === "running" for a chat job).

## R10: Setup Path Resolution

**Decision**: The `setup_path` needed for applying recommendations is resolved from the session's metadata. The backend session record contains enough context to derive the setup file path. If the session has an `active_setup_filename` in its analyzed data, the frontend constructs the path from `config.setups_path` + car folder + filename. If the path cannot be resolved, the Apply button is disabled with a tooltip explaining the issue.

**Rationale**: The backend `apply` endpoint requires a `setup_path` parameter. The frontend must provide this; it doesn't have direct file system access.

**Implementation**: Fetch the recommendation detail (which includes the setup file context from the cached EngineerResponse) or use the session's setup information from the analysis cache.
