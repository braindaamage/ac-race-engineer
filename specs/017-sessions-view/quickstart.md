# Quickstart: Sessions List & Processing View

**Feature**: 017-sessions-view | **Date**: 2026-03-06

## Prerequisites

- Node.js 20 LTS+ and npm
- Python 3.11+ in conda env `ac-race-engineer`

## Setup

No new dependencies needed. All packages are already installed from Phase 7.1/7.2.

### Backend (for integration testing)

```bash
conda activate ac-race-engineer
cd backend
python -m api.server --port 57832
```

### Frontend dev

```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

## Testing

### Frontend tests

```bash
cd frontend
npm run test
# TypeScript check:
npx tsc --noEmit
```

### Backend tests (no changes expected, verify no regressions)

```bash
conda activate ac-race-engineer
pytest backend/tests/ -v
```

## Key Files to Edit

### Frontend (all changes)
- `frontend/src/lib/api.ts` — Add `apiDelete` function
- `frontend/src/lib/types.ts` — NEW: shared TypeScript types for session API responses
- `frontend/src/views/sessions/index.tsx` — REPLACE: full sessions list view
- `frontend/src/views/sessions/SessionCard.tsx` — NEW: individual session card component
- `frontend/src/views/sessions/SessionsView.css` — NEW: sessions view styles
- `frontend/src/hooks/useSessions.ts` — NEW: TanStack Query hook for session list
- `frontend/src/components/layout/AppShell.tsx` — MODIFY: add selected session strip
- `frontend/src/components/layout/AppShell.css` — MODIFY: add strip styles

### Tests
- `frontend/tests/views/SessionsView.test.tsx` — NEW: sessions view tests
- `frontend/tests/views/SessionCard.test.tsx` — NEW: session card tests
- `frontend/tests/hooks/useSessions.test.tsx` — NEW: sessions hook tests

## API Endpoints Reference (all existing from Phase 6)

| Method | Path | Purpose |
|--------|------|---------|
| GET | /sessions | List all sessions (optional `?car=` filter) |
| GET | /sessions/{id} | Get single session detail |
| POST | /sessions/sync | Rescan sessions directory |
| DELETE | /sessions/{id} | Delete a session record (not files) |
| POST | /sessions/{id}/process | Start processing (parse + analyze), returns job_id |
| WS | /ws/jobs/{job_id} | Real-time job progress updates |
