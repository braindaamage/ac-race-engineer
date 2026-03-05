"""Storage module — SQLite persistence for sessions, recommendations, and messages."""

from .db import init_db
from .messages import clear_messages, get_messages, save_message
from .models import (
    VALID_SESSION_STATES,
    Message,
    Recommendation,
    SessionRecord,
    SetupChange,
    SyncResult,
)
from .recommendations import (
    get_recommendations,
    save_recommendation,
    update_recommendation_status,
)
from .sessions import (
    delete_session,
    get_session,
    list_sessions,
    save_session,
    session_exists,
    update_session_state,
)

__all__ = [
    "Message",
    "Recommendation",
    "SessionRecord",
    "SetupChange",
    "SyncResult",
    "VALID_SESSION_STATES",
    "clear_messages",
    "delete_session",
    "get_messages",
    "get_recommendations",
    "get_session",
    "init_db",
    "list_sessions",
    "save_message",
    "save_recommendation",
    "save_session",
    "session_exists",
    "update_recommendation_status",
    "update_session_state",
]
