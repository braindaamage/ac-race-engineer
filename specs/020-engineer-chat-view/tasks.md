# Tasks: Engineer Chat View

**Input**: Design documents from `/specs/020-engineer-chat-view/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contracts.md

**Tests**: Included — the project has established frontend testing patterns (Vitest + React Testing Library) and the plan specifies 7 test files.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend source**: `frontend/src/`
- **Frontend tests**: `frontend/tests/`
- **Views**: `frontend/src/views/engineer/`
- **Hooks**: `frontend/src/hooks/`
- **Types**: `frontend/src/lib/types.ts`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: TypeScript types and data-fetching hooks shared by all user stories

- [x] T001 Add engineer TypeScript types to `frontend/src/lib/types.ts` — add all interfaces from data-model.md: MessageResponse, MessageListResponse, ChatRequest, ChatJobResponse, RecommendationSummary, RecommendationListResponse, SetupChangeDetail, DriverFeedbackDetail, RecommendationDetailResponse, EngineerJobResponse, ApplyRequest, ApplyResponse. Also add the FeedItem discriminated union type: `{ type: "message"; data: MessageResponse } | { type: "recommendation"; data: RecommendationDetailResponse }`. Export all new types.
- [x] T002 [P] Create `useMessages` hook in `frontend/src/hooks/useMessages.ts` — TanStack Query hook that calls `GET /sessions/{sessionId}/messages`, returns `MessageListResponse`. Query key: `["messages", sessionId]`. Enabled when sessionId is set. staleTime: 0. Follow useSessions/useLaps patterns.
- [x] T003 [P] Create `useRecommendations` hook in `frontend/src/hooks/useRecommendations.ts` — TanStack Query hook that calls `GET /sessions/{sessionId}/recommendations`, returns `RecommendationListResponse`. Query key: `["recommendations", sessionId]`. Enabled when sessionId is set. staleTime: 0. Also export a `useRecommendationDetail(sessionId, recId)` hook that calls `GET /sessions/{sessionId}/recommendations/{recId}`, returns `RecommendationDetailResponse`. Query key: `["recommendation", sessionId, recId]`. staleTime: Infinity. Enabled when both sessionId and recId are set.
- [x] T004 [P] Create `useMessages` hook test in `frontend/tests/hooks/useMessages.test.tsx` — test: returns undefined when no sessionId, fetches messages when sessionId set, returns MessageListResponse shape. Mock apiGet. Use QueryClientProvider wrapper.
- [x] T005 [P] Create `useRecommendations` hook test in `frontend/tests/hooks/useRecommendations.test.tsx` — test both useRecommendations and useRecommendationDetail: returns undefined when no id, fetches list when sessionId set, fetches detail when recId set. Mock apiGet. Use QueryClientProvider wrapper.

**Checkpoint**: Types and data hooks ready — all user stories can consume messages and recommendations from the API.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Base view shell, CSS, and leaf components reused across multiple user stories

**CRITICAL**: These components are shared building blocks. All user story phases depend on them.

- [x] T006 Create view CSS file `frontend/src/views/engineer/EngineerView.css` — define all CSS classes from ui-contracts.md: `.ace-engineer-view`, `.ace-engineer-header`, `.ace-message-list`, `.ace-message`, `.ace-message--user`, `.ace-message--assistant`, `.ace-message__content`, `.ace-message__timestamp`, `.ace-recommendation-card`, `.ace-recommendation-card--proposed`, `.ace-recommendation-card--applied`, `.ace-setup-change`, `.ace-setup-change__param`, `.ace-setup-change__values`, `.ace-setup-change__reasoning`, `.ace-driver-feedback`, `.ace-typing-indicator`, `.ace-analysis-progress`, `.ace-chat-input`, `.ace-chat-input__textarea`, `.ace-chat-input__send`, `.ace-apply-modal`, `.ace-apply-modal__table`. All colors via design tokens from `tokens.css`. JetBrains Mono for numeric data (setup values, lap times). No hardcoded hex values.
- [x] T007 [P] Create `UserMessage` component in `frontend/src/views/engineer/UserMessage.tsx` — renders a user message bubble (right-aligned). Props: `{ content: string; timestamp: string }`. Uses `.ace-message .ace-message--user` classes. Shows formatted timestamp. Content rendered as plain text.
- [x] T008 [P] Create `AssistantMessage` component in `frontend/src/views/engineer/AssistantMessage.tsx` — renders an assistant message bubble (left-aligned). Props: `{ content: string; timestamp: string }`. Uses `.ace-message .ace-message--assistant` classes. Shows formatted timestamp. Content rendered as plain text.
- [x] T009 [P] Create `RecommendationCard` component in `frontend/src/views/engineer/RecommendationCard.tsx` — renders a structured recommendation card using Card (variant="ai") from design system. Props: `{ recommendation: RecommendationDetailResponse; onApply: (recId: string) => void }`. Shows: summary text, confidence Badge, status Badge ("Proposed"/"Applied"), list of SetupChangeDetail rows (each showing section, parameter, old_value -> new_value in JetBrains Mono, reasoning, expected_effect, confidence Badge), list of DriverFeedbackDetail items. "Apply" Button (primary variant) calls onApply — disabled when status is "applied". Uses `.ace-recommendation-card`, `.ace-setup-change`, `.ace-setup-change__param`, `.ace-setup-change__values`, `.ace-setup-change__reasoning` classes.
- [x] T010 [P] Create `DriverFeedbackCard` component in `frontend/src/views/engineer/DriverFeedbackCard.tsx` — renders a driving technique observation. Props: `{ feedback: DriverFeedbackDetail }`. Shows: area with severity Badge, observation text, suggestion text, affected corners list (formatted as "Turn X, Turn Y"). Uses `.ace-driver-feedback` class.
- [x] T011 [P] Create `ChatInput` component in `frontend/src/views/engineer/ChatInput.tsx` — renders a textarea + send Button. Props: `{ onSend: (content: string) => void; disabled: boolean; placeholder?: string }`. Enter key submits (Shift+Enter for newline). Send button uses Button component (primary variant). Input and button disabled when `disabled` prop is true. Clears input after send. Uses `.ace-chat-input`, `.ace-chat-input__textarea`, `.ace-chat-input__send` classes.
- [x] T012 [P] Create `TypingIndicator` component in `frontend/src/views/engineer/TypingIndicator.tsx` — renders three animated pulsing dots as a pseudo assistant message bubble. No props. Uses `.ace-typing-indicator` class. CSS animation for the dots.
- [x] T013 [P] Create `AnalysisProgress` component in `frontend/src/views/engineer/AnalysisProgress.tsx` — renders ProgressBar component + step description label. Props: `{ progress: number; currentStep: string | null }`. Uses `.ace-analysis-progress` class and the ProgressBar design system component.
- [x] T014 [P] Create `RecommendationCard` test in `frontend/tests/views/engineer/RecommendationCard.test.tsx` — test: renders summary, setup changes with all fields (section, parameter, old_value, new_value, reasoning, expected_effect, confidence), driver feedback items, Apply button enabled for "proposed" status, Apply button disabled for "applied" status, Apply button calls onApply with recommendation_id, status badge shows correct variant for proposed/applied.
- [x] T015 [P] Create `ChatInput` test in `frontend/tests/views/engineer/ChatInput.test.tsx` — test: renders textarea and send button, calls onSend with input text on button click, calls onSend on Enter key press, does not call onSend on Shift+Enter, clears input after send, send button disabled when disabled prop is true, textarea disabled when disabled prop is true, does not call onSend when input is empty.

**Checkpoint**: All leaf components and CSS ready. User story implementation can begin.

---

## Phase 3: User Story 1 — Trigger Full Session Analysis (Priority: P1) MVP

**Goal**: Driver selects an analyzed session, opens Engineer view, triggers full AI analysis, and sees structured recommendation cards + driving technique feedback in the conversation feed.

**Independent Test**: Select an analyzed session, click "Analyze Session", verify progress indicator appears, then recommendation cards and technique feedback render after completion.

### Tests for User Story 1

- [x] T016 [P] [US1] Create `EngineerView` test in `frontend/tests/views/engineer/EngineerView.test.tsx` — test US1 scenarios: shows "Select a session" empty state when no session selected, shows "Analysis required" empty state when session state is not analyzed/engineered, shows empty conversation with "Analyze Session" button when session is analyzed and no messages/recommendations exist, clicking "Analyze Session" calls POST /sessions/{id}/engineer, shows AnalysisProgress when engineer job is running, renders recommendation cards in the feed after analysis completes, renders driver feedback cards in the feed after analysis completes, shows error message when engineer job fails with retry option. Mock apiGet/apiPost, mock useSessionStore, mock useSessions, mock useJobProgress, mock jobWSManager. Use QueryClientProvider wrapper.
- [x] T017 [P] [US1] Create `MessageList` test in `frontend/tests/views/engineer/MessageList.test.tsx` — test: renders empty state message when no feed items, renders user messages as UserMessage bubbles, renders assistant messages as AssistantMessage bubbles, renders recommendation items as RecommendationCard, merge-sorts messages and recommendations by created_at, shows AnalysisProgress when activeJobType is "engineer", does not show TypingIndicator when activeJobType is "engineer".

### Implementation for User Story 1

- [x] T018 [US1] Create `MessageList` component in `frontend/src/views/engineer/MessageList.tsx` — implements the merge-sorted conversation feed per research.md R2. Props: `{ messages: MessageResponse[]; recommendations: RecommendationDetailResponse[]; activeJobType: "engineer" | "chat" | null; jobProgress: JobProgress | undefined; onApply: (recId: string) => void }`. Merges messages and recommendations into FeedItem[] sorted by created_at ascending. Renders each item by type: "message" items as UserMessage or AssistantMessage (based on role), "recommendation" items as RecommendationCard (with driver feedback rendered via DriverFeedbackCard for each feedback item). Shows AnalysisProgress at the bottom when activeJobType is "engineer". Shows TypingIndicator at the bottom when activeJobType is "chat". Implements auto-scroll via useRef: scroll to bottom on initial load, new items, and job completion. Suppress auto-scroll if user has scrolled up (detect via scroll position). Uses `.ace-message-list` class.
- [x] T019 [US1] Replace `EngineerView` placeholder in `frontend/src/views/engineer/index.tsx` — full implementation of the main view. Reads selectedSessionId from useSessionStore. Reads sessions from useSessions. Validates session state is "analyzed" or "engineered" — shows EmptyState with appropriate message if not. Fetches messages via useMessages(sessionId) and recommendations via useRecommendations(sessionId). For each recommendation summary, fetches detail via useRecommendationDetail. Manages engineer job: state variable for engineerJobId, tracks via useJobProgress. "Analyze Session" button in header (ConversationHeader area): onClick calls `apiPost<EngineerJobResponse>(/sessions/{id}/engineer)`, stores job_id, tracks progress. On job completion (status === "completed"), calls refetch on messages and recommendations queries. On job failure, shows error notification + inline error message with retry. Renders MessageList with merged data and job state. Renders ChatInput (disabled when any job running). Imports EngineerView.css. Shows empty conversation prompt with "Analyze Session" button when no messages and no recommendations.

**Checkpoint**: US1 complete — driver can trigger analysis and see structured results in the conversation feed.

---

## Phase 4: User Story 2 — Ask Follow-Up Questions (Priority: P2)

**Goal**: Driver can type free-form questions in the chat input, send them, see their message appear as a user bubble, see a typing indicator while the engineer responds, and see the assistant response when it arrives.

**Independent Test**: Open Engineer view for an analyzed session, type a question, submit, verify user bubble appears, typing indicator shows, then assistant response appears.

### Implementation for User Story 2

- [x] T020 [US2] Add chat message submission to `frontend/src/views/engineer/index.tsx` — add handleSendMessage callback: calls `apiPost<ChatJobResponse>(/sessions/{id}/messages, { content })`, stores job_id as chatJobId state, tracks via useJobProgress. On job completion, refetch messages query. Pass handleSendMessage to ChatInput onSend prop. Pass activeJobType ("engineer" | "chat" | null) to MessageList based on which job is active. Disable ChatInput when either job is running (engineerJobId or chatJobId has running status). Clear chatJobId on job completion.
- [x] T021 [US2] Update `EngineerView` test in `frontend/tests/views/engineer/EngineerView.test.tsx` — add US2 test cases: typing a message and clicking send calls POST /sessions/{id}/messages with content, user message appears in conversation immediately (optimistic or after refetch), typing indicator visible while chat job runs, assistant response appears after chat job completes, input disabled while chat job is running, error message shown when chat job fails with input re-enabled.

**Checkpoint**: US1 + US2 complete — full analysis and follow-up chat both work.

---

## Phase 5: User Story 3 — Apply Setup Recommendations (Priority: P2)

**Goal**: Driver can click "Apply" on a recommendation card, see a confirmation modal with change details, confirm to apply changes to the .ini file, and see the card update to "Applied" status.

**Independent Test**: With a recommendation card visible, click Apply, verify modal shows changes table, confirm, verify card shows "Applied" badge and button is disabled.

### Tests for User Story 3

- [x] T022 [P] [US3] Create `ApplyConfirmModal` test in `frontend/tests/views/engineer/ApplyConfirmModal.test.tsx` — test: renders nothing when open is false, renders modal with title when open is true, shows table of setup changes (section, parameter, old_value, new_value) from recommendation, shows confirm and cancel buttons, calls onConfirm when confirm clicked, calls onClose when cancel clicked, shows loading state on confirm button when isApplying is true, confirm button disabled when isApplying is true.

### Implementation for User Story 3

- [x] T023 [US3] Create `ApplyConfirmModal` component in `frontend/src/views/engineer/ApplyConfirmModal.tsx` — renders Modal component (from design system) with a changes summary table. Props: `{ open: boolean; onClose: () => void; onConfirm: () => void; recommendation: RecommendationDetailResponse | null; isApplying: boolean }`. Table shows each SetupChangeDetail: section, parameter, old_value, new_value (values in JetBrains Mono). Confirm button ("Apply Changes") uses Button primary variant, disabled and shows loading text when isApplying. Cancel button uses Button secondary variant. Uses `.ace-apply-modal`, `.ace-apply-modal__table` classes.
- [x] T024 [US3] Add apply recommendation flow to `frontend/src/views/engineer/index.tsx` — add state: applyingRecId (string | null), showApplyModal (boolean), isApplying (boolean). handleApply callback: sets applyingRecId and opens modal. handleConfirmApply callback: calls `apiPost<ApplyResponse>(/sessions/{id}/recommendations/{recId}/apply, { setup_path })` where setup_path is resolved from session/config context (per research.md R10). On success: show success notification via notificationStore, refetch recommendations to get updated status, close modal. On error: show error notification, close modal, recommendation stays "proposed". Render ApplyConfirmModal with state. Pass handleApply as onApply to MessageList which passes to RecommendationCard.
- [x] T025 [US3] Update `EngineerView` test in `frontend/tests/views/engineer/EngineerView.test.tsx` — add US3 test cases: clicking Apply on recommendation card opens ApplyConfirmModal, modal shows changes from the recommendation, confirming calls POST apply endpoint, card updates to "Applied" after successful apply, modal closes after apply completes, error notification shown when apply fails.

**Checkpoint**: US1 + US2 + US3 complete — analysis, chat, and apply all work.

---

## Phase 6: User Story 4 — Persistent Conversation History (Priority: P3)

**Goal**: Conversation history (messages + recommendations) persists across view navigation. When the driver leaves and returns to the Engineer view, the full conversation is restored from the API.

**Independent Test**: Have a conversation, switch to another view, return to Engineer view, verify all messages and recommendation cards are present with correct statuses.

### Implementation for User Story 4

- [x] T026 [US4] Verify and refine conversation persistence in `frontend/src/views/engineer/index.tsx` — ensure that on view mount, useMessages and useRecommendations refetch from the API (staleTime: 0 ensures this). Verify that recommendation detail queries with staleTime: Infinity serve cached data correctly. Verify that when selectedSessionId changes, old data is cleared and new session's data loads. Ensure applied recommendation cards show "Applied" badge on reload. Add TanStack Query `refetchOnMount: true` to messages and recommendations hooks if not already set.
- [x] T027 [US4] Update `EngineerView` test in `frontend/tests/views/engineer/EngineerView.test.tsx` — add US4 test cases: on mount with existing messages, renders full conversation history, on mount with applied recommendations, cards show "Applied" status and disabled Apply button, switching session clears previous conversation and loads new one.

**Checkpoint**: US1-US4 complete — conversation persists across navigation.

---

## Phase 7: User Story 5 — Progress and Status Indicators (Priority: P3)

**Goal**: Clear visual feedback during all async operations — progress bar for analysis jobs, typing indicator for chat jobs, disabled input while processing, error states.

**Independent Test**: Trigger analysis, verify progress bar shows with step descriptions. Send a chat message, verify typing indicator appears. Verify input disabled during both.

### Implementation for User Story 5

- [x] T028 [US5] Refine progress indicators in `frontend/src/views/engineer/index.tsx` — ensure activeJobType is correctly set: "engineer" when engineerJobId is active, "chat" when chatJobId is active, null when idle. Pass jobProgress from useJobProgress to MessageList. Verify AnalysisProgress renders correct step text and percentage from jobProgress.currentStep and jobProgress.progress. Verify TypingIndicator renders during chat jobs. Verify both disappear within 1 rendering cycle of job completing. Verify ChatInput disabled prop is true whenever any job is running.
- [x] T029 [US5] Add re-analysis warning per FR-019 in `frontend/src/views/engineer/index.tsx` — when driver clicks "Analyze Session" and conversation already has messages or recommendations, show a confirmation Modal warning before proceeding. Use Modal component with confirm/cancel. Only trigger the engineer job after confirmation. Skip warning if conversation is empty.
- [x] T030 [US5] Update `EngineerView` test in `frontend/tests/views/engineer/EngineerView.test.tsx` — add US5 test cases: AnalysisProgress shows step description and percentage during engineer job, TypingIndicator shows during chat job, both indicators disappear when job completes, ChatInput disabled during engineer job, ChatInput disabled during chat job, re-analysis warning modal appears when conversation exists, re-analysis proceeds after confirmation, re-analysis cancelled does not start job.

**Checkpoint**: All 5 user stories complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final quality, TypeScript strictness, edge cases, and full test suite validation

- [x] T031 Run TypeScript strict check: `cd frontend && npx tsc --noEmit` — fix any type errors in all new and modified files. No explicit `any` without justification comment.
- [x] T032 Run full frontend test suite: `cd frontend && npm run test` — verify all existing 271 tests still pass plus all new tests. Fix any regressions.
- [x] T033 Handle edge cases in `frontend/src/views/engineer/index.tsx`: session not analyzed (EmptyState directing to process session), apply fails because setup file missing (error notification with explanation), long conversation scroll behavior (verify auto-scroll suppression when user scrolled up works correctly).
- [x] T034 Verify design system compliance: all colors from design tokens (no hardcoded hex), JetBrains Mono on numeric data in RecommendationCard (setup values), `ace-` prefix on all CSS classes, Button/Card/Badge/Modal/ProgressBar/EmptyState components reused (no inline duplicates).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — types and hooks first
- **Phase 2 (Foundational)**: Depends on T001 (types). T006 (CSS) has no code dependency but is needed for visual correctness. Leaf components (T007-T013) depend on types from T001.
- **Phase 3 (US1)**: Depends on Phase 1 (hooks) + Phase 2 (components). This is the MVP.
- **Phase 4 (US2)**: Depends on Phase 3 (US1 provides the view shell, MessageList, ChatInput)
- **Phase 5 (US3)**: Depends on Phase 3 (US1 provides RecommendationCard and view). Can run in parallel with Phase 4.
- **Phase 6 (US4)**: Depends on Phase 3 (data fetching in place). Mostly verification, low effort.
- **Phase 7 (US5)**: Depends on Phase 3 + 4 (progress indicators for both job types). US5 refines indicators already partially built in US1/US2.
- **Phase 8 (Polish)**: Depends on all previous phases.

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories. MVP.
- **US2 (P2)**: Builds on US1's view shell and MessageList but adds chat-specific logic.
- **US3 (P2)**: Builds on US1's RecommendationCard. Can proceed in parallel with US2.
- **US4 (P3)**: Verification layer on top of US1. Low effort.
- **US5 (P3)**: Refinement layer on top of US1 + US2. Adds re-analysis warning (FR-019).

### Within Each Phase

- Tests (T016, T017) can run in parallel with each other
- Leaf components (T007-T013) can all run in parallel
- Hook files (T002, T003) can run in parallel
- Hook tests (T004, T005) can run in parallel
- MessageList (T018) must come before EngineerView (T019)

### Parallel Opportunities

**Phase 1 parallel batch:**
```
T002 (useMessages hook) | T003 (useRecommendations hook) | T004 (useMessages test) | T005 (useRecommendations test)
```

**Phase 2 parallel batch:**
```
T006 (CSS) | T007 (UserMessage) | T008 (AssistantMessage) | T009 (RecommendationCard) | T010 (DriverFeedbackCard) | T011 (ChatInput) | T012 (TypingIndicator) | T013 (AnalysisProgress) | T014 (RecommendationCard test) | T015 (ChatInput test)
```

**Phase 3 parallel batch (tests):**
```
T016 (EngineerView test) | T017 (MessageList test)
```

**Phase 4 + 5 parallel:**
```
US2 (T020-T021) can run in parallel with US3 (T022-T025)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Types + hooks (T001-T005)
2. Complete Phase 2: CSS + leaf components (T006-T015)
3. Complete Phase 3: US1 — trigger analysis + render results (T016-T019)
4. **STOP and VALIDATE**: `cd frontend && npm run test && npx tsc --noEmit`
5. MVP delivers: full session analysis with recommendation cards and technique feedback

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 (US1) → MVP — analysis + recommendation cards
3. Phase 4 (US2) → Chat — follow-up questions
4. Phase 5 (US3) → Apply — one-click setup changes
5. Phase 6 (US4) → Persistence — conversation survives navigation
6. Phase 7 (US5) → Polish — progress refinement + re-analysis warning
7. Phase 8 → Final validation

Each phase adds value without breaking previous work.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All backend endpoints already exist (Phase 6) — this is frontend-only work
- No new npm dependencies needed — uses existing React, TanStack Query, Zustand
- CSS uses `ace-` prefix, design tokens only, JetBrains Mono for numbers
- Total new files: ~13 source + ~7 test = ~20 files
- Existing 271 frontend tests must not regress
