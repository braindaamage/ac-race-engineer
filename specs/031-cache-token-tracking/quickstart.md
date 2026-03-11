# Quickstart: Cache Token Tracking

**Feature**: 031-cache-token-tracking | **Date**: 2026-03-11

## Overview

This feature adds two integer fields (`cache_read_tokens`, `cache_write_tokens`) to the existing LLM usage tracking pipeline. The change touches 8 existing files across 4 layers — no new files needed.

## Implementation Order

### Layer 1: Storage (backend/ac_engineer/storage/)

1. **models.py** — Add `cache_read_tokens: int = Field(default=0, ge=0)` and `cache_write_tokens: int = Field(default=0, ge=0)` to `LlmEvent`
2. **db.py** — Add migration 7 to `_MIGRATIONS`: two `ALTER TABLE llm_events ADD COLUMN` statements with `DEFAULT 0`
3. **usage.py** — Include `cache_read_tokens` and `cache_write_tokens` in the INSERT statement of `save_llm_event()` and the SELECT reconstruction in `get_llm_events()`

### Layer 2: Capture (backend/ac_engineer/engineer/ + backend/api/engineer/)

4. **agents.py** — In `analyze_with_engineer()` usage capture block (~line 625), read `usage.cache_read_tokens` and `usage.cache_write_tokens` into the `LlmEvent` constructor
5. **pipeline.py** — In `make_chat_job()` usage capture block (~line 218), read the same two fields into the `LlmEvent` constructor

### Layer 3: API (backend/api/engineer/)

6. **serializers.py** — Add `cache_read_tokens: int = 0` and `cache_write_tokens: int = 0` to both `AgentUsageDetail` and `UsageTotals`
7. **routes/engineer.py** — In `_compute_usage_response()`, sum cache fields for totals and pass them through for per-agent detail

### Layer 4: Frontend (frontend/src/)

8. **lib/types.ts** — Add `cache_read_tokens: number` and `cache_write_tokens: number` to `UsageTotals` and `AgentUsageDetail` interfaces
9. **views/engineer/UsageSummaryBar.tsx** — Conditionally show cache_read_tokens total when > 0
10. **views/engineer/UsageDetailModal.tsx** — Conditionally show cache_read and cache_write per agent when either > 0

## Testing

- **Storage tests**: Verify save/get round-trip with cache fields; verify 0 defaults for records without cache data
- **Capture tests**: Verify LlmEvent construction includes cache fields from mock RunUsage
- **API tests**: Verify usage endpoint responses include cache fields
- **Frontend tests**: Verify conditional rendering (shown when non-zero, hidden when zero)

## Commands

```bash
# Backend tests
conda run -n ac-race-engineer pytest backend/tests/ -v

# Frontend type check + tests
cd frontend && npx tsc --noEmit && npm run test
```
