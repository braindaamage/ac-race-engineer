"""Storage module — SQLite persistence for sessions, recommendations, and messages."""

from .db import init_db
from .messages import clear_messages, get_messages, save_message
from .models import Message, Recommendation, SessionRecord, SetupChange
from .recommendations import (
    get_recommendations,
    save_recommendation,
    update_recommendation_status,
)
from .sessions import get_session, list_sessions, save_session

__all__ = [
    "Message",
    "Recommendation",
    "SessionRecord",
    "SetupChange",
    "clear_messages",
    "get_messages",
    "get_recommendations",
    "get_session",
    "init_db",
    "list_sessions",
    "save_message",
    "save_recommendation",
    "save_session",
    "update_recommendation_status",
]
