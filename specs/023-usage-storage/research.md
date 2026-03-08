# Research: Usage Storage

**Feature**: 023-usage-storage | **Date**: 2026-03-08

## R1: Migration Strategy for Two New Tables

**Decision**: Use two `CREATE TABLE IF NOT EXISTS` statements appended to the `_MIGRATIONS` list in `storage/db.py`.

**Rationale**: The existing pattern (used for `parameter_cache`) wraps the full DDL in a single string and relies on `CREATE TABLE IF NOT EXISTS` for idempotency. The `try/except sqlite3.OperationalError: pass` block in `init_db` handles re-runs gracefully. Two new entries (one per table) maintain readability and follow the established convention.

**Alternatives considered**:
- Single migration string with both tables concatenated via `executescript`: Rejected because the existing pattern uses `conn.execute()` for each migration, not `executescript`. Keeping consistency is more important than saving one list entry.
- Using `ALTER TABLE` on existing tables: Not applicable — we are adding entirely new tables, not columns.

## R2: Transaction Scope for save_agent_usage

**Decision**: `save_agent_usage` inserts the `agent_usage` row and all `tool_call_details` rows within a single connection's implicit transaction, calling `conn.commit()` once at the end (matching `save_recommendation` pattern).

**Rationale**: The existing `save_recommendation` function demonstrates the pattern: open connection, insert parent row, loop to insert child rows, commit once, close. This gives atomicity for free — if any insert fails, all are rolled back on connection close without commit.

**Alternatives considered**:
- Explicit `BEGIN`/`COMMIT`: Unnecessary — sqlite3 connections default to implicit transactions. Adding explicit transaction management would diverge from the established pattern.
- Separate `save_agent_usage` and `save_tool_call_detail` functions: Rejected because it forces callers to manage transactions, violating the single-transaction requirement from FR-006.

## R3: Model Design for AgentUsage and ToolCallDetail

**Decision**: Follow the existing Pydantic v2 model style: `BaseModel` subclasses with `Field(...)` for required fields and default empty strings for ID fields that get auto-generated. `ToolCallDetail` is nested inside `AgentUsage.tool_calls: list[ToolCallDetail]` for retrieval, matching how `SetupChange` is nested inside `Recommendation.changes`.

**Rationale**: Direct precedent exists in `Recommendation` (with nested `changes: list[SetupChange]`). This pattern cleanly separates the DB flat structure from the nested Python representation.

**Alternatives considered**:
- Flat models without nesting: Rejected — would force callers to manually join usage records with their tool calls, duplicating work done in `get_recommendations`.

## R4: Domain Validation

**Decision**: Validate `domain` at both the database level (CHECK constraint in DDL) and the Pydantic model level (`Field` with a validator or Literal type). The four valid values are: `balance`, `tyre`, `aero`, `technique`.

**Rationale**: Belt-and-suspenders approach. The CHECK constraint prevents invalid data even if inserted outside of Python. The Pydantic validation provides clear error messages at the application layer.

**Alternatives considered**:
- Database-only CHECK: Insufficient — sqlite3 raises a generic `IntegrityError` without explaining which constraint failed. Pydantic validation gives descriptive errors.
- Python-only validation: Insufficient — does not protect against direct SQL inserts or future non-Python consumers.

## R5: Test Structure

**Decision**: Create `backend/tests/storage/test_usage.py` with test classes mirroring the pattern in `test_recommendations.py`. Use the existing `db_path` fixture from `conftest.py` and a local helper `_setup_recommendation()` that creates the prerequisite session + recommendation chain.

**Rationale**: The test file structure, fixture usage, and helper pattern are well-established across `test_sessions.py`, `test_recommendations.py`, and `test_messages.py`. Following the same pattern ensures consistency and leverages the existing `conftest.py` setup.

**Alternatives considered**:
- Adding tests to existing test files: Rejected — each storage module has its own test file, maintaining clear correspondence.
- New conftest fixtures for recommendations: Not needed — a simple module-level helper (like `_setup_session` in `test_recommendations.py`) is lighter and follows precedent.
