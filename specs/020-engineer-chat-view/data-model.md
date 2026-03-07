# Data Model: Engineer Chat View

**Branch**: `020-engineer-chat-view` | **Date**: 2026-03-06

## Frontend TypeScript Types

All types below are new additions to `frontend/src/lib/types.ts`. They mirror the backend API response shapes from `backend/api/engineer/serializers.py`.

### Message Types

```typescript
/** A single message in the engineer conversation. */
interface MessageResponse {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string; // ISO 8601
}

/** Response from GET /sessions/{id}/messages */
interface MessageListResponse {
  session_id: string;
  messages: MessageResponse[];
}

/** Request body for POST /sessions/{id}/messages */
interface ChatRequest {
  content: string;
}

/** Response from POST /sessions/{id}/messages */
interface ChatJobResponse {
  job_id: string;
  message_id: string;
}
```

### Recommendation Types

```typescript
/** Summary item in the recommendations list. */
interface RecommendationSummary {
  recommendation_id: string;
  session_id: string;
  status: "proposed" | "applied" | "rejected";
  summary: string;
  change_count: number;
  created_at: string; // ISO 8601
}

/** Response from GET /sessions/{id}/recommendations */
interface RecommendationListResponse {
  session_id: string;
  recommendations: RecommendationSummary[];
}

/** A single setup parameter change within a recommendation. */
interface SetupChangeDetail {
  section: string;
  parameter: string;
  old_value: string;
  new_value: string;
  reasoning: string;
  expected_effect: string;
  confidence: "high" | "medium" | "low";
}

/** A driving technique observation from the engineer. */
interface DriverFeedbackDetail {
  area: string;
  observation: string;
  suggestion: string;
  corners_affected: number[];
  severity: "high" | "medium" | "low";
}

/** Full recommendation detail with changes and feedback. */
interface RecommendationDetailResponse {
  recommendation_id: string;
  session_id: string;
  status: "proposed" | "applied" | "rejected";
  summary: string;
  explanation: string;
  confidence: "high" | "medium" | "low";
  signals_addressed: string[];
  setup_changes: SetupChangeDetail[];
  driver_feedback: DriverFeedbackDetail[];
  created_at: string; // ISO 8601
}
```

### Engineer Job Types

```typescript
/** Response from POST /sessions/{id}/engineer */
interface EngineerJobResponse {
  job_id: string;
  session_id: string;
}
```

### Apply Recommendation Types

```typescript
/** Request body for POST /sessions/{id}/recommendations/{recId}/apply */
interface ApplyRequest {
  setup_path: string;
}

/** Response from POST /sessions/{id}/recommendations/{recId}/apply */
interface ApplyResponse {
  recommendation_id: string;
  status: "applied";
  backup_path: string;
  changes_applied: number;
}
```

## Entity Relationships

```
Session (1) ──── (*) Message
    │                  role: "user" | "assistant"
    │                  content: text
    │                  created_at: timestamp
    │
    └──── (*) Recommendation
                 status: "proposed" | "applied" | "rejected"
                 summary: text
                 created_at: timestamp
                 │
                 ├── (*) SetupChange
                 │        section, parameter
                 │        old_value, new_value
                 │        reasoning, expected_effect
                 │        confidence
                 │
                 └── (*) DriverFeedback
                          area, observation
                          suggestion, corners_affected
                          severity
```

## State Transitions

### Recommendation Status
```
proposed ──[apply]──> applied
proposed ──[reject]──> rejected  (not in current UI scope)
```

### Session State (relevant to this view)
```
analyzed ──[engineer analysis job]──> engineered
engineered ──[re-analysis]──> engineered (new recommendation added)
```

### Job Lifecycle
```
(created) ──> pending ──> running ──> completed
                                  └──> failed
```

## View State Machine

```
                    ┌─────────────────────────┐
                    │    No Session Selected   │
                    │      (EmptyState)        │
                    └────────────┬────────────┘
                                 │ session selected
                    ┌────────────▼────────────┐
                    │   Session Not Analyzed   │
                    │      (EmptyState)        │
                    └────────────┬────────────┘
                                 │ state = "analyzed" | "engineered"
                    ┌────────────▼────────────┐
              ┌─────│   Ready (has messages?)  │─────┐
              │     └─────────────────────────┘      │
              │ no                                   │ yes
   ┌──────────▼──────────┐            ┌──────────────▼──────────┐
   │  Empty Conversation │            │  Conversation History   │
   │  (start analysis    │            │  (messages + rec cards   │
   │   or ask question)  │            │   + input field)        │
   └──────────┬──────────┘            └──────────────┬──────────┘
              │ trigger analysis / send message       │
              └──────────────┬───────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │    Job Running      │
                  │  (progress bar or   │
                  │   typing indicator) │
                  └──────────┬──────────┘
                             │ job completes
                  ┌──────────▼──────────┐
                  │  Conversation with  │
                  │  New Response       │
                  │  (refetch messages  │
                  │   + recommendations)│
                  └─────────────────────┘
```

## Data Fetching Strategy

| Data | Hook | Query Key | Endpoint | Stale Time | Enabled When |
|------|------|-----------|----------|------------|-------------|
| Messages | `useMessages(sessionId)` | `["messages", sessionId]` | GET /sessions/{id}/messages | 0 (always refetch) | sessionId set + state >= analyzed |
| Recommendations | `useRecommendations(sessionId)` | `["recommendations", sessionId]` | GET /sessions/{id}/recommendations | 0 (always refetch) | sessionId set + state >= analyzed |
| Recommendation Detail | `useRecommendationDetail(sessionId, recId)` | `["recommendation", sessionId, recId]` | GET /sessions/{id}/recommendations/{recId} | Infinity | recId set |

Note: Messages and recommendations use staleTime 0 because they change during the session (new messages added, recommendation status updates). Recommendation detail uses Infinity because once fetched, the detail doesn't change (only status does, which is refetched via the list).
