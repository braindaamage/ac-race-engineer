"""Tests for consistency analysis — session-wide consistency metrics."""

from __future__ import annotations

import pytest

from ac_engineer.analyzer.consistency import compute_consistency
from ac_engineer.analyzer.corner_analyzer import analyze_corner
from ac_engineer.analyzer.lap_analyzer import analyze_lap
from ac_engineer.analyzer.models import AnalyzedLap, ConsistencyMetrics, CornerMetrics

from .conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    SETUP_A,
    make_corner,
    make_lap_segment,
    make_parsed_session,
)


def _build_analyzed_lap(lap, metadata, lap_df=None):
    """Build an AnalyzedLap from a LapSegment."""
    metrics = analyze_lap(lap, metadata)
    corners: list[CornerMetrics] = []
    if lap.corners:
        df = lap.to_dataframe()
        for c in lap.corners:
            corners.append(analyze_corner(c, df))
    return AnalyzedLap(
        lap_number=lap.lap_number,
        classification=lap.classification,
        is_invalid=lap.is_invalid,
        metrics=metrics,
        corners=corners,
    )


class TestComputeConsistencyMultiLap:
    """Test with 4 flying laps."""

    @pytest.fixture
    def four_flying_laps(self):
        base_ts = BASE_TIMESTAMP
        corners = [make_corner(1, 0.10, 0.15, 0.20)]
        laps = []
        for i in range(4):
            n_samples = 200 + i * 5  # slightly varied lap times
            lap = make_lap_segment(
                lap_number=i, classification="flying", n_samples=n_samples,
                base_ts=base_ts, active_setup=SETUP_A,
                corners=corners,
            )
            laps.append(lap)
            base_ts += n_samples * SAMPLE_INTERVAL

        session = make_parsed_session(laps=laps, setups=[SETUP_A])
        analyzed = [_build_analyzed_lap(l, session.metadata) for l in laps]
        return analyzed

    def test_returns_consistency(self, four_flying_laps):
        result = compute_consistency(four_flying_laps)
        assert result is not None
        assert isinstance(result, ConsistencyMetrics)

    def test_flying_lap_count(self, four_flying_laps):
        result = compute_consistency(four_flying_laps)
        assert result.flying_lap_count == 4

    def test_lap_time_stddev(self, four_flying_laps):
        result = compute_consistency(four_flying_laps)
        assert result.lap_time_stddev_s >= 0

    def test_best_worst_relationship(self, four_flying_laps):
        result = compute_consistency(four_flying_laps)
        assert result.best_lap_time_s <= result.worst_lap_time_s

    def test_trend_slope(self, four_flying_laps):
        result = compute_consistency(four_flying_laps)
        assert result.lap_time_trend_slope is not None

    def test_corner_consistency(self, four_flying_laps):
        result = compute_consistency(four_flying_laps)
        assert len(result.corner_consistency) > 0
        cc = result.corner_consistency[0]
        assert cc.corner_number == 1
        assert cc.sample_count == 4


class TestComputeConsistencySingleLap:
    """Test with 1 flying lap."""

    def test_stddev_zero(self, single_flying_lap_session):
        lap = single_flying_lap_session.laps[0]
        analyzed = [_build_analyzed_lap(lap, single_flying_lap_session.metadata)]
        result = compute_consistency(analyzed)
        assert result is not None
        assert result.lap_time_stddev_s == pytest.approx(0.0)

    def test_trend_none(self, single_flying_lap_session):
        lap = single_flying_lap_session.laps[0]
        analyzed = [_build_analyzed_lap(lap, single_flying_lap_session.metadata)]
        result = compute_consistency(analyzed)
        assert result.lap_time_trend_slope is None


class TestComputeConsistencyNoFlying:
    """Test with 0 flying laps."""

    def test_returns_none(self):
        lap = make_lap_segment(
            lap_number=0, classification="outlap", n_samples=100,
        )
        session = make_parsed_session(laps=[lap])
        analyzed = [_build_analyzed_lap(lap, session.metadata)]
        result = compute_consistency(analyzed)
        assert result is None


class TestComputeConsistencyCornerVariance:
    """Test corner consistency with missing corners."""

    def test_corner_missing_from_some_laps(self):
        base_ts = BASE_TIMESTAMP
        # Lap 0: has corner 1 and 2
        lap0 = make_lap_segment(
            lap_number=0, classification="flying", n_samples=200,
            base_ts=base_ts, active_setup=SETUP_A,
            corners=[
                make_corner(1, 0.10, 0.15, 0.20),
                make_corner(2, 0.50, 0.55, 0.60),
            ],
        )
        base_ts += 200 * SAMPLE_INTERVAL
        # Lap 1: has only corner 1
        lap1 = make_lap_segment(
            lap_number=1, classification="flying", n_samples=200,
            base_ts=base_ts, active_setup=SETUP_A,
            corners=[make_corner(1, 0.10, 0.15, 0.20)],
        )

        session = make_parsed_session(laps=[lap0, lap1], setups=[SETUP_A])
        analyzed = [_build_analyzed_lap(l, session.metadata) for l in [lap0, lap1]]
        result = compute_consistency(analyzed)

        assert result is not None
        # Corner 1 appears in both laps
        c1 = [c for c in result.corner_consistency if c.corner_number == 1]
        assert len(c1) == 1
        assert c1[0].sample_count == 2
        # Corner 2 appears in only 1 lap → variance may be None
        c2 = [c for c in result.corner_consistency if c.corner_number == 2]
        assert len(c2) == 1
        assert c2[0].sample_count == 1
