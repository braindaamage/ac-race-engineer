# Research: API Server Infrastructure

**Feature**: 010-api-server-infra
**Date**: 2026-03-05

## R1: FastAPI App Factory + Lifespan Pattern

**Decision**: Use `@asynccontextmanager` lifespan function with `FastAPI(lifespan=...)` for startup/shutdown hooks.

**Rationale**: The `on_event("startup")`/`on_event("shutdown")` decorators are deprecated since FastAPI 0.109+. The lifespan pattern is the current recommended approach — it uses a single async context manager where code before `yield` runs on startup and code after `yield` runs on shutdown. This provides a clean place to initialize and tear down the job manager.

**Alternatives considered**:
- `on_event` decorators: Deprecated, will be removed in future FastAPI versions.
- Middleware-based init: Overly complex for a simple init/teardown lifecycle.

## R2: Job Manager Singleton via app.state

**Decision**: Store the `JobManager` instance on `app.state` during lifespan startup. Inject it into route handlers via a FastAPI `Depends()` function that reads from `request.app.state`.

**Rationale**: FastAPI's `app.state` is the idiomatic place for application-wide singletons. Using `Depends()` keeps handlers testable — tests can override the dependency with a fresh `JobManager` per test. No global mutable state.

**Alternatives considered**:
- Module-level global singleton: Works but harder to isolate in tests, requires manual reset between test cases.
- Dependency injection container (e.g., `dependency-injector`): Overkill for a single shared object.

## R3: WebSocket Job Progress — Poll vs Pub/Sub

**Decision**: Use asyncio Event-based notification. The `JobManager` holds an `asyncio.Event` per job. When job state changes, the event is set. The WebSocket handler awaits the event with a timeout, sends the current state, and resets the event.

**Rationale**: Pure polling with `asyncio.sleep` wastes cycles or introduces latency. A full pub/sub system (Redis, etc.) is overkill for an in-memory, single-process server. `asyncio.Event` provides instant notification with zero overhead — the WebSocket handler wakes up exactly when state changes.

**Alternatives considered**:
- `asyncio.sleep` polling loop: Simple but introduces latency (must sleep between checks) or CPU waste (very short sleep).
- `asyncio.Queue` per subscriber: Works but more complex — must manage one queue per connected client per job, handle cleanup on disconnect.
- External pub/sub (Redis): Requires infrastructure for what is a single-process localhost server.

## R4: CORS Configuration for Localhost

**Decision**: Use FastAPI's `CORSMiddleware` with `allow_origin_regex=r"^https?://localhost(:\d+)?$"` to match any localhost port. Allow all methods and common headers.

**Rationale**: The React dev server runs on a different port than the backend. Using a regex avoids maintaining a list of specific ports. Restricting to localhost prevents unintended access from non-local origins (though this is a desktop-only app, defense in depth is free).

**Alternatives considered**:
- `allow_origins=["*"]`: Too permissive — no reason to allow non-localhost origins.
- Explicit port list: Fragile — React dev server port can change, and the Tauri webview port varies.

## R5: Server Entry Point Design

**Decision**: `server.py` uses `argparse` to parse `--port` (default from `PORT` env var or 57832). Calls `uvicorn.run()` directly (not via CLI). This file is the entry point Tauri will invoke.

**Rationale**: `uvicorn.run()` provides programmatic control over host, port, and shutdown behavior. argparse is stdlib — no extra dependency. Port 57832 is unlikely to conflict with common services (avoids 8000/8080/3000 which dev tools use).

**Alternatives considered**:
- Click/Typer for CLI: Extra dependency for a single `--port` flag.
- `uvicorn` CLI invocation: Less control over startup behavior and harder for Tauri to manage as subprocess.

## R6: Graceful Shutdown Strategy

**Decision**: On lifespan exit (triggered by SIGINT/SIGTERM or uvicorn shutdown), the job manager cancels all running asyncio tasks and waits briefly for them to finish. WebSocket handlers detect cancellation and close connections cleanly.

**Rationale**: Uvicorn handles signal capture and triggers the lifespan exit. The job manager just needs to cancel its tracked tasks. asyncio's cooperative cancellation (via `CancelledError`) is the standard pattern.

**Alternatives considered**:
- Custom signal handlers: Conflicts with uvicorn's own signal handling.
- Fire-and-forget (don't cancel): Risks hanging on shutdown if a job is stuck.

## R7: Job Worker Design — Wrapping Callables as Jobs

**Decision**: The worker accepts an `async Callable` (the actual work function) and a `JobManager` reference. It updates job progress by calling `manager.update_progress(job_id, pct, step)` from within the callable. The worker catches exceptions and marks the job as failed.

**Rationale**: This keeps the job system generic — any async function can become a job. The callable receives a progress callback, making it easy for future phases (6.2-6.5) to report progress from parsing, analysis, or engineer operations.

**Alternatives considered**:
- Background thread pool: Unnecessary complexity — FastAPI is already async, and the heavy operations (parsing, LLM calls) are either CPU-bound (use `run_in_executor`) or already async.
- Celery/RQ/Dramatiq: Designed for distributed systems with external brokers — complete overkill for a localhost desktop app.

## R8: Error Response Format

**Decision**: Uniform JSON envelope: `{"error": {"type": "not_found", "message": "Human-readable message", "detail": {...optional context...}}}`. Register global exception handlers for `HTTPException`, `RequestValidationError`, and a catch-all `Exception` handler.

**Rationale**: A single envelope shape means the frontend can parse errors with one code path. The `type` field allows programmatic branching (show different UI for "not_found" vs "validation_error"). The `detail` field carries structured context (e.g., which fields failed validation) without cluttering the message.

**Alternatives considered**:
- RFC 7807 Problem Details: Good standard but more fields than needed for a desktop app with a single consumer.
- Flat JSON (no nesting): Mixes error fields with potential future response fields.

## R9: Dependencies to Install

**Decision**: Install `fastapi` and `httpx` into the conda env. `uvicorn` is already installed (0.41.0). `starlette` comes with FastAPI. `httpx` is needed for `AsyncClient` in tests.

**Rationale**: Minimal additions to the environment. FastAPI is the only new runtime dependency. httpx is test-only but commonly installed alongside FastAPI for testing.

**Alternatives considered**:
- `requests` for testing: Doesn't support async or WebSocket testing with Starlette's `TestClient`.
- `aiohttp`: Different ecosystem — FastAPI tests are best served by httpx + starlette TestClient.
