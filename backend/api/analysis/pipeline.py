"""Processing pipeline — parse + analyze as a tracked background job."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable

from ac_engineer.analyzer import analyze_session
from ac_engineer.parser import parse_session
from ac_engineer.parser.cache import save_session as save_parsed_session
from ac_engineer.storage.sessions import update_session_state

from api.analysis.cache import get_cache_dir, save_analyzed_session


def make_processing_job(
    session_id: str,
    csv_path: str,
    meta_path: str,
    sessions_dir: str | Path,
    db_path: str | Path,
    active_jobs: dict[str, str],
) -> Callable[[Callable[[int, str], Awaitable[None]]], Awaitable[Any]]:
    """Build an async callable that runs the full processing pipeline."""

    async def pipeline(
        update: Callable[[int, str], Awaitable[None]],
    ) -> dict[str, str]:
        try:
            csv = Path(csv_path)
            meta = Path(meta_path)
            if not csv.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            if not meta.exists():
                raise FileNotFoundError(f"Meta file not found: {meta_path}")

            await update(5, "Parsing session...")
            parsed = await asyncio.to_thread(parse_session, csv, meta)

            cache_dir = get_cache_dir(sessions_dir, session_id)

            await update(35, "Saving parsed data...")
            await asyncio.to_thread(save_parsed_session, parsed, cache_dir)

            await update(45, "Analyzing metrics...")
            analyzed = await asyncio.to_thread(analyze_session, parsed)

            await update(85, "Caching analysis results...")
            save_analyzed_session(cache_dir, analyzed)

            await update(95, "Updating session state...")
            update_session_state(db_path, session_id, "analyzed")

            return {"session_id": session_id, "state": "analyzed"}
        finally:
            active_jobs.pop(session_id, None)

    return pipeline
