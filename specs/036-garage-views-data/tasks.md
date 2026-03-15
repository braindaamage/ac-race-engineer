# Tasks: Garage Views Data Population

**Input**: Design documents from `/specs/036-garage-views-data/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included — the project has established test suites (pytest backend, Vitest frontend) and the spec references specific test files.

**Organization**: Tasks grouped by user story. US3 (Track Layout Distinction) is foundational — it provides the track_config schema and aggregation queries that US1 and US2 depend on, so it is merged into Phase 2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Schema migration, model updates, test fixtures, and shared types

- [x] T001 Add track_config migration and indexes to `backend/ac_engineer/storage/db.py` — append to _MIGRATIONS: (1) ALTER TABLE sessions ADD COLUMN track_config TEXT NOT NULL DEFAULT '', (2) CREATE INDEX IF NOT EXISTS idx_sessions_car ON sessions(car), (3) CREATE INDEX IF NOT EXISTS idx_sessions_car_track ON sessions(car, track, track_config)
- [x] T002 [P] Add `track_config: str = ""` field to SessionRecord in `backend/ac_engineer/storage/models.py`
- [x] T003 [P] Add frontend types to `frontend/src/lib/types.ts` — add `track_config: string` to SessionRecord, add CarStatsRecord, CarStatsListResponse, TrackStatsRecord, TrackStatsListResponse interfaces per data-model.md
- [x] T004 [P] Create test fixtures directory `backend/tests/resolver/fixtures/` with: (1) a valid ui_car.json (name, brand, class fields), (2) a minimal ui_car.json (name only), (3) a valid ui_track.json (name, country, length fields), (4) a layout-specific ui_track.json, (5) a small badge.png, (6) a small preview.png

---

## Phase 2: Foundational — US3 Track Layout + Aggregation + AC Assets

**Purpose**: Core data layer changes that MUST be complete before US1/US2 views can be built. Covers US3 (Track Layout Distinction) plus shared backend infrastructure.

**⚠️ CRITICAL**: No frontend view work can begin until this phase is complete

### US3 Implementation: Track Layout Persistence (FR-001, FR-004, FR-005)

- [x] T005 [US3] Update scanner to persist track_config — in `backend/api/watcher/scanner.py`, read `track_config` from session metadata dict and pass it to SessionRecord when calling save_session. Default to "" if field is missing.
- [x] T006 [US3] Extend list_sessions() in `backend/ac_engineer/storage/sessions.py` to accept optional `track: str | None = None` and `track_config: str | None = None` parameters. When track is provided, add WHERE clause for track. When both track and track_config are provided, add WHERE clause for both. Existing `car` filter remains unchanged.
- [x] T007 [US3] Update save_session() in `backend/ac_engineer/storage/sessions.py` to include track_config in the INSERT OR REPLACE statement and column list
- [x] T008 [US3] Extend GET /sessions endpoint in `backend/api/routes/sessions.py` to accept optional `track` and `track_config` query params, pass them to list_sessions()

### Aggregation Functions (FR-002, FR-003)

- [x] T009 [P] Implement list_car_stats(db_path) in `backend/ac_engineer/storage/sessions.py` — SELECT car, COUNT(DISTINCT track || char(0) || track_config) as track_count, COUNT(*) as session_count, MAX(session_date) as last_session_date FROM sessions GROUP BY car ORDER BY last_session_date DESC. Return list of dicts.
- [x] T010 [P] Implement list_track_stats(db_path, car) in `backend/ac_engineer/storage/sessions.py` — SELECT track, track_config, COUNT(*) as session_count, MIN(best_lap_time) as best_lap_time, MAX(session_date) as last_session_date FROM sessions WHERE car = ? GROUP BY track, track_config ORDER BY last_session_date DESC. Return list of dicts.

### AC Metadata Reader (FR-006, FR-007, FR-008)

- [x] T011 Create `backend/ac_engineer/resolver/ac_assets.py` with Pydantic models CarInfo(display_name, brand, car_class) and TrackInfo(display_name, country, length_m). Implement: (1) _format_name(raw_id) helper to strip common prefixes (ks_, ac_) and replace underscores with spaces, (2) read_car_info(ac_cars_path, car_name) → CarInfo — parse ui/ui_car.json, extract name→display_name, brand, class→car_class; fallback to _format_name on any error, (3) read_track_info(ac_tracks_path, track_name, track_config="") → TrackInfo — parse ui/ui_track.json or ui/layout_{config}/ui_track.json; extract name→display_name, country, length→length_m (parse "5793 m" string); fallback to _format_name, (4) car_badge_path(ac_cars_path, car_name) → Path | None — return path to ui/badge.png if it exists, (5) track_preview_path(ac_tracks_path, track_name, track_config="") → Path | None — layout-aware preview.png path, (6) _validate_identifier(name) helper rejecting path separators and ".."

### Exports

- [x] T012 Export list_car_stats, list_track_stats from `backend/ac_engineer/storage/__init__.py`
- [x] T013 [P] Export CarInfo, TrackInfo, read_car_info, read_track_info, car_badge_path, track_preview_path from `backend/ac_engineer/resolver/__init__.py`

### Phase 2 Tests

- [x] T014 [P] Write tests for ac_assets reader in `backend/tests/resolver/test_ac_assets.py` — test read_car_info with valid JSON, missing JSON, missing fields; test read_track_info for base layout and layout-specific; test _format_name; test car_badge_path/track_preview_path existence checks; test _validate_identifier rejecting path traversal. Use fixtures from T004.
- [x] T015 [P] Write tests for aggregation and track_config in `backend/tests/storage/test_sessions.py` — test list_car_stats returns correct track_count/session_count/last_date; test list_track_stats groups by track+config; test list_sessions with track/track_config filters; test save_session persists track_config; test backward compatibility (old sessions get "" track_config)

**Checkpoint**: Backend data layer is complete — track_config persisted, aggregation queries working, AC metadata readable. All backend tests pass.

---

## Phase 3: User Story 1 — Browse Cars in Garage (Priority: P1) 🎯 MVP

**Goal**: Driver sees a grid of car cards on Garage Home with real data, search/filter, and navigation to tracks view

**Independent Test**: Load Garage Home with session data for 2+ cars → cards appear with correct stats, badge images, search works, click navigates to tracks

### Backend: API Endpoints

- [x] T016 [US1] Add CarStatsResponse and CarStatsListResponse Pydantic models to `backend/api/routes/sessions.py`. Implement GET /sessions/grouped/cars endpoint: call list_car_stats, read_config for ac_cars_path, enrich each car dict with read_car_info metadata and car_badge_path URL (or null). Return CarStatsListResponse.
- [x] T017 [US1] Add GET /cars/{car_name}/badge endpoint to `backend/api/routes/cars.py` — validate identifier (no path separators), construct path via car_badge_path(), return FileResponse with media_type="image/png" and Cache-Control: max-age=86400, or 404 if not found

### Backend: Tests

- [x] T018 [P] [US1] Write tests for GET /sessions/grouped/cars in `backend/tests/api/test_sessions_routes.py` — test returns correct car list with stats, test enrichment with metadata (mock ac_assets), test with no sessions returns empty list, test badge_url is null when image missing
- [x] T019 [P] [US1] Write tests for GET /cars/{car_name}/badge in `backend/tests/api/test_cars_routes.py` — test returns image when exists, test 404 when missing, test path traversal rejection

### Frontend: Hook

- [x] T020 [US1] Create `frontend/src/hooks/useCarStats.ts` — useQuery wrapping GET /sessions/grouped/cars with queryKey ["car-stats"], staleTime: 60_000. Return { cars: CarStatsRecord[], isLoading, error, refetch }.

### Frontend: Test for Hook

- [x] T021 [US1] Write tests for useCarStats in `frontend/tests/hooks/useCarStats.test.ts` — test successful fetch returns cars array, test loading state, test error handling. Mock apiGet.

### Frontend: GarageView Implementation

- [x] T022 [US1] Replace placeholder in `frontend/src/views/garage/index.tsx` with full implementation: (1) Call useCarStats() hook, (2) Render car cards grid (3 cols on XL, 2 on MD, 1 on SM) using Card component, (3) Each card: badge img from badge_url with onError fallback to fa-car icon, display_name as title, brand + car_class subtitle, track_count + session_count stats, relative time since last_session_date, (4) Search input filtering cars by display_name/brand/car_class (client-side, case-insensitive), (5) Empty state with EmptyState component when no cars, (6) No-results state when search matches nothing, (7) Loading skeleton while fetching, (8) Click card → navigate(`/garage/${car.car_name}/tracks`). Reference prototype: frontend/prototypes/3-Racing Engineering - Garage Ho.html for layout.
- [x] T023 [US1] Create `frontend/src/views/garage/GarageView.css` — styles for ace-garage container, ace-garage-grid (CSS grid responsive cols), ace-car-card (hover border-color transition), ace-car-badge (object-fit cover with placeholder fallback), ace-garage-search, ace-garage-stats. Use only design token custom properties. JetBrains Mono for numeric values (track count, session count, relative time).

### Frontend: GarageView Tests

- [x] T024 [US1] Write tests for GarageView in `frontend/tests/views/garage/GarageView.test.tsx` — test renders car cards with correct data (mock useCarStats), test search filters cards by name/brand/class, test empty state when no sessions, test no-results state when search matches nothing, test click card navigates to /garage/{carId}/tracks, test loading state shows skeleton, test badge image fallback on error. Provide QueryClientProvider wrapper and mock useNavigate.

**Checkpoint**: Garage Home is fully functional. Driver sees cars, can search/filter, clicks through to tracks.

---

## Phase 4: User Story 2 — Browse Tracks for a Car (Priority: P1)

**Goal**: Driver selects a car and sees track cards with stats, images, and navigation to sessions

**Independent Test**: Select a car with sessions on 3+ tracks (including multi-layout) → track cards appear with correct stats, layout suffixes, preview images, click navigates to sessions

### Backend: API Endpoints

- [x] T025 [US2] Add TrackStatsResponse and TrackStatsListResponse Pydantic models to `backend/api/routes/sessions.py`. Implement GET /sessions/grouped/cars/{car_name}/tracks endpoint: call list_car_stats for car aggregate, list_track_stats for track details, enrich with read_car_info + read_track_info metadata and track_preview_path URLs. Return TrackStatsListResponse with car header fields + tracks list.
- [x] T026 [US2] Create `backend/api/routes/tracks.py` with GET /tracks/{track_name}/preview endpoint — accept optional `config` query param, validate identifiers, construct path via track_preview_path(), return FileResponse with detected media type and Cache-Control: max-age=86400, or 404
- [x] T027 [US2] Register tracks router in `backend/api/main.py` — add `app.include_router(tracks_router, prefix="/tracks", tags=["tracks"])`

### Backend: Tests

- [x] T028 [P] [US2] Write tests for GET /sessions/grouped/cars/{car}/tracks in `backend/tests/api/test_sessions_routes.py` — test returns tracks list grouped by track+config, test car header fields present, test empty tracks for unknown car, test preview_url includes ?config= for non-empty config
- [x] T029 [P] [US2] Write tests for GET /tracks/{track_name}/preview in `backend/tests/api/test_tracks_routes.py` — test returns image for base layout, test returns image for specific layout config, test 404 when missing, test path traversal rejection

### Frontend: Hook

- [x] T030 [US2] Create `frontend/src/hooks/useCarTracks.ts` — useQuery wrapping GET /sessions/grouped/cars/{carId}/tracks with queryKey ["car-tracks", carId], staleTime: 60_000, enabled: !!carId. Return { data: TrackStatsListResponse | undefined, isLoading, error }.

### Frontend: Test for Hook

- [x] T031 [US2] Write tests for useCarTracks in `frontend/tests/hooks/useCarTracks.test.ts` — test successful fetch returns tracks data, test disabled when carId empty, test loading state. Mock apiGet.

### Frontend: CarTracksView Implementation

- [x] T032 [US2] Replace placeholder in `frontend/src/views/tracks/index.tsx` with full implementation: (1) Read carId from useParams, (2) Call useCarTracks(carId) hook, (3) Car header section: badge img with fallback, display_name, brand + car_class, aggregate stats (track_count, session_count, relative time), (4) Track cards grid (2 cols on LG, 1 on SM): preview img from preview_url with onError fallback to fa-road icon, display_name (+ " - {track_config}" suffix if non-empty), 3-col stat row (session_count, best_lap_time formatted mm:ss.SSS, length_m formatted as X.Xkm), relative time since last_session_date, (5) Click card → navigate to sessions with config query param: `/garage/${carId}/tracks/${track.track_name}/sessions${track.track_config ? `?config=${track.track_config}` : ""}`, (6) Loading skeleton, (7) Empty state if car has no tracks. Reference prototype: frontend/prototypes/4-Racing Engineering - Car Track.html.
- [x] T033 [US2] Create `frontend/src/views/tracks/CarTracksView.css` — styles for ace-tracks container, ace-car-header (flex row with badge + info), ace-tracks-grid (CSS grid responsive), ace-track-card (hover transition), ace-track-preview (object-fit cover), ace-track-stats (3-col grid). Use design tokens. JetBrains Mono for lap times, lengths, counts.

### Frontend: CarTracksView Tests

- [x] T034 [US2] Write tests for CarTracksView in `frontend/tests/views/tracks/CarTracksView.test.tsx` — test renders car header with correct info, test renders track cards with stats, test layout suffix shown for non-empty track_config, test lap time formatting (seconds → mm:ss.SSS), test click track card navigates with correct URL + config query param, test loading state, test empty state, test preview image fallback. Mock useParams, useNavigate, useCarTracks.

**Checkpoint**: Car Tracks view is fully functional. Full drill-down from Garage Home → Car → Tracks works.

---

## Phase 5: User Story 4 — Human-Readable Names in Breadcrumb (Priority: P2)

**Goal**: Breadcrumb shows display names from AC metadata instead of raw folder identifiers

**Independent Test**: Navigate to Car Tracks for a car with AC metadata → breadcrumb shows "Home / Ferrari 488 GT3" not "Home / ks_ferrari_488_gt3"

### Implementation

- [x] T035 [US4] Update `frontend/src/components/layout/Breadcrumb.tsx` to resolve display names from API query cache. For car segment: check if car-stats or car-tracks query data is in the TanStack Query cache (via queryClient.getQueryData), extract display_name for the matching car_name. For track segment: check car-tracks query data, find the matching track_name+track_config entry, use its display_name (with layout suffix if applicable). Fall back to existing formatCarTrack() when cache has no data. Also read `config` from useSearchParams() when constructing the track breadcrumb segment and sessions link.
- [x] T035b [US4] Update `frontend/tests/components/layout/Breadcrumb.test.tsx` — add tests for display name resolution: (1) when car-stats query data is in the TanStack Query cache, breadcrumb shows display_name instead of raw car identifier, (2) when car-tracks query data is in cache, breadcrumb shows track display_name with layout suffix, (3) when no cache data available, breadcrumb falls back to formatCarTrack formatting, (4) when config search param is present, the sessions breadcrumb link includes ?config= query parameter. Keep all existing breadcrumb tests from Phase 14.1.

**Checkpoint**: Breadcrumb shows human-readable names throughout the hierarchy. Tests verify cache-based resolution and fallback.

---

## Phase 6: User Story 5 — Sessions View Contextual Header (Priority: P2)

**Goal**: Sessions list shows a contextual header with car and track information when navigated from the hierarchy

**Independent Test**: Navigate to sessions for a specific car+track → header shows car badge, car name, track preview, track name, session count, best lap

### Implementation

- [x] T036 [US5] Update `frontend/src/views/sessions/index.tsx`: (1) Read `config` from useSearchParams() and pass to list_sessions API call as track_config filter, (2) Call useCarTracks(carId) to get car+track metadata for the header, (3) Add contextual header section above sessions list: car badge + display name on left, track preview + display name on right, session count + best lap stats. Only show header when carId and trackId are present in route params, (4) Filter sessions by track_config in addition to existing car+track filtering.

### Tests

- [x] T037 [US5] Update `frontend/tests/views/sessions/SessionsView.test.tsx` — add tests for: contextual header renders car/track info when route params present, header not shown when navigated without car/track context, track_config query param read from searchParams, sessions filtered by track_config value.

**Checkpoint**: Sessions view shows contextual header. Full hierarchy works end-to-end: Garage → Car → Track → Sessions.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verification, cleanup, edge cases

- [x] T038 Run full backend test suite: `conda activate ac-race-engineer && pytest backend/tests/ -v` — verify all existing + new tests pass
- [x] T039 Run full frontend test suite: `cd frontend && npm run test` — verify all existing + new tests pass
- [x] T040 Run TypeScript strict check: `cd frontend && npx tsc --noEmit` — verify zero type errors
- [x] T041 Verify edge cases manually: (1) AC install path not configured → views render with fallback names, no images, no errors, (2) modded car without ui_car.json → formatted fallback name shown, (3) empty track_config sessions → grouped under base track name, (4) search with no matches → empty state shown

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 Garage (Phase 3)**: Depends on Phase 2. No dependency on other stories.
- **US2 Tracks (Phase 4)**: Depends on Phase 2. No dependency on US1 (can run in parallel).
- **US4 Breadcrumb (Phase 5)**: Depends on Phase 3 or Phase 4 (needs query cache data from car-stats or car-tracks hooks)
- **US5 Sessions Header (Phase 6)**: Depends on Phase 4 (uses useCarTracks hook)
- **Polish (Phase 7)**: Depends on all phases complete

### User Story Dependencies

- **US3 (P1)**: Foundational — merged into Phase 2, blocks all others
- **US1 (P1)**: After Phase 2 — independent, no cross-story deps
- **US2 (P1)**: After Phase 2 — independent, no cross-story deps (can parallel with US1)
- **US4 (P2)**: After US1 or US2 — needs cached API data for display names
- **US5 (P2)**: After US2 — reuses useCarTracks hook for header data

### Within Each User Story

- Backend models/endpoints before frontend hooks
- Frontend hooks before view implementation
- View implementation before view tests (tests verify rendered output)

### Parallel Opportunities

**Phase 1** (all parallel):
- T001, T002, T003, T004 can run simultaneously (different files)

**Phase 2** (partially parallel):
- T009, T010 (aggregation functions) parallel with each other
- T011 (ac_assets module) parallel with T005-T008 (scanner + sessions changes)
- T014, T015 (tests) parallel after their implementations

**Phase 3 + Phase 4** (cross-story parallel):
- US1 (Phase 3) and US2 (Phase 4) can run entirely in parallel after Phase 2
- Within US1: T018, T019 parallel; T020, T021 parallel
- Within US2: T028, T029 parallel; T030, T031 parallel

---

## Parallel Example: Phases 3 + 4

```bash
# After Phase 2 completes, launch US1 and US2 backend work in parallel:

# US1 backend (parallel):
Task T016: "Add GET /sessions/grouped/cars endpoint in backend/api/routes/sessions.py"
Task T017: "Add GET /cars/{car_name}/badge endpoint in backend/api/routes/cars.py"

# US2 backend (parallel with US1):
Task T025: "Add GET /sessions/grouped/cars/{car}/tracks endpoint in backend/api/routes/sessions.py"
Task T026: "Create tracks.py router with preview endpoint"

# Then US1 + US2 frontend hooks in parallel:
Task T020: "Create useCarStats hook"
Task T030: "Create useCarTracks hook"

# Then US1 + US2 views in parallel:
Task T022: "Implement GarageView"
Task T032: "Implement CarTracksView"
```

---

## Implementation Strategy

### MVP First (Phases 1-3: US3 + US1)

1. Complete Phase 1: Setup (schema, models, types, fixtures)
2. Complete Phase 2: Foundational (track_config + aggregation + ac_assets)
3. Complete Phase 3: US1 — Garage Home with car cards
4. **STOP and VALIDATE**: Garage Home shows real cars with stats, search works, badge images load
5. This delivers the primary entry point of the car-centric navigation

### Incremental Delivery

1. Phase 1 + 2 → Data layer ready
2. + Phase 3 (US1) → Garage Home functional (MVP!)
3. + Phase 4 (US2) → Full drill-down: Garage → Car → Tracks → Sessions
4. + Phase 5 (US4) → Breadcrumb shows display names
5. + Phase 6 (US5) → Sessions view has contextual header
6. + Phase 7 → All tests pass, edge cases verified

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US3 is merged into Phase 2 (Foundational) because it provides schema changes that all other stories depend on
- US1 and US2 are both P1 but can be implemented in parallel
- Frontend views reference HTML prototypes (files 3, 4) for visual style — not pixel-perfect, but matching layout structure
- All image handling uses onError fallback pattern — no broken image indicators
- JetBrains Mono font required for all numeric data (lap times, counts, distances) per constitution Principle XII
