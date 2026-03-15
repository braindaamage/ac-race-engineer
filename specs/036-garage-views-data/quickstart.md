# Quickstart: Garage Views Data Population

**Branch**: `036-garage-views-data` | **Date**: 2026-03-15

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- Node.js 20 LTS, npm
- Assetto Corsa installed (for testing with real AC assets; optional — tests use fixtures)

## Development Setup

```bash
# Backend
conda activate ac-race-engineer
cd backend
pip install -e ".[dev]"   # if not already installed
pytest tests/ -v --tb=short   # verify baseline: ~1055 tests pass

# Frontend
cd frontend
npm install
npm run test   # verify baseline: ~402 tests pass
npx tsc --noEmit   # verify zero type errors
```

## Key Files to Create/Modify

### Backend — New Files
- `backend/ac_engineer/resolver/ac_assets.py` — AC metadata reader (CarInfo, TrackInfo, read_car_info, read_track_info, car_badge_path, track_preview_path)
- `backend/tests/resolver/test_ac_assets.py` — Tests for AC metadata reader
- `backend/tests/resolver/fixtures/` — Fixture ui_car.json, ui_track.json, badge.png for tests
- `backend/api/routes/tracks.py` — Track preview image endpoint
- `backend/tests/api/test_tracks_routes.py` — Tests for track routes

### Backend — Modified Files
- `backend/ac_engineer/storage/db.py` — Add migration for track_config column + indexes
- `backend/ac_engineer/storage/models.py` — Add track_config field to SessionRecord
- `backend/ac_engineer/storage/sessions.py` — Add list_car_stats(), list_track_stats(), extend list_sessions()
- `backend/ac_engineer/storage/__init__.py` — Export new functions
- `backend/api/routes/sessions.py` — Add grouped endpoints, track/track_config query params
- `backend/api/routes/cars.py` — Add badge image endpoint
- `backend/api/watcher/scanner.py` — Persist track_config when saving sessions
- `backend/api/main.py` — Register tracks router

### Frontend — Modified Files
- `frontend/src/lib/types.ts` — Add CarStatsRecord, TrackStatsRecord, response types, track_config to SessionRecord
- `frontend/src/hooks/useCarStats.ts` — New hook for GET /sessions/grouped/cars
- `frontend/src/hooks/useCarTracks.ts` — New hook for GET /sessions/grouped/cars/{car}/tracks
- `frontend/src/views/garage/index.tsx` — Replace placeholder with car cards grid
- `frontend/src/views/garage/GarageView.css` — Styles for garage view
- `frontend/src/views/tracks/index.tsx` — Replace placeholder with track cards grid
- `frontend/src/views/tracks/CarTracksView.css` — Styles for tracks view
- `frontend/src/views/sessions/index.tsx` — Add contextual header, read config from searchParams
- `frontend/src/components/layout/Breadcrumb.tsx` — Use display names from API data
- `frontend/src/router.tsx` — No route changes needed (config is a query param)

### Frontend — Modified Test Files
- `frontend/tests/views/sessions/SessionsView.test.tsx` — Adapt tests for contextual header rendering and track_config query parameter handling

### Frontend — New Test Files
- `frontend/tests/hooks/useCarStats.test.ts`
- `frontend/tests/hooks/useCarTracks.test.ts`
- `frontend/tests/views/garage/GarageView.test.tsx`
- `frontend/tests/views/tracks/CarTracksView.test.tsx`

## Running Tests

```bash
# Backend only
conda activate ac-race-engineer
pytest backend/tests/storage/test_sessions.py -v   # aggregation tests
pytest backend/tests/resolver/test_ac_assets.py -v  # metadata reader tests
pytest backend/tests/api/test_sessions_routes.py -v  # endpoint tests
pytest backend/tests/api/test_cars_routes.py -v      # badge endpoint
pytest backend/tests/api/test_tracks_routes.py -v    # preview endpoint

# Frontend only
cd frontend
npm run test -- tests/hooks/useCarStats.test.ts
npm run test -- tests/hooks/useCarTracks.test.ts
npm run test -- tests/views/garage/GarageView.test.tsx
npm run test -- tests/views/tracks/CarTracksView.test.tsx
npm run test -- tests/views/sessions/SessionsView.test.tsx

# Full suites
conda activate ac-race-engineer && pytest backend/tests/ -v
cd frontend && npm run test
```

## Manual Verification

1. Start backend: `conda activate ac-race-engineer && python -m api.server --port 57832`
2. Start frontend: `cd frontend && npm run dev`
3. Ensure `data/config.json` has a valid `ac_install_path` pointing to your AC install
4. Verify sessions exist (or trigger sync)
5. Navigate to Garage Home — car cards should appear with badge images
6. Click a car — track cards should appear with preview images and stats
7. Click a track — sessions list should be filtered with contextual header
8. Breadcrumb should show display names, not raw folder identifiers

## Architecture Notes

- **Storage layer** (`ac_engineer/storage/sessions.py`): Pure SQL aggregation, returns dicts
- **Asset reader** (`ac_engineer/resolver/ac_assets.py`): Pure file I/O, returns Pydantic models
- **API layer** (`api/routes/`): Merges storage stats with asset metadata into response models
- **Frontend**: Fetches pre-assembled data from API, does client-side search filtering only
- This follows the three-layer separation (Principle IX): storage → API → frontend
