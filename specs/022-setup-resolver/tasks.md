# Tasks: Tiered Setup Parameter Resolver

**Input**: Design documents from `/specs/022-setup-resolver/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — project has 1128 existing tests and the plan defines explicit test file paths.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the resolver package structure and shared models used by all user stories.

- [ ] T001 Create resolver package directory structure: `backend/ac_engineer/resolver/__init__.py`, `models.py`, `resolver.py`, `defaults.py`, `cache.py` as empty files with module docstrings
- [ ] T002 Implement resolver models in `backend/ac_engineer/resolver/models.py`: `ResolutionTier` int enum (OPEN_DATA=1, ACD_ARCHIVE=2, SESSION_FALLBACK=3), `ResolvedParameters` Pydantic v2 model (car_name, tier, parameters: dict[str, ParameterRange], has_defaults, resolved_at), `CarStatus` Pydantic v2 model (car_name, status, tier, has_defaults, resolved_at — all optional fields nullable per data-model.md)
- [ ] T003 Add `resolution_tier: int | None = None` and `tier_notice: str = ""` fields to `EngineerResponse` in `backend/ac_engineer/engineer/models.py`; add `resolution_tier: int | None = None` field to `AgentDeps` in the same file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database migration and test fixtures that MUST be complete before any user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add `parameter_cache` table to `_MIGRATIONS` list in `backend/ac_engineer/storage/db.py` using the schema from data-model.md: `car_name TEXT PRIMARY KEY, tier INTEGER NOT NULL CHECK(tier IN (1, 2)), has_defaults INTEGER NOT NULL DEFAULT 0, parameters_json TEXT NOT NULL, resolved_at TEXT NOT NULL`
- [ ] T005 Create test fixtures in `backend/tests/resolver/conftest.py`: `db_path` fixture (tmp_path + init_db), `sample_car_dir` fixture (creates a temp directory tree mimicking `content/cars/<car_name>/data/` with a valid `setup.ini` containing 3-4 sections with MIN/MAX/STEP, plus `suspensions.ini` and `tyres.ini` with matching default values), `sample_acd_car_dir` fixture (creates a temp directory with a `data.acd` archive built using `build_acd()` from `tests/acd_reader/conftest.py` containing `setup.ini` + config files), `sample_session_setup` fixture (returns a dict[str, dict[str, float|str]] matching the session setup fallback format)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Automatic Parameter Resolution During Analysis (Priority: P1) MVP

**Goal**: When a session analysis runs, the system resolves parameter ranges and defaults for the car using the three-tier fallback strategy (open data → ACD decryption → session fallback). The result includes the tier used and a limitation notice for Tier 3.

**Independent Test**: Analyze a session for a car with encrypted data and verify the engineer receives parameter ranges with defaults. Verify Tier 3 responses include a limitation notice.

### Tests for User Story 1

- [ ] T006 [P] [US1] Write tests for default extraction in `backend/tests/resolver/test_defaults.py`: test that `extract_defaults()` reads known default values from `suspensions.ini` (CAMBER, TOE_OUT, SPRING_RATE, damper values), `tyres.ini` (PRESSURE_STATIC), `aero.ini` (WING angles), `drivetrain.ini` (FINAL gear ratio); test that missing config files return None for those defaults; test that malformed config files are handled gracefully (no exception, missing defaults left as None); test corner suffix mapping (LF→FRONT index 0, RF→FRONT index 1, LR→REAR index 0, RR→REAR index 1); test unmapped section names return None default
- [ ] T007 [P] [US1] Write tests for tier evaluation in `backend/tests/resolver/test_resolver.py`: test Tier 1 — car with open `data/setup.ini` returns ranges with defaults and tier=1; test Tier 2 — car with only `data.acd` (standard encryption) returns ranges with defaults and tier=2; test Tier 2 fallthrough — car with `data.acd` using third-party encryption (unreadable output from `read_acd`) falls through silently to Tier 3; test Tier 3 — car with neither open data nor decryptable archive uses session_setup and tier=3; test Tier 3 with no session_setup returns empty parameters and tier=3; test Tier 1 precedence — car with both `data/` folder and `data.acd` uses Tier 1 only (FR-020); test open data folder exists but `setup.ini` missing falls through to Tier 2; test `ac_install_path=None` goes directly to Tier 3; test that `resolve_parameters()` never raises — always returns ResolvedParameters

### Implementation for User Story 1

- [ ] T008 [P] [US1] Implement default extraction mapping and `extract_defaults()` function in `backend/ac_engineer/resolver/defaults.py`: define `DEFAULT_MAPPING` data structure mapping setup.ini section name patterns to (config_filename, ini_section, ini_key) tuples per research.md R-001; implement corner suffix resolution (LF/RF/LR/RR → axle + index); implement `extract_defaults(config_files: dict[str, str], parameter_sections: list[str]) -> dict[str, float | None]` that takes parsed config file contents and a list of setup section names, returns section→default_value mapping; handle missing files/keys gracefully (return None, never raise)
- [ ] T009 [P] [US1] Implement `_resolve_tier1()` private function in `backend/ac_engineer/resolver/resolver.py`: given `ac_install_path` and `car_name`, check if `<ac_install_path>/content/cars/<car_name>/data/setup.ini` exists; if yes, parse it using configparser to extract MIN/MAX/STEP per section (same logic as existing `read_parameter_ranges`); read config files (`suspensions.ini`, `tyres.ini`, `aero.ini`, `drivetrain.ini`, `brakes.ini`) from the same `data/` folder; call `extract_defaults()` to get default values; build and return `dict[str, ParameterRange]` or None if setup.ini missing/malformed
- [ ] T010 [P] [US1] Implement `_resolve_tier2()` private function in `backend/ac_engineer/resolver/resolver.py`: given `ac_install_path` and `car_name`, check if `<ac_install_path>/content/cars/<car_name>/data.acd` exists; if yes, call `read_acd(acd_path, car_name)` from `ac_engineer.acd_reader`; if `result.ok` is False, return None (silent fallthrough per FR-006); extract `setup.ini` bytes from `result.files`, decode UTF-8, parse with configparser for ranges; extract config file bytes from `result.files`, decode, call `extract_defaults()`; build and return `dict[str, ParameterRange]` or None
- [ ] T011 [P] [US1] Implement `_resolve_tier3()` private function in `backend/ac_engineer/resolver/resolver.py`: given `session_setup: dict[str, dict[str, float|str]] | None`, if None return empty result; for each section in session_setup, create a ParameterRange with the current value as both min and max (inferred range), step=1, default_value=None; return `dict[str, ParameterRange]` — consistent with existing fallback behavior. Skip any section whose value is not a numeric type (int or float) — check with `isinstance(value, (int, float))` before creating the ParameterRange; non-numeric values (e.g. strings like 'auto') are omitted silently without raising.
- [ ] T012 [US1] Implement `resolve_parameters()` public function in `backend/ac_engineer/resolver/resolver.py`: orchestrate tiers 1→2→3 in strict order (FR-001, FR-002); build `ResolvedParameters` with the winning tier's data, set `has_defaults` based on whether any parameter has non-null `default_value`; set `resolved_at` to `datetime.now(timezone.utc).isoformat()`; never raise — wrap all tier calls in try/except and fall through on any error (FR-008); signature: `resolve_parameters(ac_install_path: Path | None, car_name: str, db_path: Path, session_setup: dict | None = None) -> ResolvedParameters` (db_path parameter present but unused until US2 adds caching)
- [ ] T013 [US1] Create public API exports in `backend/ac_engineer/resolver/__init__.py`: export `resolve_parameters`, `ResolvedParameters`, `ResolutionTier`, `CarStatus` from submodules; define `__all__` list
- [ ] T014 [US1] Integrate resolver into engineer pipeline in `backend/api/engineer/pipeline.py`: replace `read_parameter_ranges(config.ac_install_path, car_name)` call with `resolve_parameters(config.ac_install_path, car_name, db_path, session_setup=summary.active_setup_parameters)` from `ac_engineer.resolver`; pass `resolved.parameters` to `analyze_with_engineer()` as parameter_ranges; set `resolution_tier=resolved.tier` and `tier_notice` (Tier 3 notice text per FR-017, empty string otherwise) on the `EngineerResponse` returned by `analyze_with_engineer()`; pass `resolution_tier=resolved.tier` into `AgentDeps` construction

**Checkpoint**: At this point, the three-tier resolver is fully functional. Analyzing any car resolves parameters via the best available tier. Tier 3 responses include a limitation notice. No caching yet — every analysis resolves fresh.

---

## Phase 4: User Story 2 — Persistent Caching of Resolved Data (Priority: P2)

**Goal**: Tier 1 and Tier 2 resolution results are persisted in SQLite so subsequent analyses of the same car skip file I/O and decryption. Tier 3 results are never cached.

**Independent Test**: Resolve a car's data, then resolve the same car again and verify the second call returns from cache without filesystem access.

**Depends on**: Phase 3 (US1) — resolver must exist before caching can be added to it.

### Tests for User Story 2

- [ ] T015 [P] [US2] Write tests for cache CRUD in `backend/tests/resolver/test_cache.py`: test `save_to_cache()` persists a ResolvedParameters entry and `get_cached_parameters()` retrieves it with correct car_name, tier, has_defaults, parameters, resolved_at; test `get_cached_parameters()` returns None for non-existent car; test `invalidate_cache()` deletes a single car entry and returns True, returns False for non-existent car; test `invalidate_all_caches()` deletes all entries and returns count; test that saving a second entry for the same car_name replaces the previous one (upsert); test JSON round-trip: save parameters with various float values and verify exact equality after load
- [ ] T016 [P] [US2] Write tests for cache integration in resolver in `backend/tests/resolver/test_resolver.py` (append to existing file): test that `resolve_parameters()` returns cached result when cache hit exists (mock filesystem to verify no I/O); test that `resolve_parameters()` writes to cache after successful Tier 1 resolution; test that `resolve_parameters()` writes to cache after successful Tier 2 resolution; test that Tier 3 results are NOT written to cache; test that cached tier and resolved_at match the original resolution

### Implementation for User Story 2

- [ ] T017 [US2] Implement cache CRUD functions in `backend/ac_engineer/resolver/cache.py`: `get_cached_parameters(db_path, car_name) -> ResolvedParameters | None` — query `parameter_cache` table, deserialize `parameters_json` into dict[str, ParameterRange], build ResolvedParameters; `save_to_cache(db_path, resolved: ResolvedParameters) -> None` — INSERT OR REPLACE into `parameter_cache` with JSON-serialized parameters; `invalidate_cache(db_path, car_name) -> bool` — DELETE WHERE car_name, return whether row was deleted; `invalidate_all_caches(db_path) -> int` — DELETE all rows, return rowcount. Use `_connect` from `ac_engineer.storage.db` for connection management. Follow existing CRUD patterns (try/finally conn.close).
- [ ] T018 [US2] Integrate caching into `resolve_parameters()` in `backend/ac_engineer/resolver/resolver.py`: at the start of `resolve_parameters()`, call `get_cached_parameters(db_path, car_name)` — if cache hit, return it immediately; after a successful Tier 1 or Tier 2 resolution, call `save_to_cache(db_path, resolved)` before returning; do NOT cache Tier 3 results (FR-011); wrap cache operations in try/except so cache failures never block resolution (FR-008)
- [ ] T019 [US2] Add cache exports to `backend/ac_engineer/resolver/__init__.py`: export `get_cached_parameters`, `invalidate_cache`, `invalidate_all_caches` from cache module; update `__all__` list

**Checkpoint**: At this point, resolution results are cached for Tier 1 and Tier 2 cars. Repeated analyses of the same car resolve instantly from cache. Tier 3 always resolves fresh.

---

## Phase 5: User Story 3 — User Visibility and Cache Management (Priority: P3)

**Goal**: Users can see the resolution status of every installed car and invalidate cached data for individual cars or all cars at once, via a "Car Data" section in the Settings view.

**Independent Test**: Navigate to Settings, verify the car list shows installed cars with resolution status, invalidate a car's cache, and confirm next analysis resolves fresh.

**Depends on**: Phase 4 (US2) — cache must exist for the visibility view to display resolution status.

### Tests for User Story 3

- [ ] T020 [P] [US3] Write tests for `list_cars()` in `backend/tests/resolver/test_resolver.py` (append to existing file): test that `list_cars()` returns all subdirectory names from `content/cars/` sorted alphabetically; test that cached cars show status="resolved" with tier and resolved_at; test that uncached cars show status="unresolved" with null tier/resolved_at; test that `ac_install_path=None` raises ValueError; test that missing `content/cars/` directory raises ValueError
- [ ] T021 [P] [US3] Write API route tests in `backend/tests/api/test_cars_route.py`: test `GET /cars` returns car list with resolution status (mock `list_cars`); test `GET /cars` returns 400 with error envelope when AC path not configured; test `GET /cars/{car_name}/parameters` returns cached parameters (mock `get_cached_parameters`); test `GET /cars/{car_name}/parameters` returns 404 with error envelope when not cached; test `DELETE /cars/{car_name}/cache` returns 200 with invalidated=true (mock `invalidate_cache`); test `DELETE /cars/{car_name}/cache` returns 404 when not cached; test `DELETE /cars/cache` returns count of invalidated entries (mock `invalidate_all_caches`); test `DELETE /cars/cache` route is matched before `DELETE /cars/{car_name}/cache` (verify "cache" is not treated as car_name)
- [ ] T022 [P] [US3] Write frontend hook tests in `frontend/tests/hooks/useCars.test.ts`: test `useCars()` fetches car list from `/cars` endpoint; test `invalidateCar` mutation calls `DELETE /cars/{car_name}/cache` and refetches car list; test `invalidateAll` mutation calls `DELETE /cars/cache` and refetches car list; test error state when API returns 400 (AC path not configured); use `vi.mock("../../../src/lib/api")` pattern and `QueryClientProvider` wrapper
- [ ] T023 [P] [US3] Write frontend component tests in `frontend/tests/views/settings/CarDataSection.test.tsx`: test renders car list table with car names and status badges; test resolved cars show tier badge and date; test unresolved cars show "Unresolved" status; test clicking "Invalidate" button for a car calls invalidateCar mutation; test "Invalidate All" button calls invalidateAll mutation; test empty state when no cars; test loading state shows skeleton; test error state when AC path not configured shows message; use `vi.mock` for `useCars` hook

### Implementation for User Story 3

- [ ] T024 [US3] Implement `list_cars(ac_install_path: Path | None, db_path: Path) -> list[CarStatus]` function in `backend/ac_engineer/resolver/resolver.py`: scan `{ac_install_path}/content/cars/` for subdirectories; cross-reference each car name with `parameter_cache` table via `get_cached_parameters(db_path, car_name)`; build `list[CarStatus]` with status="resolved" (tier, has_defaults, resolved_at) or status="unresolved" (nulls); sort alphabetically by car_name; raise `ValueError` if `ac_install_path` is None or `content/cars/` directory doesn't exist
- [ ] T025 [US3] Add `list_cars` export from `resolver.py` to `backend/ac_engineer/resolver/__init__.py` — signature includes `db_path` parameter; update `__all__`
- [ ] T026 [US3] Create API route file `backend/api/routes/cars.py` with Pydantic response models (`CarStatusResponse`, `CarListResponse`, `CarParametersResponse`, `ParameterRangeResponse`, `CacheInvalidateResponse`, `CacheInvalidateAllResponse`, `ErrorDetail`, `CarErrorResponse`) per contracts/api-endpoints.md; implement `GET /cars` — read config for ac_install_path, call `list_cars(ac_install_path, request.app.state.db_path)`, return `CarListResponse`; return 400 with error envelope if ac_install_path not configured or ValueError raised; implement `GET /cars/{car_name}/parameters` — call `get_cached_parameters()`, return `CarParametersResponse` or 404 error envelope; implement `DELETE /cars/cache` — call `invalidate_all_caches()`, return `CacheInvalidateAllResponse` (register BEFORE the parameterized route); implement `DELETE /cars/{car_name}/cache` — call `invalidate_cache()`, return `CacheInvalidateResponse` or 404 error envelope
- [ ] T027 [US3] Register cars router in `backend/api/main.py`: import `router as cars_router` from `api.routes.cars`; add `app.include_router(cars_router, prefix="/cars")`
- [ ] T028 [P] [US3] Add frontend TypeScript types in `frontend/src/lib/types.ts`: `CarStatusRecord` (car_name, status, tier, has_defaults, resolved_at — nullable fields), `CarListResponse` (cars: CarStatusRecord[], total: number), `CarParametersResponse` (car_name, tier, has_defaults, resolved_at, parameters), `CacheInvalidateResponse` (car_name, invalidated), `CacheInvalidateAllResponse` (invalidated_count)
- [ ] T029 [US3] Implement `useCars` hook in `frontend/src/hooks/useCars.ts`: `useQuery` with queryKey `["cars"]` and `queryFn: () => apiGet<CarListResponse>("/cars")` with `staleTime: 60_000`; `useMutation` for `invalidateCar(car_name)` calling `apiDelete(`/cars/${car_name}/cache`)` with `onSuccess` invalidating `["cars"]` query; `useMutation` for `invalidateAll()` calling `apiDelete("/cars/cache")` with `onSuccess` invalidating `["cars"]` query; return `{ cars, isLoading, error, invalidateCar, invalidateAll, isInvalidating }`
- [ ] T030 [P] [US3] Create `frontend/src/views/settings/CarDataSection.css` with styles using `ace-car-data` prefix and design tokens: `.ace-car-data` container, `.ace-car-data__header` (flex row with title + "Invalidate All" button), `.ace-car-data__table` (full-width table), `.ace-car-data__row`, `.ace-car-data__name` (font-mono for car names), `.ace-car-data__status` (badge styling), `.ace-car-data__status--resolved` (green), `.ace-car-data__status--unresolved` (text-secondary), `.ace-car-data__date` (text-secondary, font-size-sm), `.ace-car-data__actions`, `.ace-car-data__empty` (centered message), `.ace-car-data__error` (configuration prompt). Use only design token CSS variables (`--text-primary`, `--text-secondary`, `--bg-surface`, `--border`, `--color-green`, `--font-mono`, etc.)
- [ ] T031 [US3] Implement `CarDataSection` component in `frontend/src/views/settings/CarDataSection.tsx`: import `useCars` hook; render loading state with `Skeleton` component; render error state (AC path not configured) with message and link to AC path field; render empty state if no cars; render table with columns: Car Name, Status (Badge: "Tier 1"/"Tier 2" green for resolved, "Unresolved" secondary), Defaults (yes/no), Last Resolved (formatted date or "—"), Actions (Button "Invalidate" for cached cars); render "Invalidate All" Button in card header (disabled if no cached cars); use `Card` component as wrapper with title="Car Data"; import `CarDataSection.css`
- [ ] T032 [US3] Integrate `CarDataSection` into Settings view in `frontend/src/views/settings/index.tsx`: import `CarDataSection`; add `<CarDataSection />` between the Appearance and Advanced cards unconditionally — the component handles the unconfigured state internally

**Checkpoint**: All user stories are now independently functional. Users can see car resolution status in Settings and manage the cache.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation updates.

- [ ] T033 Update `backend/ac_engineer/resolver/__init__.py` module docstring with a summary of the public API and usage examples
- [ ] T034 Run full backend test suite: `conda run -n ac-race-engineer pytest backend/tests/ -v` — verify all existing tests still pass alongside new resolver tests
- [ ] T035 Run full frontend test suite: `cd frontend && npm run test` — verify all existing tests still pass alongside new CarDataSection and useCars tests
- [ ] T036 Run TypeScript strict check: `cd frontend && npx tsc --noEmit` — verify zero type errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — can start after foundational is complete
- **US2 (Phase 4)**: Depends on Phase 3 — caching wraps the resolver from US1
- **US3 (Phase 5)**: Depends on Phase 4 — visibility requires cache to exist
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Depends on US1 — adds caching to the resolver created in US1
- **US3 (P3)**: Depends on US2 — displays cache status and provides invalidation UI

### Within Each User Story

- Tests written and verified to fail before implementation
- Models/data structures before business logic
- Core logic before integration points
- Backend before frontend (US3)

### Parallel Opportunities

- Within Phase 3 (US1): T006+T007 (tests) in parallel; T008+T009+T010+T011 (tier implementations) in parallel
- Within Phase 4 (US2): T015+T016 (tests) in parallel
- Within Phase 5 (US3): T020+T021+T022+T023 (all tests) in parallel; T028+T030 (types + CSS) in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests first (parallel — different files):
Task T006: "Write tests for default extraction in backend/tests/resolver/test_defaults.py"
Task T007: "Write tests for tier evaluation in backend/tests/resolver/test_resolver.py"

# Launch all tier implementations (parallel — different functions, no deps between them):
Task T008: "Implement default extraction in backend/ac_engineer/resolver/defaults.py"
Task T009: "Implement _resolve_tier1() in backend/ac_engineer/resolver/resolver.py"
Task T010: "Implement _resolve_tier2() in backend/ac_engineer/resolver/resolver.py"
Task T011: "Implement _resolve_tier3() in backend/ac_engineer/resolver/resolver.py"

# Sequential — depends on all tier implementations:
Task T012: "Implement resolve_parameters() orchestrator in resolver.py"
Task T013: "Create public API exports in __init__.py"
Task T014: "Integrate resolver into engineer pipeline in pipeline.py"
```

## Parallel Example: User Story 3

```bash
# Launch all tests (parallel — different files):
Task T020: "Write tests for list_cars() in test_resolver.py"
Task T021: "Write API route tests in test_cars_route.py"
Task T022: "Write frontend hook tests in useCars.test.ts"
Task T023: "Write frontend component tests in CarDataSection.test.tsx"

# Launch frontend assets (parallel — different files):
Task T028: "Add TypeScript types in types.ts"
Task T030: "Create CarDataSection.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005)
3. Complete Phase 3: User Story 1 (T006–T014)
4. **STOP and VALIDATE**: Run `pytest backend/tests/resolver/ -v` — all tests pass. Analyze a session for an encrypted car and verify parameter ranges are resolved at Tier 2.
5. MVP is functional — the engineer now has parameter data for all official cars.

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test resolver independently → MVP complete
3. Add User Story 2 → Verify caching works → Repeated analyses are instant
4. Add User Story 3 → Full visibility UI → Users can manage car data
5. Polish → Full test suite green → Ready for release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 have sequential dependencies on prior stories (cache requires resolver; visibility requires cache)
- The resolver module (`ac_engineer/resolver/`) is a pure Python package with no HTTP imports — testable without the API server
- The API route (`api/routes/cars.py`) is a thin wrapper delegating to resolver functions
- Frontend uses existing patterns: TanStack Query for data, `ace-` CSS prefix, design tokens only
- All error responses use the project's standard error envelope: `{"error": {"type": "...", "message": "...", "detail": null}}`
