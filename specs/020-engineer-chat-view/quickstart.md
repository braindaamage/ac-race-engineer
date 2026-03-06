# Quickstart: Engineer Chat View

**Branch**: `020-engineer-chat-view` | **Date**: 2026-03-06

## Prerequisites

- Node.js 20 LTS
- npm (from frontend/package.json lock file)
- Backend running at http://127.0.0.1:57832 (for manual testing)

## Development

```bash
# Frontend dev server
cd frontend
npm run dev

# Run tests
cd frontend
npm run test

# Type check
cd frontend
npx tsc --noEmit
```

## Key Files to Create/Modify

### New Files
```
frontend/src/views/engineer/index.tsx          — Main view (replace placeholder)
frontend/src/views/engineer/EngineerView.css   — View styles
frontend/src/views/engineer/MessageList.tsx     — Conversation thread
frontend/src/views/engineer/UserMessage.tsx     — User message bubble
frontend/src/views/engineer/AssistantMessage.tsx — Assistant message bubble
frontend/src/views/engineer/RecommendationCard.tsx — Setup changes card
frontend/src/views/engineer/DriverFeedbackCard.tsx — Technique feedback card
frontend/src/views/engineer/ChatInput.tsx       — Message input
frontend/src/views/engineer/TypingIndicator.tsx — Animated typing dots
frontend/src/views/engineer/AnalysisProgress.tsx — Progress bar during analysis
frontend/src/views/engineer/ApplyConfirmModal.tsx — Apply confirmation dialog
frontend/src/hooks/useMessages.ts               — Messages TanStack Query hook
frontend/src/hooks/useRecommendations.ts        — Recommendations TanStack Query hook
frontend/tests/views/engineer/EngineerView.test.tsx
frontend/tests/views/engineer/MessageList.test.tsx
frontend/tests/views/engineer/RecommendationCard.test.tsx
frontend/tests/views/engineer/ChatInput.test.tsx
frontend/tests/views/engineer/ApplyConfirmModal.test.tsx
frontend/tests/hooks/useMessages.test.tsx
frontend/tests/hooks/useRecommendations.test.tsx
```

### Modified Files
```
frontend/src/lib/types.ts                      — Add engineer TypeScript types
```

## Backend Endpoints Used (all existing, Phase 6)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /sessions/{id}/engineer | Start full analysis job |
| GET | /sessions/{id}/recommendations | List recommendations |
| GET | /sessions/{id}/recommendations/{recId} | Get recommendation detail |
| POST | /sessions/{id}/recommendations/{recId}/apply | Apply recommendation |
| GET | /sessions/{id}/messages | Get conversation history |
| POST | /sessions/{id}/messages | Send chat message |

## Testing

```bash
# Run only engineer view tests
cd frontend
npx vitest run tests/views/engineer/

# Run only hook tests
cd frontend
npx vitest run tests/hooks/useMessages.test.tsx tests/hooks/useRecommendations.test.tsx

# Full frontend test suite
cd frontend
npm run test
```
