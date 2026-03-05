"""Tests for analysis cache save/load round-trip."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.analyzer import analyze_session
from ac_engineer.analyzer.models import AnalyzedSession

# Reuse fixture builders from analyzer tests
from tests.analyzer.conftest import (
    make_corner,
    make_lap_segment,
    make_parsed_session,
    SETUP_A,
)
from api.analysis.cache import get_cache_dir, load_analyzed_session, save_analyzed_session


def _make_analyzed() -> AnalyzedSession:
    """Build a realistic AnalyzedSession for testing."""
    corners = [
        make_corner(corner_number=1),
        make_corner(corner_number=2, entry_norm_pos=0.50, apex_norm_pos=0.55, exit_norm_pos=0.60),
    ]
    lap = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        corners=corners, active_setup=SETUP_A,
        throttle=0.7, g_lat=0.5, g_lon=0.3,
    )
    parsed = make_parsed_session(laps=[lap], setups=[SETUP_A])
    return analyze_session(parsed)


class TestGetCacheDir:
    def test_returns_correct_path(self, tmp_path: Path) -> None:
        result = get_cache_dir(tmp_path, "session_abc")
        assert result == tmp_path / "session_abc"

    def test_returns_path_type(self, tmp_path: Path) -> None:
        result = get_cache_dir(str(tmp_path), "session_abc")
        assert isinstance(result, Path)


class TestSaveLoadRoundTrip:
    def test_round_trip_produces_identical_data(self, tmp_path: Path) -> None:
        analyzed = _make_analyzed()
        cache_dir = tmp_path / "test_session"
        save_analyzed_session(cache_dir, analyzed)
        loaded = load_analyzed_session(cache_dir)

        assert loaded.metadata == analyzed.metadata
        assert len(loaded.laps) == len(analyzed.laps)
        assert loaded.laps[0].lap_number == analyzed.laps[0].lap_number
        assert loaded.laps[0].metrics.timing.lap_time_s == analyzed.laps[0].metrics.timing.lap_time_s
        assert len(loaded.laps[0].corners) == len(analyzed.laps[0].corners)
        assert loaded.stints == analyzed.stints
        assert loaded.stint_comparisons == analyzed.stint_comparisons

    def test_load_nonexistent_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_analyzed_session(tmp_path / "nonexistent")

    def test_load_corrupted_json_raises_value_error(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "corrupted"
        cache_dir.mkdir()
        (cache_dir / "analyzed.json").write_text("not valid json{{{", encoding="utf-8")
        with pytest.raises(ValueError):
            load_analyzed_session(cache_dir)

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        analyzed = _make_analyzed()
        cache_dir = tmp_path / "idempotent"
        save_analyzed_session(cache_dir, analyzed)
        save_analyzed_session(cache_dir, analyzed)
        loaded = load_analyzed_session(cache_dir)
        assert len(loaded.laps) == len(analyzed.laps)

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        analyzed = _make_analyzed()
        cache_dir = tmp_path / "new_dir" / "nested"
        path = save_analyzed_session(cache_dir, analyzed)
        assert path.exists()
        assert path.name == "analyzed.json"
