# Quickstart: Usage Storage

**Feature**: 023-usage-storage | **Date**: 2026-03-08

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- Existing project dependencies (pydantic, pytest)

## Development Setup

```bash
conda activate ac-race-engineer
```

## Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `backend/ac_engineer/storage/models.py` | MODIFY | Add `ToolCallDetail`, `AgentUsage`, `VALID_DOMAINS` |
| `backend/ac_engineer/storage/db.py` | MODIFY | Add 2 entries to `_MIGRATIONS` list |
| `backend/ac_engineer/storage/usage.py` | CREATE | `save_agent_usage()`, `get_agent_usage()` |
| `backend/ac_engineer/storage/__init__.py` | MODIFY | Export new models and functions |
| `backend/tests/storage/test_usage.py` | CREATE | Tests for usage CRUD + migration |

## Implementation Order

1. **Models** (`models.py`) — Add `VALID_DOMAINS`, `ToolCallDetail`, `AgentUsage`
2. **Migration** (`db.py`) — Add `CREATE TABLE IF NOT EXISTS` for both tables to `_MIGRATIONS`
3. **CRUD** (`usage.py`) — Implement `save_agent_usage` and `get_agent_usage`
4. **Exports** (`__init__.py`) — Wire up public API
5. **Tests** (`test_usage.py`) — Verify all scenarios from spec

## Running Tests

```bash
conda activate ac-race-engineer

# Run only usage tests
pytest backend/tests/storage/test_usage.py -v

# Run all storage tests (to verify no regressions)
pytest backend/tests/storage/ -v

# Run full backend suite
pytest backend/tests/ -v
```

## Key Patterns to Follow

- **IDs**: `uuid.uuid4().hex` (32-char hex strings)
- **Timestamps**: `datetime.now(timezone.utc).isoformat()`
- **Connection**: Use `_connect(db_path)` from `storage/db.py`
- **Transaction**: Open connection → insert all rows → `conn.commit()` → close in `finally`
- **Retrieval**: Query parent rows, then query child rows per parent, return nested models
