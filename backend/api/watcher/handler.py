"""Watchdog event handler with debounce for session file pairs."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from api.watcher.scanner import register_single_pair

logger = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 2.0
CHECK_INTERVAL = 1.0


class SessionEventHandler(FileSystemEventHandler):
    """Tracks file modification timestamps and registers stabilized pairs."""

    def __init__(self, sessions_dir: Path, db_path: Path) -> None:
        super().__init__()
        self._sessions_dir = sessions_dir
        self._db_path = db_path
        self._pending: dict[str, float] = {}  # base_name -> last_seen_timestamp
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._stopped = False

    def _is_relevant(self, path: str) -> bool:
        return path.endswith(".csv") or path.endswith(".meta.json")

    def _base_name(self, path: str) -> str:
        name = Path(path).name
        if name.endswith(".meta.json"):
            return name[: -len(".meta.json")]
        if name.endswith(".csv"):
            return name[: -len(".csv")]
        return name

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_relevant(event.src_path):
            self._track(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_relevant(event.src_path):
            self._track(event.src_path)

    def _track(self, path: str) -> None:
        base = self._base_name(path)
        with self._lock:
            self._pending[base] = time.monotonic()
            self._schedule_check()

    def _schedule_check(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        if not self._stopped:
            self._timer = threading.Timer(CHECK_INTERVAL, self._check_stabilized)
            self._timer.daemon = True
            self._timer.start()

    def _check_stabilized(self) -> None:
        now = time.monotonic()
        to_process: list[str] = []

        with self._lock:
            stabilized = [
                name
                for name, ts in self._pending.items()
                if now - ts >= DEBOUNCE_SECONDS
            ]
            for name in stabilized:
                del self._pending[name]
                to_process.append(name)

            # Reschedule if there are still pending items
            if self._pending and not self._stopped:
                self._schedule_check()

        for name in to_process:
            csv_path = self._sessions_dir / f"{name}.csv"
            meta_path = self._sessions_dir / f"{name}.meta.json"
            if csv_path.exists() and meta_path.exists():
                try:
                    registered = register_single_pair(csv_path, meta_path, self._db_path)
                    if registered:
                        logger.info("Auto-discovered session: %s", name)
                except Exception:
                    logger.exception("Failed to register session: %s", name)

    def stop(self) -> None:
        self._stopped = True
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
