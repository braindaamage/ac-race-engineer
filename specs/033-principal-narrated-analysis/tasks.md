# Tasks: Principal Narrated Analysis

**Input**: Design documents from `/specs/033-principal-narrated-analysis/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included — the spec explicitly defines test requirements for backend (agents, storage, API) and frontend.

**Organization**: Tasks grouped by user story. US1+US2 share implementation (principal agent produces both fields in one call). US5 fallback is inherent to the synthesis implementation but has dedicated test tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Model + Prompt)

**Purpose**: Add the structured output model and adapt the principal agent prompt — prerequisites for the synthesis implementation.

- [ ] T001 Add `PrincipalNarrative` Pydantic model (summary: str, explanation: str) in `backend/ac_engineer/engineer/models.py`
- [ ] T002 [P] Adapt the user prompt in `_synthesize_with_principal()` (agents.py, from T007) to include explicit instructions for two distinct fields — summary (2–4 sentences, ≤80 words, executive headline, driver-friendly language, no raw parameter names) and explanation (multi-paragraph, ≤300 words, cause-effect, trade-offs, technique integration, expected feel). The system prompt continues to use `principal.md` as-is (loaded via `_load_skill_prompt("principal")`) — do NOT modify `principal.md` because it is also used by the chat agent in pipeline.py. All synthesis-specific output formatting instructions go in the user prompt, not the system prompt.

---

## Phase 2: Foundational (Database + Storage)

**Purpose**: DB migration and storage updates — MUST complete before principal agent can persist explanation.

**⚠️ CRITICAL**: No user story work that persists data can begin until this phase is complete.

- [ ] T003 Add migration to `_MIGRATIONS` list in `backend/ac_engineer/storage/db.py`: `ALTER TABLE recommendations ADD COLUMN explanation TEXT NOT NULL DEFAULT ''`
- [ ] T004 [P] Update `save_recommendation()` in `backend/ac_engineer/storage/recommendations.py` to accept `explanation: str = ""` parameter and INSERT it into the recommendations table
- [ ] T005 [P] Update `get_recommendations()` and related queries in `backend/ac_engineer/storage/recommendations.py` to SELECT and return the `explanation` field in the Recommendation return object
- [ ] T006 Add tests for explanation column in `backend/tests/storage/test_recommendations.py`: migration applies cleanly, save_recommendation persists explanation, get_recommendations returns explanation, default empty string for legacy rows

**Checkpoint**: Database schema supports explanation field. Storage CRUD works with explanation.

---

## Phase 3: User Story 1+2 — Principal Agent Synthesis (Priority: P1) 🎯 MVP

**Goal**: After specialist agents complete and results are conflict-resolved and post-validated, invoke the principal agent to produce an original summary (executive headline) and explanation (detailed narrative) that replace the concatenated domain_summaries.

**Independent Test**: Run an analysis with multiple specialist domains. Verify summary is an original 2–4 sentence paragraph without domain-name prefixes. Verify explanation is multi-paragraph, connects domains causally, does not repeat individual change reasoning fields, and closes with expected driver feel.

### Implementation for US1+US2

- [ ] T007 [US1] Implement `_synthesize_with_principal()` in `backend/ac_engineer/engineer/agents.py`: build a Pydantic AI Agent with `result_type=PrincipalNarrative`, no tools, system prompt from `_load_skill_prompt("principal")`, model from `build_model(config)`, `usage_limits=UsageLimits(request_limit=5)`. Format user prompt with: domain_summaries, setup_changes (section/parameter/reasoning/expected_effect), driver_feedback (area/observation/suggestion), signals_addressed. Return PrincipalNarrative on success.
- [ ] T008 [US1] Wire `_synthesize_with_principal()` into `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py`: call it AFTER `_resolve_conflicts()` and `_post_validate_changes()` complete, passing the final EngineerResponse and specialist_results. On success, replace `response.summary` and `response.explanation` with the principal agent's output. Wrap in try/except Exception with logging — on failure, keep concatenated text (FR-011 fallback).
- [ ] T009 [US1] Add LLM usage tracking for the principal agent call in `backend/ac_engineer/engineer/agents.py`: build `LlmEvent` with `agent_name="principal"`, `event_type="analysis"`, extract usage from result, call `save_llm_event()`. Follow existing specialist agent tracking pattern.
- [ ] T010 [US1] Update `make_engineer_job()` in `backend/api/engineer/pipeline.py`: pass `response.explanation` to `save_recommendation()` call so the explanation is persisted to SQLite alongside the summary.
- [ ] T011 [US1] Add tests for principal synthesis in `backend/tests/engineer/test_agents.py`: (a) _synthesize_with_principal returns PrincipalNarrative with distinct summary and explanation using FunctionModel, (b) analyze_with_engineer produces non-concatenated summary and explanation, (c) LlmEvent is created with agent_name="principal" and event_type="analysis", (d) principal agent receives no tools (agent has empty tools list).

**Checkpoint**: Analysis pipeline produces principal-authored summary and explanation. Explanation is persisted to DB. Usage is tracked.

---

## Phase 4: User Story 5 — Graceful Degradation (Priority: P2)

**Goal**: When the principal agent LLM call fails, the system falls back to concatenated domain_summaries for both fields without surfacing an error.

**Independent Test**: Simulate a principal agent failure. Verify analysis completes with concatenated text and no error shown.

### Implementation for US5

- [ ] T012 [US5] Add fallback tests in `backend/tests/engineer/test_agents.py`: (a) when _synthesize_with_principal raises Exception, analyze_with_engineer still completes with concatenated domain_summaries as summary and explanation, (b) no error is propagated — EngineerResponse is returned normally, (c) LlmEvent for principal is NOT saved on failure (no partial tracking).

**Checkpoint**: Fallback behavior verified — principal agent failures never block analysis.

---

## Phase 5: User Story 4 — DB Persistence via API (Priority: P2)

**Goal**: The API returns explanation from the database, surviving cache eviction.

**Independent Test**: Run analysis, delete JSON cache, retrieve recommendation via API — explanation is still present.

### Implementation for US4

- [ ] T013 [US4] Update `get_recommendation_detail()` in `backend/api/routes/engineer.py`: read `explanation` from the DB Recommendation object (via `get_recommendations()`). When cache is available, prefer cache for fields like confidence/signals_addressed but always include explanation from DB. When cache is missing, explanation comes from DB (no longer empty string).
- [ ] T014 [US4] Add API tests in `backend/tests/api/test_engineer_routes.py`: (a) GET recommendation detail returns explanation field from DB, (b) when JSON cache is missing, explanation is still returned from DB, (c) legacy recommendations (empty explanation) return explanation as empty string.

**Checkpoint**: Explanation survives cache eviction. API always returns explanation from durable storage.

---

## Phase 6: User Story 3 — Frontend Display (Priority: P1)

**Goal**: The driver can view the explanation in an expandable section below the summary on the recommendation card.

**Independent Test**: View a recommendation card — summary visible at top, explanation accessible via expand action. Empty explanation hides the section.

### Implementation for US3

- [ ] T015 [US3] Add collapsible explanation section in `frontend/src/views/engineer/RecommendationCard.tsx`: collapsed by default, toggle on click, render explanation with paragraph breaks (split on `\n\n`). Hide section entirely when `recommendation.explanation` is empty string. Use CSS design tokens for styling (no hardcoded colors).
- [ ] T016 [US3] Add frontend tests in `frontend/tests/views/engineer/RecommendationCard.test.tsx`: (a) explanation section is collapsed by default when explanation is non-empty, (b) clicking expand shows full explanation with paragraph formatting, (c) when explanation is empty string, no expandable section is rendered, (d) summary remains visible regardless of explanation state.

**Checkpoint**: Driver can view full explanation in one click. Empty explanation is gracefully hidden.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate all stories work together, no regressions.

- [ ] T017 Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) and fix any regressions
- [ ] T018 Run full frontend test suite (`cd frontend && npm run test`) and TypeScript strict check (`npx tsc --noEmit`) and fix any regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: No dependency on Phase 1 for DB/storage work; T004/T005 parallel
- **US1+US2 (Phase 3)**: Depends on Phase 1 (PrincipalNarrative model, prompt) AND Phase 2 (save_recommendation accepts explanation)
- **US5 (Phase 4)**: Depends on Phase 3 (fallback is part of synthesis implementation; Phase 4 adds explicit tests)
- **US4 (Phase 5)**: Depends on Phase 2 (DB migration) and Phase 3 (explanation populated in pipeline)
- **US3 (Phase 6)**: Depends on Phase 5 (API returns explanation) — can start frontend work in parallel if mocking API
- **Polish (Phase 7)**: Depends on all previous phases

### User Story Dependencies

- **US1+US2 (P1)**: Core synthesis — must complete first. Depends on Foundational.
- **US5 (P2)**: Fallback testing — depends on US1+US2 implementation.
- **US4 (P2)**: DB persistence via API — depends on Foundational + US1+US2 (explanation must be populated).
- **US3 (P1)**: Frontend display — depends on US4 (API must serve explanation). Can start with mock data.

### Within Each Phase

- Models before agent implementation
- Agent implementation before pipeline integration
- Pipeline integration before API route updates
- Backend complete before frontend
- Tests alongside or immediately after implementation

### Parallel Opportunities

- T004 and T005 can run in parallel (different functions in same file, independent changes)
- Phase 1 (T001, T002) and Phase 2 (T003–T006) can run in parallel (different files)
- Frontend work (Phase 6) can start in parallel with backend API work (Phase 5) using mock data
- T017 and T018 can run in parallel (backend vs frontend test suites)

---

## Parallel Example: Phase 1 + Phase 2

```bash
# These can run simultaneously (different files):
Task T001: "Add PrincipalNarrative model in backend/ac_engineer/engineer/models.py"
Task T003: "Add migration in backend/ac_engineer/storage/db.py"
Task T004: "Update save_recommendation() in backend/ac_engineer/storage/recommendations.py"
Task T005: "Update get_recommendations() in backend/ac_engineer/storage/recommendations.py"
```

---

## Implementation Strategy

### MVP First (US1+US2 Only)

1. Complete Phase 1: Setup (model + prompt)
2. Complete Phase 2: Foundational (DB migration + storage)
3. Complete Phase 3: US1+US2 (principal synthesis + pipeline)
4. **STOP and VALIDATE**: Run analysis, verify summary and explanation are distinct principal-authored narratives
5. This delivers the core value — coherent narrative analysis

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1+US2 → Principal synthesis works → **MVP!**
3. US5 → Fallback verified → Resilience confirmed
4. US4 → API serves explanation from DB → Durability confirmed
5. US3 → Frontend displays explanation → **Full feature complete**
6. Polish → All tests pass, no regressions

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 share implementation — principal agent produces both fields in one structured output call
- US5 fallback is implemented inside the try/except in T008 — Phase 4 adds dedicated test coverage
- The principal agent uses NO tools for synthesis — all data is in the prompt (R-003)
- Existing infrastructure requires no changes: EngineerResponse.explanation, RecommendationDetailResponse.explanation, frontend types.ts (R-007)
- Total: 18 tasks across 7 phases
