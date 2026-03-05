# Research: Config, Knowledge & Packaging Endpoints

**Feature**: 014-config-knowledge-endpoints | **Date**: 2026-03-05

## R1: Config PATCH Semantics — Partial Update via Pydantic

**Decision**: Use a Pydantic model with all `Optional[str]` fields and `model_config = ConfigDict(extra="forbid")`. Extract only provided (non-None) fields via `body.model_dump(exclude_unset=True)` and pass them as kwargs to `update_config()`.

**Rationale**: `exclude_unset=True` distinguishes "field not sent" from "field explicitly set to None". This matches the existing `update_config(**kwargs)` signature which only updates provided keys. FastAPI + Pydantic v2 handle this natively.

**Alternatives considered**:
- JSON Merge Patch (RFC 7396): Overkill for 4 flat fields, adds complexity
- PUT with full replacement: User must re-send all fields, error-prone
- Custom diff format: Non-standard, unnecessary

## R2: Config Response — None-to-Empty-String Coercion

**Decision**: Define a `ConfigResponse` Pydantic model with all `str` fields (never Optional). Build it from `ACConfig` by coercing `None` paths to `""` in the route handler.

**Rationale**: The spec requires "never null for required fields — missing values returned as empty strings". ACConfig stores paths as `Path | None` internally. The coercion happens at the API boundary (route handler), keeping `ac_engineer.config` unchanged.

**Alternatives considered**:
- Modify ACConfig serializer: Violates constraint "existing packages must not be modified"
- Use `response_model_exclude_none=True`: Would omit fields entirely, not return ""

## R3: Config Validation Endpoint Design

**Decision**: `GET /config/validate` reads the current config and checks three conditions: `ac_install_path` exists on disk, `setups_path` exists on disk, `llm_provider` is non-empty. Returns a `ConfigValidationResponse` with per-field booleans and an `is_valid` aggregate.

**Rationale**: Separating validation from update lets the frontend show a pre-flight checklist before running the engineer. Using the existing `ACConfig.is_ac_configured` and `is_setups_configured` computed properties provides the checks without duplicating logic.

**Alternatives considered**:
- Validate on PATCH and return errors: Already happens for invalid providers, but path existence is not a write-time concern (paths may not exist yet when configuring)
- Return detailed error messages per field: Per-field booleans are simpler and let the frontend compose its own messages

## R4: Knowledge Search Result Cap

**Decision**: Cap results at 10 by slicing the list returned from `search_knowledge(query)[:10]`. Return both the capped list and the total unfiltered count.

**Rationale**: `search_knowledge()` already returns results sorted by relevance. Simple slicing at the route level avoids modifying the knowledge package. The total count lets the frontend indicate "showing 10 of 47 results".

**Alternatives considered**:
- Add `limit` parameter to `search_knowledge()`: Violates "existing packages must not be modified"
- Pagination with offset/limit: Over-engineering for a knowledge base with ~50-100 sections total

## R5: Session Knowledge Endpoint — Reusing Existing Machinery

**Decision**: `GET /sessions/{session_id}/knowledge` reuses the same guard pattern from `analysis.py` (`_get_analyzed_session`). It loads the `AnalyzedSession` from cache, runs `detect_signals()` to get signal names, then calls `get_knowledge_for_signals()` to get fragments.

**Rationale**: This mirrors what the engineer does internally but exposes it as a read-only query. Reusing `load_analyzed_session()` from `api.analysis.cache` and `detect_signals()` from `ac_engineer.knowledge.signals` avoids duplication.

**Alternatives considered**:
- Store signals in SQLite at analysis time: Would require schema changes, over-engineering
- Cache fragments alongside analysis results: Adds file I/O complexity for a fast in-memory operation

## R6: Path Resolution for PyInstaller Packaging

**Decision**: Create `api/paths.py` with a `get_data_dir()` function that detects `getattr(sys, 'frozen', False)`. In frozen mode, resolve relative to `sys.executable` parent. In dev mode, resolve relative to `Path(__file__).resolve().parent.parent.parent` (the repo root). Derived paths (`get_db_path()`, `get_config_path()`, `get_sessions_dir()`) all build on `get_data_dir()`.

**Rationale**: PyInstaller sets `sys.frozen = True` and `sys.executable` to the exe path. This is the standard detection pattern. Centralizing path resolution in one module replaces the scattered `Path(__file__).resolve()` patterns in `main.py` and `engineer.py`.

**Alternatives considered**:
- Environment variables for all paths: Requires user to set vars, poor UX for desktop app
- Config file for paths: Circular — need to find the config file first
- `importlib.resources`: Doesn't work well for arbitrary data files with PyInstaller

## R7: PyInstaller Spec File Configuration

**Decision**: Document a `--onedir` build (recommended for faster startup) with a `--onefile` alternative. Include `backend/ac_engineer/knowledge/docs/` and `backend/ac_engineer/engineer/skills/` as data files. Add hidden imports for `pydantic_ai`, `anthropic`, `openai`, `watchdog`.

**Rationale**: `--onedir` avoids the slow temp-extraction penalty of `--onefile`. Knowledge docs and skill prompts are data files read at runtime. LLM provider SDKs are dynamically imported based on config, so PyInstaller can't auto-detect them.

**Alternatives considered**:
- Nuitka: More complex build process, less documentation
- cx_Freeze: Less actively maintained
- Embedding Python in Tauri: Too complex, breaks the subprocess architecture from Principle X

## R8: Existing DEFAULT_CONFIG_PATH Pattern

**Decision**: Replace the `DEFAULT_CONFIG_PATH = Path(__file__).resolve()...` pattern in `engineer.py:40` with `get_config_path()` from the new `paths.py` module. The engineer routes already use `getattr(request.app.state, "config_path", DEFAULT_CONFIG_PATH)` — after this change, `app.state.config_path` will always be set in lifespan, making the fallback unnecessary.

**Rationale**: Centralizing path computation eliminates the scattered `__file__`-relative patterns that break under PyInstaller. Setting paths in lifespan ensures all routes get correct paths regardless of working directory.

**Alternatives considered**:
- Keep fallbacks: Inconsistent, some routes would break in frozen mode while others work
- Set paths via environment variables: Extra config step for Tauri to manage
