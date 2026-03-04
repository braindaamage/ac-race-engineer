# Quickstart: Config + Storage (Phase 5.1)

## Prerequisites

```bash
conda activate ac-race-engineer
# Pydantic v2 should already be installed; no new dependencies needed
```

## Config Module Usage

```python
from pathlib import Path
from ac_engineer.config import ACConfig, read_config, write_config, update_config

config_path = Path("data/config.json")

# Read config (never raises — returns defaults if file missing/corrupt)
config = read_config(config_path)

# Write full config
config = ACConfig(
    ac_install_path="C:\\Games\\Assetto Corsa",
    llm_provider="anthropic",
)
write_config(config_path, config)

# Partial update (only changes specified fields)
updated = update_config(config_path, llm_model="claude-sonnet-4-5-20250514")
print(updated.ac_install_path)  # Still "C:\Games\Assetto Corsa"
print(updated.llm_model)        # "claude-sonnet-4-5-20250514"
```

## Storage Module Usage

```python
from pathlib import Path
from ac_engineer.storage import (
    init_db, save_session, list_sessions, get_session,
    save_recommendation, get_recommendations, update_recommendation_status,
    save_message, get_messages, clear_messages,
    SessionRecord, SetupChange,
)

db_path = Path("data/ac_engineer.db")

# Initialize database (idempotent — safe to call on every startup)
init_db(db_path)

# Save a session
save_session(db_path, SessionRecord(
    session_id="monza_2026-03-04_001",
    car="ks_ferrari_488_gt3",
    track="monza",
    session_date="2026-03-04T14:30:00",
    lap_count=12,
    best_lap_time=108.432,
))

# List sessions (most recent first)
sessions = list_sessions(db_path)
sessions_ferrari = list_sessions(db_path, car="ks_ferrari_488_gt3")

# Save a recommendation with setup changes
rec = save_recommendation(
    db_path,
    session_id="monza_2026-03-04_001",
    summary="Reduce front ARB to address understeer in slow corners",
    changes=[
        SetupChange(
            section="ARB",
            parameter="FRONT",
            old_value="5",
            new_value="3",
            reasoning="High understeer ratio in corners 1, 4, 8 suggests the front is too stiff",
        ),
    ],
)

# Accept/reject recommendations
update_recommendation_status(db_path, rec.recommendation_id, "accepted")

# Conversation messages
msg = save_message(db_path, "monza_2026-03-04_001", "user", "I have understeer in turn 3")
msg = save_message(db_path, "monza_2026-03-04_001", "assistant", "Looking at your telemetry...")
history = get_messages(db_path, "monza_2026-03-04_001")
clear_messages(db_path, "monza_2026-03-04_001")
```

## Running Tests

```bash
conda activate ac-race-engineer

# All tests
pytest backend/tests/ -v

# Config tests only
pytest backend/tests/config/ -v

# Storage tests only
pytest backend/tests/storage/ -v
```

## Public Imports

```python
# Config
from ac_engineer.config import read_config, write_config, update_config, ACConfig

# Storage
from ac_engineer.storage import (
    init_db,
    save_session, list_sessions, get_session,
    save_recommendation, get_recommendations, update_recommendation_status,
    save_message, get_messages, clear_messages,
    SessionRecord, Recommendation, SetupChange, Message,
)
```
