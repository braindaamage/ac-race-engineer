"""Session watcher — watchdog Observer lifecycle management."""

from __future__ import annotations

import logging
from pathlib import Path

from watchdog.observers import Observer

from api.watcher.handler import SessionEventHandler

logger = logging.getLogger(__name__)


class SessionWatcher:
    """Start/stop lifecycle for the filesystem watcher."""

    def __init__(self) -> None:
        self._observer: Observer | None = None
        self._handler: SessionEventHandler | None = None

    def start(self, sessions_dir: Path, db_path: Path) -> None:
        """Schedule the handler on the sessions directory and start observing."""
        if not sessions_dir.is_dir():
            logger.warning(
                "Sessions directory does not exist, creating: %s", sessions_dir
            )
            sessions_dir.mkdir(parents=True, exist_ok=True)

        self._handler = SessionEventHandler(sessions_dir, db_path)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(sessions_dir), recursive=False)
        self._observer.daemon = True
        self._observer.start()
        logger.info("Session watcher started on: %s", sessions_dir)

    def stop(self) -> None:
        """Stop the observer and wait for the thread to finish."""
        if self._handler is not None:
            self._handler.stop()
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            logger.info("Session watcher stopped")
