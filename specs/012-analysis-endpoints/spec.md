# Feature Specification: Analysis Endpoints

**Feature Branch**: `012-analysis-endpoints`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Build the Analysis endpoints for AC Race Engineer (Phase 6.3) — connect the parser+analyzer pipeline to the API with a job-based processing endpoint and synchronous metric query endpoints."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process a Session (Priority: P1)

The user opens the desktop app, sees a list of discovered sessions, selects one, and clicks "Process". The backend kicks off the full parse+analyze pipeline as a background job. The user watches a progress indicator update in real time (parsing started, laps segmented, corners detected, analysis running, metrics computed, done). When the job completes, the session state changes from "discovered" to "analyzed" and the cached results are stored to disk alongside the original files.

**Why this priority**: Without processing, no metrics are available. This is the gateway to all other stories.

**Independent Test**: Can be fully tested by triggering processing on a discovered session and verifying the state advances to "analyzed" with cached Parquet+JSON files on disk.

**Acceptance Scenarios**:

1. **Given** a session in "discovered" state, **When** the user triggers processing, **Then** a background job is created and the session state advances to "analyzed" upon completion.
2. **Given** processing is in progress, **When** the user checks progress, **Then** they see real-time step descriptions and a percentage between 0 and 100.
3. **Given** processing completes, **When** the user inspects the session directory, **Then** cached analysis results (Parquet + JSON) exist alongside the original CSV and meta.json.
4. **Given** a session already in "analyzed" state, **When** the user triggers processing again, **Then** the pipeline re-runs and overwrites the existing cache (idempotent).
5. **Given** a session whose CSV or meta.json is missing, **When** the user triggers processing, **Then** the job fails with a clear error message identifying which file is missing.
6. **Given** a session is already being processed (job running), **When** the user triggers processing again, **Then** the system rejects the request indicating a job is already in progress.

---

### User Story 2 - Explore Lap Metrics (Priority: P2)

After processing, the user navigates to the session detail view and sees a list of all laps with summary metrics (lap time, classification, average tyre temps, peak G-force, driver input percentages). They click on a specific lap to see the full detailed breakdown across all 7 metric groups: timing, tyres, grip, driver inputs, speed, fuel, and suspension.

**Why this priority**: Lap-level metrics are the most commonly viewed data and the foundation for understanding session performance.

**Independent Test**: Can be tested by processing a session first, then querying the lap list and individual lap detail endpoints, verifying all metric fields are populated.

**Acceptance Scenarios**:

1. **Given** an analyzed session, **When** the user requests lap metrics, **Then** all laps are returned with summary-level fields (lap time, classification, tyre temps, peak G, driver inputs).
2. **Given** an analyzed session, **When** the user requests detail for a specific lap, **Then** all 7 metric groups are returned with their full sub-fields.
3. **Given** a lap number that does not exist in the session, **When** the user requests its detail, **Then** a not-found error is returned.
4. **Given** a session that has not been analyzed yet, **When** the user requests lap metrics, **Then** a conflict error is returned indicating the session must be processed first.

---

### User Story 3 - Explore Corner Metrics (Priority: P3)

The user wants to understand their corner-by-corner performance. They view a list of all detected corners with aggregated metrics across flying laps (average apex speed, understeer ratio, trail braking intensity). They can also drill into a specific corner to see per-lap breakdowns.

**Why this priority**: Corner analysis provides actionable insights but depends on lap metrics being available first.

**Independent Test**: Can be tested by querying the corner list and corner detail endpoints on an analyzed session, verifying aggregated and per-lap corner data.

**Acceptance Scenarios**:

1. **Given** an analyzed session, **When** the user requests corner metrics, **Then** all detected corners are returned with aggregated metrics across flying laps.
2. **Given** an analyzed session, **When** the user requests detail for a specific corner, **Then** per-lap metrics for that corner are returned.
3. **Given** a corner number that does not exist, **When** the user requests its detail, **Then** a not-found error is returned.
4. **Given** a session with no detected corners, **When** the user requests corner metrics, **Then** an empty list is returned.

---

### User Story 4 - View Stint Trends and Comparisons (Priority: P4)

The user wants to understand how their performance evolved across stints. They view a list of stints with aggregated metrics and trend data (lap time slope, tyre temp slope, fuel consumption slope). They can also compare two stints to see the setup parameter differences and metric deltas between them.

**Why this priority**: Stint analysis is valuable for multi-stint sessions but is less frequently used than lap/corner data.

**Independent Test**: Can be tested by querying stint list and stint comparison endpoints on an analyzed session with multiple stints.

**Acceptance Scenarios**:

1. **Given** an analyzed session, **When** the user requests stint metrics, **Then** all stints are returned with aggregated metrics and trend data.
2. **Given** an analyzed session with multiple stints, **When** the user compares two stints by index, **Then** setup parameter deltas and metric deltas are returned.
3. **Given** a stint index that does not exist, **When** the user requests a comparison with it, **Then** a not-found error is returned.
4. **Given** a single-stint session, **When** the user requests stint comparisons, **Then** an empty comparisons list is available and comparing non-existent indices returns an error.

---

### User Story 5 - View Session Consistency (Priority: P5)

The user wants a high-level view of their driving consistency. They access a single endpoint that returns session-wide consistency metrics: lap time standard deviation, best and worst lap times, lap time trend slope, and corner-by-corner variance.

**Why this priority**: Consistency is a summary view that enhances the overall picture but is not essential for core analysis workflows.

**Independent Test**: Can be tested by querying the consistency endpoint on an analyzed session and verifying all consistency fields are populated.

**Acceptance Scenarios**:

1. **Given** an analyzed session with flying laps, **When** the user requests consistency metrics, **Then** lap time stddev, best/worst lap time, trend slope, and corner consistency data are returned.
2. **Given** a session that has not been analyzed, **When** the user requests consistency, **Then** a conflict error is returned.

---

### Edge Cases

- What happens when a session has zero flying laps? Processing should still succeed and produce an analyzed session with empty or zero-valued consistency metrics.
- What happens when the parser encounters malformed CSV data? The processing job should fail with a descriptive error rather than crashing silently.
- What happens when multiple users trigger processing on the same session simultaneously? The second request is rejected with a conflict error (job already running).
- What happens when the disk is full and caching fails? The processing job fails with an error and the session state does not advance to "analyzed".
- What happens when the cached results on disk are corrupted or manually deleted? Metric queries fail gracefully, and the user can re-trigger processing to regenerate the cache.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a processing endpoint that runs the full parse+analyze pipeline as a tracked background job.
- **FR-002**: System MUST report real-time progress during processing with step descriptions (parsing started, laps segmented, corners detected, analysis running, metrics computed, done) and a percentage from 0 to 100.
- **FR-003**: System MUST advance the session state from "discovered" to "analyzed" upon successful processing completion.
- **FR-004**: System MUST cache analysis results (Parquet + JSON format) in a subdirectory alongside the original session files.
- **FR-005**: System MUST support idempotent processing — re-processing an already-analyzed session re-runs the pipeline and overwrites the cache.
- **FR-006**: System MUST reject processing requests when a job is already running for the same session, returning a conflict error.
- **FR-007**: System MUST provide a lap list endpoint returning all laps with summary metrics (lap time, classification, tyre temps, peak G, driver inputs).
- **FR-008**: System MUST provide a lap detail endpoint returning the full 7-group metric breakdown for a single lap.
- **FR-009**: System MUST provide a corner list endpoint returning all corners with aggregated metrics across flying laps.
- **FR-010**: System MUST provide a corner detail endpoint returning per-lap metrics for a specific corner.
- **FR-011**: System MUST provide a stint list endpoint returning all stints with aggregated metrics and trend data.
- **FR-012**: System MUST provide a stint comparison endpoint that accepts two stint indices and returns setup parameter deltas and metric deltas.
- **FR-013**: System MUST provide a consistency endpoint returning session-wide consistency metrics.
- **FR-014**: All metric endpoints MUST return a not-found error if the session does not exist.
- **FR-015**: All metric endpoints MUST return a conflict error if the session has not been analyzed yet (state is "discovered" or "parsed").
- **FR-016**: All metric endpoints MUST load results from the cached files — they MUST NOT re-run the pipeline.
- **FR-017**: System MUST fail the processing job with a clear error message if the CSV or meta.json files are missing.
- **FR-018**: Lap and corner detail endpoints MUST return a not-found error if the requested lap number or corner number does not exist in the session.

### Key Entities

- **Processing Job**: A background operation that runs the parse+analyze pipeline for a specific session. Tracked by the existing job system with progress updates.
- **Cached Analysis**: The on-disk Parquet + JSON representation of an AnalyzedSession, stored alongside the original session files and loaded by all metric query endpoints.
- **Session State**: Lifecycle state stored in SQLite (discovered → parsed → analyzed → engineered). Processing advances from discovered to analyzed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A discovered session can be fully processed (parsed + analyzed + cached) in under 10 seconds for a typical 20-lap session.
- **SC-002**: Progress updates are delivered at least 5 times during a typical processing job, giving the user continuous feedback.
- **SC-003**: All metric query endpoints return results in under 500 milliseconds when loading from cache.
- **SC-004**: Re-processing an already-analyzed session produces identical results and the session remains in the "analyzed" state.
- **SC-005**: 100% of metric endpoints correctly reject requests for non-existent or not-yet-analyzed sessions with appropriate error codes.
- **SC-006**: The processing pipeline handles sessions from any car (vanilla or modded) without hardcoded car-specific logic.

## Assumptions

- The existing parser (`parse_session`) and analyzer (`analyze_session`) functions are stable and well-tested (530+ tests). This phase wraps them in API endpoints without modifying their internals.
- The existing job system (Phase 6.1) handles background task execution, progress tracking via WebSocket, and job lifecycle management. This phase creates jobs through that system.
- The existing session discovery (Phase 6.2) populates sessions in SQLite with `csv_path` and `meta_path` fields that point to the actual files on disk.
- The cache format uses the existing `save_session` for the parsed intermediate and a new JSON serialization for the analyzed results, both stored in the same session subdirectory.
- The `analyzed` state in the session lifecycle is a prerequisite for all metric query endpoints. The `parsed` intermediate state is an internal detail of the processing pipeline, not exposed to the user.
- Corner aggregation across flying laps (for the corner list endpoint) is computed at query time from the cached per-lap corner metrics, as the analyzer stores metrics per-lap-per-corner.

## Out of Scope

- LLM or AI engineer operations (Phase 6.4)
- Writing or modifying setup .ini files
- Real-time telemetry streaming — all analysis is post-session
- Frontend UI components — this phase is backend-only
- Modifications to the parser or analyzer internals
