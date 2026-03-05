"""Tests for the processing pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio

from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import get_session, save_session

from tests.analyzer.conftest import (
    CHANNELS,
    SAMPLE_INTERVAL,
    SETUP_A,
    make_lap_data,
    make_lap_segment,
    make_parsed_session,
)
from api.analysis.pipeline import make_processing_job


def _write_session_files(
    sessions_dir: Path,
    session_id: str,
) -> tuple[Path, Path]:
    """Write a minimal CSV + meta.json that parse_session can process."""
    csv_path = sessions_dir / f"{session_id}.csv"
    meta_path = sessions_dir / f"{session_id}.meta.json"

    # Build lap data for 2 laps (outlap + flying) with proper normalized_position
    n_samples = 100
    data = make_lap_data(n_samples=n_samples, start_norm_pos=0.0, end_norm_pos=0.99)

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Add a second lap to cross lap boundary
    data2 = make_lap_data(
        n_samples=n_samples,
        start_norm_pos=0.0,
        end_norm_pos=0.99,
        base_ts=data["timestamp"][-1] + SAMPLE_INTERVAL,
    )
    df2 = pd.DataFrame(data2)
    df2["lap_count"] = 1.0

    full_df = pd.concat([df, df2], ignore_index=True)
    full_df.to_csv(csv_path, index=False)

    meta = {
        "car_name": "bmw_m235i_racing",
        "track_name": "mugello",
        "track_config": "",
        "track_length_m": 5245.0,
        "session_type": "practice",
        "tyre_compound": "SM",
        "driver_name": "Test Driver",
        "air_temp_c": 22.0,
        "road_temp_c": 30.5,
        "session_start": "2026-03-02T14:30:00",
        "session_end": "2026-03-02T15:00:00",
        "laps_completed": 2,
        "total_samples": len(full_df),
        "sample_rate_hz": 22.0,
        "app_version": "0.2.0",
    }
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    return csv_path, meta_path


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    init_db(path)
    return path


@pytest.fixture()
def sessions_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sessions"
    d.mkdir()
    return d


class TestProcessingPipeline:
    @pytest.mark.asyncio
    async def test_successful_pipeline(self, db_path: Path, sessions_dir: Path) -> None:
        session_id = "test_session"
        csv_path, meta_path = _write_session_files(sessions_dir, session_id)

        save_session(db_path, SessionRecord(
            session_id=session_id, car="bmw", track="mugello",
            session_date="2026-03-02T14:30:00", lap_count=2, best_lap_time=90.0,
            state="discovered", session_type="practice",
            csv_path=str(csv_path), meta_path=str(meta_path),
        ))

        active_jobs: dict[str, str] = {session_id: "job_123"}
        progress_steps: list[tuple[int, str]] = []

        async def update(pct: int, step: str) -> None:
            progress_steps.append((pct, step))

        pipeline = make_processing_job(
            session_id=session_id,
            csv_path=str(csv_path),
            meta_path=str(meta_path),
            sessions_dir=str(sessions_dir),
            db_path=db_path,
            active_jobs=active_jobs,
        )

        result = await pipeline(update)

        assert result["session_id"] == session_id
        assert result["state"] == "analyzed"

        # Verify progress callbacks
        assert len(progress_steps) >= 5
        assert progress_steps[0][0] == 5  # First update at 5%

        # Verify session state updated
        session = get_session(db_path, session_id)
        assert session is not None
        assert session.state == "analyzed"

        # Verify cache file exists
        cache_dir = sessions_dir / session_id
        assert (cache_dir / "analyzed.json").exists()

        # Verify active jobs cleaned up
        assert session_id not in active_jobs

    @pytest.mark.asyncio
    async def test_pipeline_csv_missing(self, db_path: Path, sessions_dir: Path) -> None:
        active_jobs: dict[str, str] = {"missing": "job_1"}

        pipeline = make_processing_job(
            session_id="missing",
            csv_path=str(sessions_dir / "nonexistent.csv"),
            meta_path=str(sessions_dir / "nonexistent.meta.json"),
            sessions_dir=str(sessions_dir),
            db_path=db_path,
            active_jobs=active_jobs,
        )

        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            async def noop(pct: int, step: str) -> None:
                pass
            await pipeline(noop)

        # Verify cleanup
        assert "missing" not in active_jobs

    @pytest.mark.asyncio
    async def test_pipeline_meta_missing(self, db_path: Path, sessions_dir: Path) -> None:
        csv_path = sessions_dir / "test.csv"
        csv_path.write_text("header\n")
        active_jobs: dict[str, str] = {"test": "job_1"}

        pipeline = make_processing_job(
            session_id="test",
            csv_path=str(csv_path),
            meta_path=str(sessions_dir / "nonexistent.meta.json"),
            sessions_dir=str(sessions_dir),
            db_path=db_path,
            active_jobs=active_jobs,
        )

        with pytest.raises(FileNotFoundError, match="Meta file not found"):
            async def noop(pct: int, step: str) -> None:
                pass
            await pipeline(noop)

        assert "test" not in active_jobs

    @pytest.mark.asyncio
    async def test_idempotent_reprocessing(self, db_path: Path, sessions_dir: Path) -> None:
        session_id = "reprocess"
        csv_path, meta_path = _write_session_files(sessions_dir, session_id)

        save_session(db_path, SessionRecord(
            session_id=session_id, car="bmw", track="mugello",
            session_date="2026-03-02T14:30:00", lap_count=2, best_lap_time=90.0,
            state="discovered", session_type="practice",
            csv_path=str(csv_path), meta_path=str(meta_path),
        ))

        async def noop(pct: int, step: str) -> None:
            pass

        active1: dict[str, str] = {session_id: "j1"}
        p1 = make_processing_job(session_id, str(csv_path), str(meta_path),
                                  str(sessions_dir), db_path, active1)
        await p1(noop)

        active2: dict[str, str] = {session_id: "j2"}
        p2 = make_processing_job(session_id, str(csv_path), str(meta_path),
                                  str(sessions_dir), db_path, active2)
        result = await p2(noop)

        assert result["state"] == "analyzed"
        assert (sessions_dir / session_id / "analyzed.json").exists()
