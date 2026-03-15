# Quickstart: Session Views Visual Polish

**Branch**: `037-session-views-visual-polish` | **Date**: 2026-03-15

## Prerequisites

- Node.js 20 LTS
- npm (from frontend/package-lock.json)
- Python 3.11+ in conda env `ac-race-engineer` (only needed to run backend for manual visual testing)

## Setup

```bash
# Switch to feature branch
git checkout 037-session-views-visual-polish

# Install frontend dependencies
cd frontend && npm install

# Verify current tests pass before making changes
npm run test

# Verify TypeScript compiles
npx tsc --noEmit
```

## Development Workflow

```bash
# Start frontend dev server (for visual testing against running backend)
cd frontend && npm run dev

# Start backend (separate terminal — only for manual visual testing)
conda activate ac-race-engineer
cd backend && python -m api.server --port 57832

# Run frontend tests after each change
cd frontend && npm run test

# TypeScript check after each change
cd frontend && npx tsc --noEmit
```

## Verification

### Automated

```bash
# Full frontend test suite (must pass: ~431+ tests, 0 failures)
cd frontend && npm run test

# TypeScript strict (must pass: 0 errors)
cd frontend && npx tsc --noEmit
```

### Manual (requires running backend with session data)

1. **Session Detail Header**: Navigate to any session → header shows car badge/name, track preview/name, date, laps, best time, status badge
2. **Lap Analysis**: Open Laps tab → verify updated card styling, lap list, charts, corner table
3. **Setup Compare**: Open Setup tab → verify updated stint selector, diff sections, metrics panel
4. **Engineer**: Open Engineer tab → verify updated chat bubbles, recommendation cards, modals
5. **Settings**: Navigate to Settings → verify updated card styling, form elements, car data table
6. **Theme Toggle**: Switch between Night Grid and Garage Floor → verify all views render correctly in both
7. **Responsive**: Narrow the window → verify layouts adapt without breaking

## Key Files

### New Files
- `frontend/src/components/layout/SessionHeader.tsx` — session detail context header
- `frontend/src/components/layout/SessionHeader.css` — header styles
- `frontend/tests/components/layout/SessionHeader.test.tsx` — header tests

### Modified Files (CSS updates)
- `frontend/src/views/analysis/AnalysisView.css`
- `frontend/src/views/compare/CompareView.css`
- `frontend/src/views/engineer/EngineerView.css`
- `frontend/src/views/settings/Settings.css`
- `frontend/src/views/settings/CarDataSection.css`
- `frontend/src/components/layout/SessionLayout.tsx` — adds SessionHeader
- `frontend/src/components/layout/SessionLayout.css` — layout adjustments
- `frontend/src/tokens.css` — potential minor token additions

### Reference Files (read-only)
- `frontend/prototypes/6-*.html` — Lap Analysis visual reference
- `frontend/prototypes/7-*.html` — Setup Compare visual reference
- `frontend/prototypes/8-*.html` — Engineer visual reference
- `frontend/prototypes/11-*.html` — Settings visual reference
