# Contract: Storage Module Public API

**Module**: `ac_engineer.storage`
**Exports** (`__all__`): `init_db`, `save_session`, `list_sessions`, `get_session`, `save_recommendation`, `get_recommendations`, `update_recommendation_status`, `save_message`, `get_messages`, `clear_messages`, `SessionRecord`, `Recommendation`, `SetupChange`, `Message`

All functions take `db_path: str | Path` as the first argument — the path to the SQLite database file.

## Database Initialization

### init_db

```python
def init_db(db_path: str | Path) -> None:
```

Create database file and all tables if they don't exist. Idempotent — safe to call multiple times. Enables WAL mode and foreign keys.

## Sessions

### save_session

```python
def save_session(db_path: str | Path, session: SessionRecord) -> None:
```

Upsert a session record. If `session_id` already exists, updates all fields; otherwise inserts a new record.

### list_sessions

```python
def list_sessions(db_path: str | Path, *, car: str | None = None) -> list[SessionRecord]:
```

Return all sessions ordered by `session_date` DESC. If `car` is provided, filter to only that car name.

### get_session

```python
def get_session(db_path: str | Path, session_id: str) -> SessionRecord | None:
```

Return a single session by ID, or `None` if not found.

## Recommendations

### save_recommendation

```python
def save_recommendation(
    db_path: str | Path,
    session_id: str,
    summary: str,
    changes: list[SetupChange],
) -> Recommendation:
```

Create a new recommendation (status="proposed") with its setup changes. Auto-generates `recommendation_id` and `change_id` values. Returns the saved `Recommendation` with all IDs populated.

Raises `ValueError` if `session_id` doesn't exist in sessions table.

### get_recommendations

```python
def get_recommendations(db_path: str | Path, session_id: str) -> list[Recommendation]:
```

Return all recommendations for a session, each with its `changes` list populated. Ordered by `created_at` ASC.

### update_recommendation_status

```python
def update_recommendation_status(
    db_path: str | Path,
    recommendation_id: str,
    status: str,
) -> None:
```

Update a recommendation's status. `status` must be `"applied"` or `"rejected"`. Raises `ValueError` if recommendation not found or status is invalid.

## Messages

### save_message

```python
def save_message(
    db_path: str | Path,
    session_id: str,
    role: str,
    content: str,
) -> Message:
```

Save a new conversation message. Auto-generates `message_id` and `created_at`. `role` must be `"user"` or `"assistant"`. Returns the saved `Message`.

Raises `ValueError` if `session_id` doesn't exist or `role` is invalid.

### get_messages

```python
def get_messages(db_path: str | Path, session_id: str) -> list[Message]:
```

Return all messages for a session ordered by `created_at` ASC.

### clear_messages

```python
def clear_messages(db_path: str | Path, session_id: str) -> int:
```

Delete all messages for a session. Returns the number of deleted messages.

## Models

### SessionRecord

```python
class SessionRecord(BaseModel):
    session_id: str          # Caller-provided unique ID
    car: str                 # Car name
    track: str               # Track name
    session_date: str        # ISO 8601 datetime string
    lap_count: int           # Number of laps (>= 0)
    best_lap_time: float | None = None  # Best lap in seconds
```

### Recommendation

```python
class Recommendation(BaseModel):
    recommendation_id: str   # UUID4 hex (auto-generated)
    session_id: str          # FK to sessions
    status: str              # "proposed" | "applied" | "rejected"
    summary: str             # Human-readable summary
    created_at: str          # ISO 8601 timestamp
    changes: list[SetupChange] = []  # Associated parameter changes
```

### SetupChange

```python
class SetupChange(BaseModel):
    change_id: str = ""      # UUID4 hex (auto-generated on save; empty before save)
    recommendation_id: str = ""  # FK (populated on save)
    section: str             # Setup file section
    parameter: str           # Parameter name
    old_value: str           # Previous value
    new_value: str           # New value
    reasoning: str           # Why this change
```

### Message

```python
class Message(BaseModel):
    message_id: str          # UUID4 hex (auto-generated)
    session_id: str          # FK to sessions
    role: str                # "user" | "assistant"
    content: str             # Message text
    created_at: str          # ISO 8601 timestamp
```
