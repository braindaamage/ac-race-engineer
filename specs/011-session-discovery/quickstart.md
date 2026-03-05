# Quickstart: Session Discovery

**Branch**: `011-session-discovery` | **Date**: 2026-03-05

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- Dependencies: `fastapi`, `uvicorn`, `pydantic`, `watchdog`

## Install new dependency

```bash
conda activate ac-race-engineer
pip install watchdog>=4.0
```

## Run the server

```bash
conda activate ac-race-engineer
cd backend
uvicorn api.main:create_app --factory --reload
```

The file watcher starts automatically and monitors `~/Documents/ac-race-engineer/sessions/`.

## Test the endpoints

```bash
# List all sessions
curl http://localhost:8000/sessions

# Get a specific session
curl http://localhost:8000/sessions/2026-03-05_1430_ks_ferrari_488_gt3_monza

# Trigger manual sync
curl -X POST http://localhost:8000/sessions/sync

# Delete a session (DB only, files preserved)
curl -X DELETE http://localhost:8000/sessions/2026-03-05_1430_ks_ferrari_488_gt3_monza
```

## Run tests

```bash
conda activate ac-race-engineer
pytest backend/tests/ -v
```

## Simulate a new session (for development)

Create a test file pair in the sessions directory:

```bash
mkdir -p ~/Documents/ac-race-engineer/sessions
# Create a minimal meta.json
echo '{"car_name":"test_car","track_name":"test_track","session_start":"2026-03-05T14:30:00","laps_completed":5,"session_type":"practice"}' > ~/Documents/ac-race-engineer/sessions/2026-03-05_1430_test_car_test_track.meta.json
# Create an empty CSV (watcher only needs it to exist)
touch ~/Documents/ac-race-engineer/sessions/2026-03-05_1430_test_car_test_track.csv
```

The session should appear in the list within 5 seconds.

## Project structure (new files)

```
backend/
  ac_engineer/
    storage/
      sessions.py       # extended: session_exists, delete_session, update_session_state
      models.py          # extended: SessionRecord new fields, SyncResult
      db.py              # extended: init_db() migration for new columns
  api/
    watcher/
      __init__.py
      observer.py        # SessionWatcher: start/stop, watchdog Observer lifecycle
      handler.py         # SessionEventHandler: debounce, pair detection, registration
      scanner.py         # scan_sessions_dir(): pure function for directory scanning
    routes/
      sessions.py        # GET /sessions, GET /sessions/{id}, POST /sessions/sync, DELETE /sessions/{id}
  tests/
    storage/
      test_sessions_extended.py   # Tests for new storage functions
    api/
      test_sessions_routes.py     # Tests for session endpoints
      test_scanner.py             # Tests for directory scanner
      test_watcher.py             # Tests for file watcher handler
```
