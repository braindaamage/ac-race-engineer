# Research: Analysis Endpoints

**Feature**: 012-analysis-endpoints | **Date**: 2026-03-05

## R1: AnalyzedSession Cache Format

**Decision**: Serialize AnalyzedSession as a single JSON file using Pydantic v2's `model_dump(mode="json")` and `model_validate()`.

**Rationale**: AnalyzedSession is a Pydantic v2 model with well-defined serialization. JSON is human-readable, debuggable, and sufficient for the data sizes involved (a 50-lap session produces ~200KB of JSON). The parsed intermediate is already cached as Parquet + JSON by `ac_engineer.parser.cache`; adding another Parquet file for analyzed results adds complexity with no performance benefit since metric queries only read specific fields.

**Alternatives considered**:
- **Parquet for analyzed results**: More compact but AnalyzedSession is deeply nested (laps → corners → sub-metrics) which maps poorly to columnar format. Serialization/deserialization complexity would be high.
- **Pickle**: Fast but not portable, not human-readable, and has security concerns with untrusted data.
- **MessagePack/CBOR**: Faster than JSON but adds a dependency and loses human readability for minimal gain at these data sizes.

## R2: Cache Directory Layout

**Decision**: Store cache files in `{sessions_dir}/{session_id}/` — the same directory structure used by session discovery. The analyzed results file is named `analyzed.json`.

**Rationale**: Keeps all session data together. The parser cache (`save_session`) creates `telemetry.parquet` and `session.json` in the same directory. Adding `analyzed.json` alongside them is natural. The session_id is already used as the directory name by convention.

**Alternatives considered**:
- **Separate cache directory** (e.g., `data/cache/`): Splits session data across two locations, making cleanup harder.
- **Filename with session_id prefix** (`{session_id}.analyzed.json`): Redundant since the directory is already per-session.

## R3: Active Job Tracking for Duplicate Prevention

**Decision**: Maintain a `dict[str, str]` mapping `session_id → job_id` on `app.state.active_processing_jobs`. Entries are added when a processing job starts and removed when it completes or fails (via a cleanup callback in the pipeline).

**Rationale**: Simple in-memory tracking is sufficient for a single-user, single-server application. No need for database-level locking or distributed coordination. The dict is checked atomically in the route handler before creating a new job.

**Alternatives considered**:
- **Database-level lock column**: Adds schema complexity and requires cleanup on server crash. Overkill for single-user.
- **Check JobManager for running jobs of same type**: JobManager doesn't index by session_id, so this would require iterating all jobs.

## R4: Progress Step Granularity

**Decision**: Report 6 progress steps during processing:
1. Parsing CSV + meta.json (0% → 30%)
2. Segmenting laps (30% → 50%) — reported after parse_session completes, since the parser handles segmentation internally
3. Detecting corners (50% → 60%)
4. Analyzing metrics (60% → 85%)
5. Caching results (85% → 95%)
6. Finalizing (95% → 100%)

**Rationale**: The parser and analyzer are atomic functions — we can't inject progress callbacks into their internals without modifying them (which is out of scope). Progress is reported at the boundaries between pipeline stages. The percentages are weighted by typical execution time: parsing is the most I/O-heavy step (CSV reading), analysis is the most CPU-heavy.

**Note**: Steps 1-3 (parsing, segmenting, detecting corners) all happen inside `parse_session()` — a single call. Progress for these is reported before and after the call, with the intermediate step reported based on timing. In practice, the implementation reports "Parsing session..." at 0%, then "Analysis running..." at 40% after parse_session returns, then "Caching results..." at 85% after analyze_session returns. The fine-grained step names (laps segmented, corners detected) may be simplified if they can't be observed individually.

**Alternatives considered**:
- **Modify parser/analyzer to accept progress callbacks**: Would give finer granularity but violates the constraint of not modifying existing packages.
- **Single progress jump (0 → 100)**: Poor UX — user sees no intermediate feedback.

## R5: Corner Aggregation Strategy

**Decision**: Aggregate corner metrics across flying laps at query time in `serializers.py`. For each corner number, compute mean values of apex_speed_kmh, understeer_ratio, and trail_braking_intensity across all flying laps that contain that corner.

**Rationale**: The analyzer stores per-lap-per-corner metrics in AnalyzedLap.corners. Aggregation is a lightweight computation (simple averages over a small number of laps) that doesn't warrant pre-computation or caching. Computing at query time ensures the aggregation always reflects the full cached data.

**Alternatives considered**:
- **Pre-compute during processing and cache**: Adds complexity to the cache format for negligible performance gain. Aggregating ~50 laps × ~20 corners is sub-millisecond.
- **Store aggregated metrics in SQLite**: Adds schema complexity and denormalization. Not worth it for read-only computed data.

## R6: Pipeline Error Handling

**Decision**: Wrap the pipeline in a try/except that catches all exceptions. On failure, the job is marked as failed via JobManager, the active processing job entry is cleaned up, and the session state is NOT advanced. If the session was previously "analyzed" (re-processing), the state remains "analyzed" — the old cache is preserved.

**Rationale**: The parser and analyzer can raise various exceptions (FileNotFoundError for missing files, ValueError for malformed data, pandas errors for corrupt CSVs). All should result in a failed job with a descriptive error message. The session state should only advance on success.

**Alternatives considered**:
- **Partial state advancement** (e.g., "parsed" after parse_session succeeds but before analyze_session): Adds a visible intermediate state that the user can't do anything with. Simpler to keep it atomic: either fully analyzed or not.

## R7: Async vs Sync Pipeline Execution

**Decision**: The pipeline callable is async (matching the job system's `run_job` signature) but runs the CPU-bound parser/analyzer in a thread pool via `asyncio.to_thread()`. This prevents blocking the event loop during parsing/analysis.

**Rationale**: `parse_session()` and `analyze_session()` are synchronous, CPU-bound functions that can take several seconds. Running them directly in an async function would block the FastAPI event loop, preventing progress updates from being sent via WebSocket. Using `asyncio.to_thread()` offloads the work while keeping the async job tracking operational.

**Alternatives considered**:
- **Run synchronously in the async function**: Blocks the event loop, preventing WebSocket progress updates during processing.
- **Use multiprocessing**: Overkill for single-user app, adds complexity with process communication.
