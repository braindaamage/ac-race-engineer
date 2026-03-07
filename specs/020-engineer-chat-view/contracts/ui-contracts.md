# UI Contracts: Engineer Chat View

**Branch**: `020-engineer-chat-view` | **Date**: 2026-03-06

## Component Hierarchy

```
EngineerView
├── EmptyState (no session / not analyzed)
├── ConversationHeader
│   ├── Session info (car, track)
│   └── "Analyze Session" button (when no recommendations exist yet)
├── MessageList
│   ├── UserMessage (role="user")
│   ├── AssistantMessage (role="assistant")
│   │   ├── Message text content
│   │   ├── RecommendationCard[] (if analysis response)
│   │   │   ├── SetupChangeRow[] (section, param, old, new, reasoning)
│   │   │   ├── Badge (confidence)
│   │   │   ├── Badge (status: proposed/applied)
│   │   │   └── Button ("Apply" / disabled if applied)
│   │   └── DriverFeedbackCard[] (if analysis response)
│   │       ├── Area + severity Badge
│   │       ├── Observation text
│   │       ├── Suggestion text
│   │       └── Affected corners list
│   ├── AnalysisProgress (during engineer job)
│   │   ├── ProgressBar (value + step description)
│   │   └── Step label
│   └── TypingIndicator (during chat job)
├── ChatInput
│   ├── Text input (textarea)
│   ├── Send button
│   └── Disabled overlay (when job running)
└── ApplyConfirmModal
    ├── Changes summary table
    ├── Setup file path
    ├── Confirm button
    └── Cancel button
```

## Component Props Contracts

### EngineerView
- No props (top-level view, reads from stores and hooks)
- Reads: `useSessionStore(s => s.selectedSessionId)`, `useSessions()`, `useMessages()`, `useRecommendations()`

### MessageList
```typescript
interface MessageListProps {
  messages: MessageResponse[];
  recommendations: RecommendationDetailResponse[];
  activeJobType: "engineer" | "chat" | null;
  jobProgress: JobProgress | undefined;
  onApply: (recommendationId: string) => void;
}
```

### UserMessage
```typescript
interface UserMessageProps {
  content: string;
  timestamp: string; // ISO 8601
}
```

### AssistantMessage
```typescript
interface AssistantMessageProps {
  content: string;
  timestamp: string;
  recommendation?: RecommendationDetailResponse;
  onApply?: (recommendationId: string) => void;
}
```

### RecommendationCard
```typescript
interface RecommendationCardProps {
  recommendation: RecommendationDetailResponse;
  onApply: (recommendationId: string) => void;
}
```

### SetupChangeRow
```typescript
interface SetupChangeRowProps {
  change: SetupChangeDetail;
}
```

### DriverFeedbackCard
```typescript
interface DriverFeedbackCardProps {
  feedback: DriverFeedbackDetail;
}
```

### AnalysisProgress
```typescript
interface AnalysisProgressProps {
  progress: number;       // 0-100
  currentStep: string | null;
}
```

### TypingIndicator
- No props (purely visual component)

### ChatInput
```typescript
interface ChatInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
  placeholder?: string;
}
```

### ApplyConfirmModal
```typescript
interface ApplyConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  recommendation: RecommendationDetailResponse | null;
  isApplying: boolean;
}
```

## Custom Hooks

### useMessages
```typescript
function useMessages(sessionId: string | null): {
  data: MessageListResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<QueryObserverResult>;
}
```

### useRecommendations
```typescript
function useRecommendations(sessionId: string | null): {
  data: RecommendationListResponse | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<QueryObserverResult>;
}
```

### useRecommendationDetail
```typescript
function useRecommendationDetail(
  sessionId: string | null,
  recommendationId: string | null,
): {
  data: RecommendationDetailResponse | undefined;
  isLoading: boolean;
  error: Error | null;
}
```

## Interaction Flows

### Flow 1: Trigger Full Analysis
```
User clicks "Analyze Session" button
  → POST /sessions/{id}/engineer
  → Receive { job_id, session_id }
  → Set activeJobType = "engineer", track job_id
  → AnalysisProgress renders with ProgressBar
  → Job completes (WS event)
  → Refetch messages + recommendations
  → AssistantMessage renders with RecommendationCard(s)
  → Clear activeJobType
```

### Flow 2: Send Chat Message
```
User types in ChatInput, clicks Send
  → POST /sessions/{id}/messages { content }
  → Receive { job_id, message_id }
  → Optimistic: add user message to list
  → Set activeJobType = "chat", track job_id
  → TypingIndicator renders
  → Job completes (WS event)
  → Refetch messages
  → New AssistantMessage renders
  → Clear activeJobType
```

### Flow 3: Apply Recommendation
```
User clicks "Apply" on RecommendationCard
  → ApplyConfirmModal opens with changes table
  → User clicks Confirm
  → POST /sessions/{id}/recommendations/{recId}/apply { setup_path }
  → On success: update recommendation status to "applied"
  → Show success notification
  → RecommendationCard re-renders with "Applied" badge, disabled button
  → Modal closes
```

## CSS Classes (ace- prefix)

```
.ace-engineer-view          — Main view container
.ace-engineer-header        — Header bar with session info + analyze button
.ace-message-list           — Scrollable conversation container
.ace-message                — Base message bubble
.ace-message--user          — User message variant (right-aligned)
.ace-message--assistant     — Assistant message variant (left-aligned)
.ace-message__content       — Message text
.ace-message__timestamp     — Timestamp label
.ace-recommendation-card    — Recommendation card container
.ace-recommendation-card--proposed  — Proposed status
.ace-recommendation-card--applied   — Applied status
.ace-setup-change           — Single setup change row
.ace-setup-change__param    — Parameter name cell
.ace-setup-change__values   — Old → New values cell
.ace-setup-change__reasoning — Reasoning text
.ace-driver-feedback        — Driver feedback card
.ace-typing-indicator       — Animated dots container
.ace-analysis-progress      — Progress bar wrapper during analysis
.ace-chat-input             — Input area container
.ace-chat-input__textarea   — Text input field
.ace-chat-input__send       — Send button
.ace-apply-modal            — Apply confirmation modal content
.ace-apply-modal__table     — Changes summary table
```
