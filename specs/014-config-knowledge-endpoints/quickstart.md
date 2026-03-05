# Quickstart: Config, Knowledge & Packaging Endpoints

**Feature**: 014-config-knowledge-endpoints

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- All existing tests passing: `conda run -n ac-race-engineer pytest backend/tests/ -v`

## Development Order

1. **`api/paths.py`** — Path resolution module (no dependencies on new code)
2. **`api/routes/config.py`** — Config endpoints (depends on paths.py for config_path)
3. **`api/routes/knowledge.py`** — Knowledge endpoints (depends on paths.py, reuses analysis cache)
4. **`api/main.py` modifications** — Register new routers, use paths.py in lifespan
5. **Tests** — Can be written alongside each step
6. **`build/`** — PyInstaller spec + docs (last, depends on everything being stable)

## Key Integration Points

### paths.py
- Imported by `api/main.py` to set `app.state.config_path`, `app.state.db_path`, `app.state.sessions_dir`
- Replaces `DEFAULT_DB_PATH` and `DEFAULT_SESSIONS_DIR` in `main.py`
- Replaces `DEFAULT_CONFIG_PATH` in `routes/engineer.py`

### config.py routes
- Imports `read_config`, `update_config` from `ac_engineer.config`
- Gets `config_path` from `request.app.state.config_path`

### knowledge.py routes
- Imports `search_knowledge`, `get_knowledge_for_signals` from `ac_engineer.knowledge`
- Imports `detect_signals` from `ac_engineer.knowledge.signals`
- Imports `load_analyzed_session` from `api.analysis.cache`
- Gets `db_path`, `sessions_dir` from `request.app.state`

## Running Tests

```bash
# All tests
conda run -n ac-race-engineer pytest backend/tests/ -v

# Just the new tests
conda run -n ac-race-engineer pytest backend/tests/api/test_config_routes.py backend/tests/api/test_knowledge_routes.py backend/tests/api/test_paths.py -v
```

## Testing the Server Manually

```bash
# Start server
conda run -n ac-race-engineer python -m api.server

# Test config endpoints
curl http://localhost:57832/config
curl -X PATCH http://localhost:57832/config -H "Content-Type: application/json" -d '{"llm_provider": "openai"}'
curl http://localhost:57832/config/validate

# Test knowledge endpoints
curl "http://localhost:57832/knowledge/search?q=understeer"
curl http://localhost:57832/sessions/{session_id}/knowledge
```
