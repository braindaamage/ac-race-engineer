"""Tests for analysis serializers (lap summaries, corner aggregation)."""

from __future__ import annotations

import pytest

from ac_engineer.analyzer import analyze_session
from ac_engineer.analyzer.models import AnalyzedSession

from tests.analyzer.conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    SETUP_A,
    make_corner,
    make_lap_segment,
    make_parsed_session,
)
from api.analysis.serializers import (
    aggregate_corners,
    get_corner_by_lap,
    summarize_all_laps,
    summarize_lap,
)


def _make_multi_lap_analyzed() -> AnalyzedSession:
    """Build an AnalyzedSession with outlap + 2 flying laps (each with 2 corners) + inlap."""
    base_ts = BASE_TIMESTAMP
    outlap = make_lap_segment(
        lap_number=0, classification="outlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )
    base_ts += 100 * SAMPLE_INTERVAL

    flying1 = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[make_corner(1), make_corner(2, entry_norm_pos=0.50, apex_norm_pos=0.55, exit_norm_pos=0.60)],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
    )
    base_ts += 200 * SAMPLE_INTERVAL

    flying2 = make_lap_segment(
        lap_number=2, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[make_corner(1), make_corner(2, entry_norm_pos=0.50, apex_norm_pos=0.55, exit_norm_pos=0.60)],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
    )
    base_ts += 200 * SAMPLE_INTERVAL

    inlap = make_lap_segment(
        lap_number=3, classification="inlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )

    parsed = make_parsed_session(
        laps=[outlap, flying1, flying2, inlap],
        setups=[SETUP_A],
    )
    return analyze_session(parsed)


class TestSummarizeLap:
    def test_produces_correct_summary(self) -> None:
        corners = [make_corner(1)]
        lap = make_lap_segment(
            lap_number=1, classification="flying", n_samples=200,
            corners=corners, active_setup=SETUP_A,
            throttle=0.7, g_lat=0.5, g_lon=0.3,
        )
        parsed = make_parsed_session(laps=[lap], setups=[SETUP_A])
        analyzed = analyze_session(parsed)
        summary = summarize_lap(analyzed.laps[0])

        assert summary.lap_number == 1
        assert summary.classification == "flying"
        assert summary.is_invalid is False
        assert summary.lap_time_s > 0
        assert "fl" in summary.tyre_temps_avg
        assert "fr" in summary.tyre_temps_avg
        assert "rl" in summary.tyre_temps_avg
        assert "rr" in summary.tyre_temps_avg
        assert summary.peak_lat_g >= 0
        assert summary.peak_lon_g >= 0

    def test_tyre_temps_avg_extracts_core(self) -> None:
        lap = make_lap_segment(
            lap_number=1, classification="flying", n_samples=200,
            active_setup=SETUP_A,
            tyre_temp_core={"fl": 85.0, "fr": 86.0, "rl": 83.0, "rr": 84.0},
        )
        parsed = make_parsed_session(laps=[lap], setups=[SETUP_A])
        analyzed = analyze_session(parsed)
        summary = summarize_lap(analyzed.laps[0])

        # Core temps should match the input values
        assert summary.tyre_temps_avg["fl"] == pytest.approx(85.0, abs=0.5)
        assert summary.tyre_temps_avg["fr"] == pytest.approx(86.0, abs=0.5)


class TestSummarizeAllLaps:
    def test_returns_correct_count(self) -> None:
        analyzed = _make_multi_lap_analyzed()
        summaries = summarize_all_laps(analyzed)
        assert len(summaries) == 4  # outlap + 2 flying + inlap


class TestAggregateCorners:
    def test_aggregates_across_flying_laps(self) -> None:
        analyzed = _make_multi_lap_analyzed()
        aggregated = aggregate_corners(analyzed)

        assert len(aggregated) == 2
        assert aggregated[0].corner_number == 1
        assert aggregated[1].corner_number == 2
        assert aggregated[0].sample_count == 2  # 2 flying laps

    def test_excludes_non_flying_laps(self) -> None:
        analyzed = _make_multi_lap_analyzed()
        aggregated = aggregate_corners(analyzed)

        # Only flying laps contribute, outlap/inlap don't have corners anyway
        for agg in aggregated:
            assert agg.sample_count == 2

    def test_empty_corners(self) -> None:
        lap = make_lap_segment(
            lap_number=1, classification="flying", n_samples=200,
            active_setup=SETUP_A, corners=[],
        )
        parsed = make_parsed_session(laps=[lap], setups=[SETUP_A])
        analyzed = analyze_session(parsed)
        assert aggregate_corners(analyzed) == []

    def test_sorted_by_corner_number(self) -> None:
        analyzed = _make_multi_lap_analyzed()
        aggregated = aggregate_corners(analyzed)
        corner_numbers = [c.corner_number for c in aggregated]
        assert corner_numbers == sorted(corner_numbers)


class TestGetCornerByLap:
    def test_returns_per_lap_entries(self) -> None:
        analyzed = _make_multi_lap_analyzed()
        entries = get_corner_by_lap(analyzed, 1)

        # Corner 1 exists in flying laps 1 and 2
        assert len(entries) >= 2
        lap_numbers = {e.lap_number for e in entries}
        assert 1 in lap_numbers
        assert 2 in lap_numbers

    def test_nonexistent_corner_returns_empty(self) -> None:
        analyzed = _make_multi_lap_analyzed()
        entries = get_corner_by_lap(analyzed, 999)
        assert entries == []
