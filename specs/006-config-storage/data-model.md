# Data Model: Config + Storage (Phase 5.1)

**Feature**: 006-config-storage | **Date**: 2026-03-04

## Entities

### 1. ACConfig (Pydantic v2 model — JSON file)

User configuration persisted to `data/config.json`.

| Field | Type | Default | Validation | Description |
| ----- | ---- | ------- | ---------- | ----------- |
| ac_install_path | Path \| None | None | Non-empty when set | Path to Assetto Corsa installation directory |
| setups_path | Path \| None | None | Non-empty when set | Path to setups folder |
| llm_provider | str | "anthropic" | Must be one of: "anthropic", "openai", "gemini" | LLM provider name |
| llm_model | str \| None | None | Non-empty string when set | Specific model within the provider (e.g., "claude-sonnet-4-5") |

**Computed properties** (not stored in JSON):

| Property | Type | Derivation |
| -------- | ---- | ---------- |
| ac_cars_path | Path \| None | `ac_install_path / "content" / "cars"` (None if ac_install_path is None) |
| ac_tracks_path | Path \| None | `ac_install_path / "content" / "tracks"` (None if ac_install_path is None) |
| is_ac_configured | bool | True if ac_install_path is set AND is an existing directory |
| is_setups_configured | bool | True if setups_path is set AND is an existing directory |

**Rules**:
- Path fields are optional — the system operates with reduced functionality when unset.
- `llm_provider` defaults to `"anthropic"` and is validated against a fixed set of allowed values.
- Invalid types on read are silently replaced with defaults (`None` for paths/model, `"anthropic"` for provider).
- Serialized as flat JSON with paths as strings: `{"ac_install_path": "C:\\Games\\AC", "llm_provider": "anthropic", ...}`

### 2. SessionRecord (Pydantic v2 model — SQLite table `sessions`)

Index record for an analyzed telemetry session.

| Field | Type | Constraints | Description |
| ----- | ---- | ----------- | ----------- |
| session_id | str | PK, non-empty | Unique identifier from parser (e.g., filename-derived) |
| car | str | NOT NULL, non-empty | Car name (e.g., "ks_ferrari_488_gt3") |
| track | str | NOT NULL, non-empty | Track name (e.g., "monza") |
| session_date | str | NOT NULL, ISO 8601 | Date/time of the session |
| lap_count | int | NOT NULL, >= 0 | Number of laps in the session |
| best_lap_time | float \| None | >= 0 when set | Best lap time in seconds (None if no valid laps) |

**Rules**:
- `session_id` is provided by the caller (from parser metadata), not auto-generated.
- Duplicate `session_id` performs an upsert (updates existing record if session_id already exists, inserts if not).
- Default ordering: `session_date DESC`.

### 3. Recommendation (Pydantic v2 model — SQLite table `recommendations`)

A setup change suggestion from the AI engineer.

| Field | Type | Constraints | Description |
| ----- | ---- | ----------- | ----------- |
| recommendation_id | str | PK, UUID4 hex | Auto-generated unique identifier |
| session_id | str | FK → sessions, NOT NULL | Session this recommendation belongs to |
| status | str | NOT NULL, one of: "proposed", "applied", "rejected" | Current decision status |
| summary | str | NOT NULL | Human-readable summary of the recommendation |
| created_at | str | NOT NULL, ISO 8601 | Timestamp when the recommendation was created |

**State transitions**: `proposed` → `applied` | `proposed` → `rejected`. No other transitions allowed.

### 4. SetupChange (Pydantic v2 model — SQLite table `setup_changes`)

A single parameter modification within a recommendation.

| Field | Type | Constraints | Description |
| ----- | ---- | ----------- | ----------- |
| change_id | str | PK, UUID4 hex | Auto-generated unique identifier |
| recommendation_id | str | FK → recommendations, NOT NULL | Parent recommendation |
| section | str | NOT NULL, non-empty | Setup file section (e.g., "TYRES", "SUSPENSION") |
| parameter | str | NOT NULL, non-empty | Parameter name (e.g., "PRESSURE_LF") |
| old_value | str | NOT NULL | Previous value as string |
| new_value | str | NOT NULL | New value as string |
| reasoning | str | NOT NULL | Why this change was recommended |

**Rules**:
- Values stored as strings to accommodate any parameter type (int, float, string).
- Cascading delete: when a recommendation is deleted, its setup_changes are deleted.

### 5. Message (Pydantic v2 model — SQLite table `messages`)

A conversation turn between user and AI engineer.

| Field | Type | Constraints | Description |
| ----- | ---- | ----------- | ----------- |
| message_id | str | PK, UUID4 hex | Auto-generated unique identifier |
| session_id | str | FK → sessions, NOT NULL | Session this conversation belongs to |
| role | str | NOT NULL, one of: "user", "assistant" | Who sent the message |
| content | str | NOT NULL | Message text |
| created_at | str | NOT NULL, ISO 8601 | Timestamp when the message was created |

**Rules**:
- Chronological ordering: `created_at ASC`.
- Clear conversation = `DELETE FROM messages WHERE session_id = ?`.

## Entity Relationships

```
ACConfig (JSON file — standalone, no relationships)

SessionRecord 1──*  Recommendation 1──*  SetupChange
      │
      └──────────*  Message
```

- A session has zero or more recommendations.
- A recommendation has one or more setup changes.
- A session has zero or more messages.
- Deleting a session cascades to its recommendations (which cascade to setup_changes) and messages.

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    car          TEXT NOT NULL,
    track        TEXT NOT NULL,
    session_date TEXT NOT NULL,
    lap_count    INTEGER NOT NULL,
    best_lap_time REAL
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    status            TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed', 'applied', 'rejected')),
    summary           TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS setup_changes (
    change_id         TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
    section           TEXT NOT NULL,
    parameter         TEXT NOT NULL,
    old_value         TEXT NOT NULL,
    new_value         TEXT NOT NULL,
    reasoning         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```
