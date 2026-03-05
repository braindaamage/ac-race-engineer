# Quickstart: Analysis Endpoints

**Feature**: 012-analysis-endpoints | **Date**: 2026-03-05

## Prerequisites

- conda environment `ac-race-engineer` (Python 3.11+)
- All Phase 6.1 and 6.2 dependencies installed (FastAPI, httpx, watchdog, etc.)

## Setup

```bash
# Activate the environment
conda activate ac-race-engineer

# Verify existing tests pass (530+ from Phases 2-5, plus Phase 6.1-6.2 API tests)
pytest backend/tests/ -v --tb=short

# No new dependencies required — this phase uses only existing packages
```

## Development Workflow

### New files to create

```
backend/api/analysis/__init__.py
backend/api/analysis/cache.py
backend/api/analysis/pipeline.py
backend/api/analysis/serializers.py
backend/api/routes/analysis.py
backend/tests/api/test_analysis_cache.py
backend/tests/api/test_analysis_pipeline.py
backend/tests/api/test_analysis_serializers.py
backend/tests/api/test_analysis_routes.py
```

### File to modify

```
backend/api/main.py  — add one line to register the analysis router
```

### Run tests

```bash
# Run only analysis tests
pytest backend/tests/api/test_analysis_cache.py backend/tests/api/test_analysis_pipeline.py backend/tests/api/test_analysis_serializers.py backend/tests/api/test_analysis_routes.py -v

# Run all API tests
pytest backend/tests/api/ -v

# Run all tests
pytest backend/tests/ -v
```

### Test the server manually

```bash
# Start the server
conda run -n ac-race-engineer uvicorn api.main:app --reload --app-dir backend

# Sync sessions (discover from filesystem)
curl -X POST http://localhost:8000/sessions/sync

# List sessions
curl http://localhost:8000/sessions

# Process a session (get session_id from list above)
curl -X POST http://localhost:8000/sessions/{session_id}/process

# Watch job progress via WebSocket
# (use wscat or browser dev tools)
# ws://localhost:8000/ws/jobs/{job_id}

# Query metrics (after processing completes)
curl http://localhost:8000/sessions/{session_id}/laps
curl http://localhost:8000/sessions/{session_id}/laps/1
curl http://localhost:8000/sessions/{session_id}/corners
curl http://localhost:8000/sessions/{session_id}/corners/1
curl http://localhost:8000/sessions/{session_id}/stints
curl "http://localhost:8000/sessions/{session_id}/compare?stint_a=0&stint_b=1"
curl http://localhost:8000/sessions/{session_id}/consistency
```

## Key Patterns

### Test fixtures
Reuse the programmatic fixture builders from `backend/tests/analyzer/conftest.py`:
- `make_parsed_session()` — build a ParsedSession with controlled data
- `make_lap_segment()` — build individual laps
- `make_corner()` — build corners

For route tests, build an AnalyzedSession by running `analyze_session()` on a fixture session, then save it via the new cache module. This gives realistic test data without needing real telemetry files.

### Guard rail pattern
Extract a shared dependency or helper for the common session-lookup + state-check logic used by all metric endpoints. This avoids duplicating the 404/409 checks in every route handler.
