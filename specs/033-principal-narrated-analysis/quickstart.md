# Quickstart: Principal Narrated Analysis

**Feature**: 033-principal-narrated-analysis | **Date**: 2026-03-11

## What This Feature Does

Replaces the mechanical concatenation of specialist domain summaries with a principal-agent-authored narrative. After all specialist agents complete their analysis, the principal agent synthesizes their findings into two distinct outputs:
- **Summary**: 2–4 sentence executive headline (dominant problem, severity, correction direction)
- **Explanation**: Multi-paragraph detailed narrative (cause-effect, trade-offs, expected feel)

## Files to Modify

### Backend Core (ac_engineer/)
1. **`engineer/models.py`** — Add `PrincipalNarrative` model (summary + explanation)
2. **`engineer/agents.py`** — Add `_synthesize_with_principal()` function; call it after `_combine_results()` in `analyze_with_engineer()`
3. **`engineer/skills/principal.md`** — Adapt prompt for structured output (distinct summary vs explanation guidance)
4. **`storage/db.py`** — Add migration for `explanation` column on `recommendations` table
5. **`storage/recommendations.py`** — Add `explanation` parameter to `save_recommendation()`; include `explanation` in `get_recommendations()` return

### Backend API (api/)
6. **`api/routes/engineer.py`** — Update `get_recommendation_detail()` to read `explanation` from DB (not only from cache)
7. **`api/engineer/pipeline.py`** — Pass `explanation` to `save_recommendation()` call

### Frontend
8. **`frontend/src/views/engineer/RecommendationCard.tsx`** — Add collapsible explanation section below summary

### Tests
9. **`backend/tests/engineer/test_agents.py`** — Tests for principal synthesis (structured output, fallback, LLM event)
10. **`backend/tests/storage/test_recommendations.py`** — Tests for explanation column migration and persistence
11. **`backend/tests/api/test_engineer_routes.py`** — Tests for explanation in API response
12. **`frontend/tests/views/engineer/RecommendationCard.test.tsx`** — Tests for expandable section and empty-state

## Key Patterns to Follow

- **Structured output**: `Agent[AgentDeps | None, PrincipalNarrative](result_type=PrincipalNarrative)` — same pattern as specialist agents
- **Model construction**: Use existing `build_model(config)` function
- **Usage tracking**: Build `LlmEvent` with `agent_name="principal"`, `event_type="analysis"`, same as specialists
- **Fallback**: `try/except Exception` → keep `_combine_results()` output
- **DB migration**: Append to `_MIGRATIONS` list in `db.py`
- **Frontend pattern**: Toggle state for expand/collapse, conditionally render when explanation is non-empty
