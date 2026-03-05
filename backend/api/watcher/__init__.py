"""Session file watcher — automatic discovery of new telemetry sessions."""

from api.watcher.observer import SessionWatcher
from api.watcher.scanner import scan_sessions_dir

__all__ = ["SessionWatcher", "scan_sessions_dir"]
