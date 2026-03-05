# Quickstart: API Server Infrastructure

**Feature**: 010-api-server-infra
**Date**: 2026-03-05

## Prerequisites

- conda environment `ac-race-engineer` with Python 3.11+
- Packages: `fastapi`, `uvicorn`, `httpx` (for tests)

## Install Dependencies

```bash
conda activate ac-race-engineer
pip install fastapi httpx
```

(`uvicorn` 0.41.0 is already installed in the environment.)

## Start the Server

```bash
# Default port (57832)
conda run -n ac-race-engineer python -m api.server

# Custom port via argument
conda run -n ac-race-engineer python -m api.server --port 8080

# Custom port via environment variable
PORT=8080 conda run -n ac-race-engineer python -m api.server
```

Working directory must be `backend/` (or `backend/` must be on `PYTHONPATH`).

## Verify It Works

```bash
curl http://localhost:57832/health
# → {"status":"ok","version":"0.1.0"}
```

## Run Tests

```bash
conda run -n ac-race-engineer pytest backend/tests/api/ -v
```

## Project Structure

```
backend/
  api/
    __init__.py          # Package marker
    main.py              # FastAPI app factory + lifespan
    server.py            # CLI entry point (--port, starts uvicorn)
    jobs/
      __init__.py
      manager.py         # In-memory JobManager (create, update, get, cancel)
      models.py          # Job, JobEvent, JobStatus Pydantic models
      worker.py          # Async task runner wrapping callables as jobs
    routes/
      __init__.py
      health.py          # GET /health
      jobs.py            # GET /jobs/{job_id}
    ws/
      __init__.py
      jobs.py            # WebSocket /ws/jobs/{job_id}
    errors/
      __init__.py
      handlers.py        # Global exception handlers
      models.py          # ErrorResponse Pydantic model
  tests/
    api/
      __init__.py
      test_health.py     # Health endpoint tests
      test_jobs_manager.py  # JobManager unit tests
      test_jobs_worker.py   # Worker lifecycle tests
      test_jobs_api.py      # GET /jobs/{job_id} tests
      test_ws_jobs.py       # WebSocket integration tests
      test_errors.py        # Error handling tests
      conftest.py           # Shared fixtures (app, client, manager)
```
