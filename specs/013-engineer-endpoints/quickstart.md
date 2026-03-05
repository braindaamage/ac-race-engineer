# Quickstart: Engineer Endpoints

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- All existing tests passing (530+)
- A session in "analyzed" state in the database (run processing first)

## Development Setup

```bash
conda activate ac-race-engineer
cd backend
```

## Key Files to Create

1. `backend/api/engineer/__init__.py` — public imports
2. `backend/api/engineer/pipeline.py` — `make_engineer_job()`, `make_chat_job()`
3. `backend/api/engineer/serializers.py` — API response models
4. `backend/api/routes/engineer.py` — 7 endpoint handlers
5. `backend/tests/api/test_engineer_pipeline.py`
6. `backend/tests/api/test_engineer_serializers.py`
7. `backend/tests/api/test_engineer_routes.py`

## Key Files to Modify

1. `backend/api/main.py` — add `active_engineer_jobs` to lifespan, include engineer router

## Implementation Order

1. **Serializers** — Define API response models (pure Pydantic, no dependencies)
2. **Pipeline** — `make_engineer_job()` factory (depends on ac_engineer.engineer + serializers)
3. **Pipeline** — `make_chat_job()` factory (depends on Pydantic AI + serializers)
4. **Routes** — All 7 endpoints (depends on pipeline + serializers)
5. **Main** — Register router and add state (one-liner changes)

## Running Tests

```bash
# All engineer endpoint tests
conda run -n ac-race-engineer pytest backend/tests/api/test_engineer_pipeline.py backend/tests/api/test_engineer_serializers.py backend/tests/api/test_engineer_routes.py -v

# Full suite (should stay at 530+ existing tests + new tests)
conda run -n ac-race-engineer pytest backend/tests/ -v
```

## Testing Patterns

- Pipeline tests: mock `analyze_with_engineer()` and LLM calls
- Route tests: use `httpx.AsyncClient` with `create_app()`, pre-populate SQLite via storage functions, pre-cache `analyzed.json`
- All tests use `tmp_path` — no real LLM calls, no real setup files
- Follow `ALLOW_MODEL_REQUESTS=False` pattern from Phase 5.3 for Pydantic AI mocks

## Endpoint Quick Reference

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| POST | /sessions/{id}/engineer | 202 | Run AI engineer (job) |
| GET | /sessions/{id}/recommendations | 200 | List recommendations |
| GET | /sessions/{id}/recommendations/{rec_id} | 200 | Recommendation detail |
| POST | /sessions/{id}/recommendations/{rec_id}/apply | 200 | Apply to .ini |
| GET | /sessions/{id}/messages | 200 | Chat history |
| POST | /sessions/{id}/messages | 202 | Send message (job) |
| DELETE | /sessions/{id}/messages | 200 | Clear chat |
