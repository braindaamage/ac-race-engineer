"""Pure session directory scanner — no HTTP coupling."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ac_engineer.storage.models import SessionRecord, SyncResult
from ac_engineer.storage.sessions import save_session, session_exists

logger = logging.getLogger(__name__)


def _extract_session_id(meta_path: Path) -> str:
    """Extract session_id from a .meta.json filename.

    For 'foo.meta.json' the session_id is 'foo'.
    """
    name = meta_path.name
    if name.endswith(".meta.json"):
        return name[: -len(".meta.json")]
    return meta_path.stem


def _read_metadata(meta_path: Path) -> dict | None:
    """Read and validate a meta.json file. Returns None on failure."""
    try:
        with open(meta_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Skipping malformed meta.json: %s (%s)", meta_path, exc)
        return None

    required = ("car_name", "track_name", "session_start")
    if not all(k in data for k in required):
        logger.warning("Skipping meta.json missing required fields: %s", meta_path)
        return None
    return data


def scan_sessions_dir(sessions_dir: Path, db_path: Path) -> SyncResult:
    """Scan sessions directory for CSV + meta.json pairs and register new sessions.

    Pure function — no HTTP coupling. Handles missing dirs, malformed JSON, orphans.
    """
    result = SyncResult()

    if not sessions_dir.is_dir():
        logger.warning("Sessions directory does not exist: %s", sessions_dir)
        return result

    # Collect all CSV and meta.json files
    csv_files = {f.stem: f for f in sessions_dir.glob("*.csv")}
    meta_files: dict[str, Path] = {}
    for f in sessions_dir.glob("*.meta.json"):
        sid = _extract_session_id(f)
        meta_files[sid] = f

    # Find complete pairs
    csv_ids = set(csv_files.keys())
    meta_ids = set(meta_files.keys())
    paired_ids = csv_ids & meta_ids
    orphan_count = len(csv_ids - meta_ids) + len(meta_ids - csv_ids)
    result.incomplete = orphan_count

    for sid in paired_ids:
        if session_exists(db_path, sid):
            result.already_known += 1
            continue

        meta = _read_metadata(meta_files[sid])
        if meta is None:
            result.incomplete += 1
            continue

        session = SessionRecord(
            session_id=sid,
            car=meta["car_name"],
            track=meta["track_name"],
            track_config=meta.get("track_config", ""),
            session_date=meta["session_start"],
            lap_count=meta.get("laps_completed") or 0,
            best_lap_time=None,
            state="discovered",
            session_type=meta.get("session_type"),
            csv_path=str(csv_files[sid].resolve()),
            meta_path=str(meta_files[sid].resolve()),
        )
        save_session(db_path, session)
        result.discovered += 1

    return result


def register_single_pair(csv_path: Path, meta_path: Path, db_path: Path) -> bool:
    """Register a single CSV + meta.json pair. Returns True if newly registered."""
    sid = _extract_session_id(meta_path)
    if session_exists(db_path, sid):
        return False

    meta = _read_metadata(meta_path)
    if meta is None:
        return False

    session = SessionRecord(
        session_id=sid,
        car=meta["car_name"],
        track=meta["track_name"],
        track_config=meta.get("track_config", ""),
        session_date=meta["session_start"],
        lap_count=meta.get("laps_completed") or 0,
        best_lap_time=None,
        state="discovered",
        session_type=meta.get("session_type"),
        csv_path=str(csv_path.resolve()),
        meta_path=str(meta_path.resolve()),
    )
    save_session(db_path, session)
    return True
