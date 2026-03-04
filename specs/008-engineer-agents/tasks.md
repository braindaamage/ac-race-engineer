# Tasks: Engineer Agents

**Input**: Design documents from `/specs/008-engineer-agents/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/agents-api.md

**Tests**: Included — spec requires ~40 tests, all using Pydantic AI TestModel/FunctionModel (no real LLM calls).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend source**: `backend/ac_engineer/engineer/`
- **Tests**: `backend/tests/engineer/`
- **Skills prompts**: `backend/ac_engineer/engineer/skills/`

---

## Phase 1: Setup

**Purpose**: Add pydantic-ai dependency, create module skeleton, configure test infrastructure

- [ ] T001 Add `pydantic-ai[anthropic]` to dependencies in `backend/pyproject.toml` and install into conda env `ac-race-engineer`
- [ ] T002 Create `backend/ac_engineer/engineer/skills/` directory with empty `__init__.py` (or no init — it's a data dir)
- [ ] T003 Add SpecialistResult and AgentDeps models to `backend/ac_engineer/engineer/models.py` per data-model.md (SpecialistResult: setup_changes, driver_feedback, domain_summary; AgentDeps: session_summary, parameter_ranges, domain_signals, knowledge_fragments)
- [ ] T004 Add test infrastructure to `backend/tests/engineer/conftest.py`: set `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False`, add fixtures for AgentDeps builder and sample SessionSummary with signals

**Checkpoint**: Skeleton ready, pydantic-ai importable, test infrastructure in place

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Signal routing, model string builder, and tool implementations — deterministic Python functions that all user stories depend on

**CRITICAL**: No agent work can begin until these are complete

- [ ] T005 Implement `route_signals()` and constants (SIGNAL_DOMAINS, DOMAIN_PRIORITY, AERO_SECTIONS) in `backend/ac_engineer/engineer/agents.py` per research.md R3 and contracts/agents-api.md — pure function, no LLM
- [ ] T006 [P] Implement `get_model_string(config)` in `backend/ac_engineer/engineer/agents.py` per research.md R5 — maps ACConfig provider/model to Pydantic AI model string (handles "gemini" → "google" prefix)
- [ ] T007 [P] Implement tool functions in `backend/ac_engineer/engineer/tools.py`: `search_kb(ctx, query)` wrapping `search_knowledge()`, `get_setup_range(ctx, section)` wrapping parameter range lookup, `get_current_value(ctx, section)` reading from active_setup_parameters, `get_lap_detail(ctx, lap_number)` returning full metrics for a specific flying lap from SessionSummary.laps (empty dict if not found), `get_corner_metrics(ctx, corner_number, lap_number=None)` returning CornerIssue data for a specific corner averaged across flying laps or for a specific lap (None if not found)
- [ ] T008 Write tests for route_signals() in `backend/tests/engineer/test_agents.py`: single-domain signals, multi-domain signals (brake_balance_issue → balance+technique), aero detection from setup parameters, no signals → empty, unknown signals ignored (~8 tests)
- [ ] T009 [P] Write tests for get_model_string() in `backend/tests/engineer/test_agents.py`: anthropic default, openai, gemini→google prefix, custom model override (~4 tests)
- [ ] T010 [P] Write tests for tool functions in `backend/tests/engineer/test_tools.py`: search_kb returns formatted fragments, get_setup_range returns range or None, get_current_value reads from summary, get_lap_detail returns correct lap or empty dict for unknown lap, get_corner_metrics returns aggregated data or per-lap data (~8 tests)

**Checkpoint**: All deterministic routing and tools tested, ready for agent definitions

---

## Phase 3: User Story 1 — Analyze a Session and Get Setup Recommendations (Priority: P1) MVP

**Goal**: Given a SessionSummary with detected signals, produce an EngineerResponse with targeted setup changes and driver-friendly explanations

**Independent Test**: Provide a SessionSummary with known signals → verify EngineerResponse contains appropriate changes with non-empty reasoning/expected_effect, correct signals_addressed, and valid confidence

### Implementation for User Story 1

- [ ] T011 [US1] Write system prompt `backend/ac_engineer/engineer/skills/principal.md` — role as race engineer orchestrator, instructions on combining specialist outputs into summary and explanation, confidence assessment guidelines
- [ ] T012 [P] [US1] Write system prompt `backend/ac_engineer/engineer/skills/balance.md` — role as balance specialist, domain knowledge summary (springs, ARB, dampers, brake bias), instructions to propose SetupChanges with reasoning/expected_effect referencing specific corners, tool usage for knowledge search
- [ ] T013 [P] [US1] Write system prompt `backend/ac_engineer/engineer/skills/tyre.md` — role as tyre specialist, domain knowledge (pressures, camber, toe, temps, wear), same tool/output instructions
- [ ] T014 [P] [US1] Write system prompt `backend/ac_engineer/engineer/skills/technique.md` — role as driving coach, produces DriverFeedback not SetupChanges, observes consistency/braking technique, references specific corners/laps
- [ ] T015 [US1] Define specialist Pydantic AI agents in `backend/ac_engineer/engineer/agents.py`: create `_build_specialist_agent(domain, model_string)` that loads the domain's skill prompt from `skills/{domain}.md`, registers tools from tools.py, sets `output_type=SpecialistResult` and `deps_type=AgentDeps`
- [ ] T016 [US1] Implement `_build_user_prompt(summary, domain_signals)` in `backend/ac_engineer/engineer/agents.py` — formats SessionSummary data into a natural language prompt for the specialist, including relevant signals, corner issues, tyre data, stint trends
- [ ] T017 [US1] Implement `_combine_results(session_id, specialist_results, summary)` in `backend/ac_engineer/engineer/agents.py` — merges all SpecialistResults into a single EngineerResponse: concatenate setup_changes and driver_feedback, build summary from domain_summaries, set signals_addressed, determine overall confidence
- [ ] T018 [US1] Implement `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py` per contracts/agents-api.md — orchestrates: read_parameter_ranges → route_signals → pre-load knowledge → run specialists → combine → validate → resolve conflicts → persist → return. Handle edge cases: no signals, no flying laps, LLM errors
- [ ] T019 [US1] Write tests for analyze_with_engineer() in `backend/tests/engineer/test_integration.py` using TestModel: session with balance signals only → only balance agent runs, session with no signals → empty response, session with no flying laps → insufficient data response (~5 tests)
- [ ] T020 [US1] Write tests for _combine_results() and _build_user_prompt() in `backend/tests/engineer/test_agents.py`: multiple specialist results merged correctly, summary built from domain summaries, signals_addressed populated (~4 tests)

**Checkpoint**: Core analysis pipeline works end-to-end with mocked LLM. US1 acceptance scenarios verified.

---

## Phase 4: User Story 2 — Domain-Specific Specialist Routing (Priority: P1)

**Goal**: Verify that each specialist agent only runs when its domain signals are present, and each produces domain-appropriate output

**Independent Test**: Provide SessionSummaries with signals from different domains → verify only relevant specialists run and produce domain-specific output

### Implementation for User Story 2

- [ ] T021 [P] [US2] Write system prompt `backend/ac_engineer/engineer/skills/aero.md` — role as aero specialist, domain knowledge (wing angles, ride heights, downforce/drag trade-offs), instructions to propose SetupChanges for aero parameters only
- [ ] T022 [US2] Add aero agent creation in `_build_specialist_agent()` in `backend/ac_engineer/engineer/agents.py` — aero uses same pattern as balance/tyre but with aero skill prompt
- [ ] T023 [US2] Write specialist-specific tests in `backend/tests/engineer/test_agents.py` using TestModel: balance agent with understeer signals, tyre agent with temp signals, aero agent with aero-equipped car, technique agent with consistency signal — each produces domain-appropriate SpecialistResult (~4 tests)
- [ ] T024 [US2] Write routing integration tests in `backend/tests/engineer/test_integration.py`: session with only tyre signals → only tyre specialist runs, session with balance+tyre+consistency → 3 specialists run, car with aero params + balance signal → balance+aero run (~3 tests)

**Checkpoint**: All 4 specialist domains tested independently. Routing verified for all signal combinations.

---

## Phase 5: User Story 3 — Plain-Language Explanations (Priority: P1)

**Goal**: Every SetupChange has non-empty reasoning and expected_effect in driver-friendly language; EngineerResponse has a concise summary

**Independent Test**: Run analysis → verify all reasoning/expected_effect fields are non-empty and reference on-track behavior, not jargon

### Implementation for User Story 3

- [ ] T025 [US3] Refine all skill prompts (`backend/ac_engineer/engineer/skills/balance.md`, `tyre.md`, `aero.md`) with explicit instructions: reasoning MUST reference specific corners/laps from the data, expected_effect MUST describe what the driver will feel on track, avoid engineering jargon, explain trade-offs
- [ ] T026 [US3] Write tests in `backend/tests/engineer/test_agents.py` using FunctionModel that returns SpecialistResults with specific reasoning text — verify EngineerResponse summary is non-empty, all SetupChange.reasoning and expected_effect are non-empty strings (~3 tests)

**Checkpoint**: Educational quality of output verified. US3 acceptance scenarios met.

---

## Phase 6: User Story 4 — Knowledge-Grounded Reasoning (Priority: P2)

**Goal**: Specialist agents consult the vehicle dynamics knowledge base via tool calls when reasoning about setup changes

**Independent Test**: Run analysis with TestModel → verify knowledge search tool was called with relevant queries

### Implementation for User Story 4

- [ ] T027 [US4] Enhance `search_kb` tool in `backend/ac_engineer/engineer/tools.py` to format KnowledgeFragment content as structured text with source attribution (source_file, section_title) so the agent sees where the knowledge comes from
- [ ] T028 [US4] Add pre-loading of knowledge in `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py`: call `get_knowledge_for_signals()` before running specialists, pass fragments via AgentDeps.knowledge_fragments so they're available in system context
- [ ] T029 [US4] Write tests in `backend/tests/engineer/test_tools.py`: search_kb returns formatted fragments with source attribution, pre-loaded knowledge passed correctly in AgentDeps (~3 tests)

**Checkpoint**: Knowledge grounding verified. Agents have access to domain knowledge.

---

## Phase 7: User Story 5 — Parameter-Safe Recommendations (Priority: P2)

**Goal**: All proposed setup changes validated against car's parameter ranges; out-of-range values clamped; missing ranges produce warnings

**Independent Test**: Propose changes exceeding ranges → verify all clamped; propose changes for unknown params → verify warnings included

### Implementation for User Story 5

- [ ] T030 [US5] Add post-validation step in `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py`: after combining specialist results, call `validate_changes(ranges, all_setup_changes)`, update each SetupChange.value_after with clamped values, append warnings to reasoning
- [ ] T031 [US5] Implement conflict resolution in `_combine_results()` or a new `_resolve_conflicts()` in `backend/ac_engineer/engineer/agents.py`: detect same section/parameter from multiple specialists, keep higher-priority domain's change per DOMAIN_PRIORITY, note conflict in explanation
- [ ] T032 [US5] Write tests in `backend/tests/engineer/test_integration.py`: proposed value above max → clamped, proposed value below min → clamped, unknown parameter → warning but included, two specialists change same param → higher priority wins (~4 tests)

**Checkpoint**: Parameter safety verified. No out-of-range values possible in output.

---

## Phase 8: User Story 6 — Persist Analysis Results (Priority: P3)

**Goal**: EngineerResponse is saved to the database after analysis completes

**Independent Test**: Run analysis → query database for recommendation → verify it matches

### Implementation for User Story 6

- [ ] T033 [US6] Wire persistence in `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py`: call `save_recommendation(db_path, session_id, summary, explanation, setup_changes)` before returning EngineerResponse; handle DB errors gracefully (log warning, still return response)
- [ ] T034 [US6] Write tests in `backend/tests/engineer/test_integration.py`: verify recommendation saved after successful analysis, verify response returned even if DB save fails, verify feedback-only response saved with empty changes (~3 tests)

**Checkpoint**: Persistence verified. Recommendations retrievable from database.

---

## Phase 9: User Story 7 — Apply Accepted Recommendations (Priority: P3)

**Goal**: apply_recommendation() orchestrates validation + backup + atomic write + status update in one call

**Independent Test**: Create a recommendation, apply it to a setup file → verify backup exists, values written, DB status "applied"

### Implementation for User Story 7

- [ ] T035 [US7] Implement `apply_recommendation()` in `backend/ac_engineer/engineer/agents.py` per contracts/agents-api.md and research.md R9: load recommendation from DB → read_parameter_ranges → validate_changes → create_backup → apply_changes → update_recommendation_status("applied") → return outcomes. On failure: original file intact, status unchanged
- [ ] T036 [US7] Write tests in `backend/tests/engineer/test_integration.py`: successful apply → backup + values written + status "applied", apply with invalid recommendation_id → ValueError, write failure mid-operation → original intact + status unchanged (~3 tests)

**Checkpoint**: Full write pipeline verified. US7 acceptance scenarios met.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Public API exports, final validation, documentation

- [ ] T037 Update `backend/ac_engineer/engineer/__init__.py` to export Phase 5.3 public API: analyze_with_engineer, apply_recommendation, route_signals, get_model_string, SpecialistResult, AgentDeps, SIGNAL_DOMAINS, DOMAIN_PRIORITY — per contracts/agents-api.md
- [ ] T038 Run full test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) — verify all ~500+ tests pass (464 existing + ~40 new)
- [ ] T039 Validate quickstart.md: verify the usage example from `specs/008-engineer-agents/quickstart.md` is consistent with the implemented API signatures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — core pipeline, MVP
- **US2 (Phase 4)**: Depends on Phase 3 (builds on specialist agent infrastructure)
- **US3 (Phase 5)**: Depends on Phase 3 (refines skill prompts created in US1)
- **US4 (Phase 6)**: Depends on Phase 2 (enhances tools, can parallelize with US3)
- **US5 (Phase 7)**: Depends on Phase 3 (adds validation to combine step)
- **US6 (Phase 8)**: Depends on Phase 3 (adds persistence to orchestrator)
- **US7 (Phase 9)**: Depends on Phase 8 (needs saved recommendations to apply)
- **Polish (Phase 10)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Start after Foundational → delivers MVP
- **US2 (P1)**: After US1 (adds aero specialist, tests routing)
- **US3 (P1)**: After US1 (refines prompt quality)
- **US4 (P2)**: After Foundational (enhances tools); can run in parallel with US3
- **US5 (P2)**: After US1 (adds validation/conflict resolution)
- **US6 (P3)**: After US1 (adds persistence)
- **US7 (P3)**: After US6 (applies persisted recommendations)

### Within Each User Story

- Skill prompts before agent implementation
- Agent functions before integration tests
- Core logic before edge case handling

### Parallel Opportunities

**Within Phase 2**: T006, T007 can run in parallel; T009, T010 can run in parallel
**Within Phase 3**: T012, T013, T014 (skill prompts) can run in parallel
**After Phase 3**: US3, US4, US5, US6 can run in parallel (different concerns)
**Within Phase 4**: T021 (aero prompt) parallel with T023 (tests)

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Parallel: Write all specialist skill prompts
Task T012: "Write balance.md skill prompt"
Task T013: "Write tyre.md skill prompt"
Task T014: "Write technique.md skill prompt"

# Sequential: Agent definitions depend on prompts
Task T015: "Define specialist agents" (after T012-T014)
Task T016: "Build user prompt formatter" (after T015)
Task T017: "Combine specialist results" (after T015)
Task T018: "Implement analyze_with_engineer()" (after T016, T017)

# Sequential: Tests depend on implementation
Task T019: "Integration tests" (after T018)
Task T020: "Unit tests for combine/prompt" (after T017)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T010)
3. Complete Phase 3: User Story 1 (T011–T020)
4. **STOP and VALIDATE**: Run `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v`
5. MVP delivers: analyze a session → get setup recommendations with explanations

### Incremental Delivery

1. Setup + Foundational → routing and tools ready
2. Add US1 → core analysis pipeline (MVP!)
3. Add US2 → all 4 specialist domains with routing tests
4. Add US3 → refined educational explanations
5. Add US4 → knowledge-grounded reasoning
6. Add US5 → parameter validation and conflict resolution
7. Add US6 → database persistence
8. Add US7 → apply recommendations to setup files
9. Polish → exports, full suite validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- All tests use Pydantic AI TestModel or FunctionModel — no real LLM calls
- Total: 39 tasks (4 setup + 6 foundational + 10 US1 + 4 US2 + 2 US3 + 3 US4 + 3 US5 + 2 US6 + 2 US7 + 3 polish)
- Expected new tests: ~40 across test_agents.py, test_tools.py, test_integration.py
