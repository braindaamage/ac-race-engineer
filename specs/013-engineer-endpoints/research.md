# Research: Engineer Endpoints

## R1: Pipeline Callable Pattern

**Decision**: Use `make_*_job()` factory functions that return async callables accepting a progress callback, matching the Phase 6.3 `make_processing_job()` pattern.

**Rationale**: The existing `run_job()` worker expects `Callable[[Callable[[int, str], Awaitable[None]]], Awaitable[Any]]`. Phase 6.3 uses a factory function (`make_processing_job()`) that captures parameters via closure and returns an async `pipeline(update)` function. The `finally` block in the pipeline cleans up `active_jobs`. This is a proven, well-tested pattern.

**Alternatives considered**:
- Class-based jobs: More boilerplate, no benefit for this use case.
- Direct coroutine creation in route handler: Mixes pipeline logic with HTTP concerns (violates Principle IX).

## R2: analyze_with_engineer() Integration

**Decision**: Call `analyze_with_engineer()` directly (it's already async) within the pipeline. Wrap progress updates around it since the function itself doesn't emit progress — the pipeline reports coarse-grained steps.

**Rationale**: `analyze_with_engineer(summary, config, db_path, ac_install_path)` handles the full orchestration internally (route signals → run specialists → combine → validate → persist recommendation). It already saves the recommendation to SQLite. The pipeline wraps this with progress steps and handles state transitions.

**Key insight**: `analyze_with_engineer()` already calls `save_recommendation()` internally (agents.py:458-477). The pipeline does NOT need to save the recommendation separately — it only needs to update session state to "engineered" after the function returns.

**Alternatives considered**:
- Breaking apart `analyze_with_engineer()` to report per-specialist progress: Would require modifying Phase 5 internals (out of scope).
- Running in a thread: Unnecessary — the function is already async.

## R3: Chat LLM Call Design

**Decision**: Build a simple Pydantic AI agent for chat that receives the SessionSummary as system context and the conversation history as user/assistant turns. Use the same `get_model_string(config)` for provider abstraction.

**Rationale**: Chat does not need specialist routing — it's a single conversational agent that answers questions about the session. The system prompt includes the principal skill prompt (`skills/principal.md`) and a formatted SessionSummary. Prior messages from `get_messages()` provide conversation context.

**Implementation detail**: The chat agent uses `Agent(model_string, system_prompt=...).run(user_message, message_history=...)` where `message_history` is built from stored messages. Pydantic AI's `ModelMessage` format supports role-based history.

**Alternatives considered**:
- Direct SDK calls: Forbidden by Principle XI.
- Reusing `analyze_with_engineer()` for chat: Overkill — chat doesn't need specialist routing or setup change tools.
- No session context in chat: Would make responses generic and unhelpful.

## R4: Active Job Tracking for Engineer

**Decision**: Add `app.state.active_engineer_jobs: dict[str, str]` (session_id → job_id) in the lifespan, following the same pattern as `active_processing_jobs`. Engineer jobs and processing jobs are tracked independently.

**Rationale**: A session can be processed and engineered concurrently (unlikely but possible). Separate dicts keep the tracking clean. The 409 conflict guard only fires if another *engineer* job is already running for the same session.

**Note on chat jobs**: Chat jobs do NOT need active job tracking. Multiple chat messages can be sent before previous responses complete — the conversation history ensures ordering via timestamps. The job system tracks individual jobs, but there's no per-session exclusion for chat.

**Alternatives considered**:
- Shared `active_jobs` dict with type prefixes: More complex, no benefit.
- No active job tracking: Would allow duplicate engineer runs consuming LLM tokens.

## R5: Recommendation Status for Apply

**Decision**: The apply endpoint checks the recommendation status from the database. If already "applied", return 409. The existing `apply_recommendation()` function in agents.py handles the full flow (load, validate, backup, write, update status).

**Rationale**: `apply_recommendation()` already calls `update_recommendation_status(db_path, rec_id, "applied")` at the end. The route handler only needs to: (1) verify the recommendation exists, (2) verify it's not already applied, (3) resolve the setup file path, and (4) call `apply_recommendation()`.

**Key detail**: `apply_recommendation()` needs `setup_path`, `db_path`, and optionally `ac_install_path` + `car_name` for range re-validation. The route should resolve `setup_path` from ACConfig.setups_path + the session's car name, or accept it as a request body parameter.

**Decision on setup_path resolution**: Accept `setup_path` as a required field in the request body. The frontend knows which setup file the user wants to modify. The backend validates the path exists before proceeding.

## R6: Serialization Strategy

**Decision**: Create thin API response models in `api/engineer/serializers.py` that wrap the storage models (`Recommendation`, `SetupChange`, `Message`). The engineer's `EngineerResponse` is used internally but not returned directly — recommendations are retrieved from SQLite after being saved.

**Rationale**: The `EngineerResponse` from `analyze_with_engineer()` contains the full AI output, but it's transient. The persisted `Recommendation` + `SetupChange` records in SQLite are the source of truth for the view/apply endpoints. Serializers convert these storage models to API response shapes.

**Alternatives considered**:
- Returning `EngineerResponse` directly from the job result: Would work for the trigger endpoint but not for the view endpoints. Consistency favors always reading from SQLite.
- No serializers (return storage models directly): Storage models don't include all fields the API needs (e.g., `EngineerResponse.driver_feedback` is not persisted in the current schema).

**Important discovery**: The current storage schema does NOT persist `driver_feedback`, `explanation`, `confidence`, or `signals_addressed` from `EngineerResponse`. Only `summary` and `setup_changes` are saved. To serve the full recommendation detail, the engineer job result (the `EngineerResponse`) must be stored in the job's result field and/or the recommendation table must be extended.

**Decision**: Store the full `EngineerResponse` as the job result (via `manager.complete_job(job_id, response.model_dump())`). For the recommendation detail endpoint, return the stored recommendation data (summary + changes) which is what's persisted. Driver feedback and explanation are available in the job result immediately after completion but are not persisted long-term in the current schema. This is acceptable for Phase 6.4 — schema extensions can be added later if needed.

**Revised decision**: Actually, store the full `EngineerResponse` JSON alongside the recommendation by saving it to a file (`{cache_dir}/recommendation_{rec_id}.json`) similar to how analyzed sessions are cached. This preserves the full detail (driver feedback, explanation, confidence, signals) without schema changes. The recommendation detail endpoint loads this file. If the file is missing (older recommendations), fall back to the SQLite-only data.
