"""Tests for stint analyzer — grouping, trends, and comparison."""

from __future__ import annotations

import pytest

from ac_engineer.analyzer.lap_analyzer import analyze_lap
from ac_engineer.analyzer.models import AnalyzedLap, StintComparison, StintMetrics
from ac_engineer.analyzer.stint_analyzer import (
    compare_stints,
    compute_stint_trends,
    group_stints,
)

from .conftest import (
    SETUP_A,
    SETUP_B,
    make_lap_segment,
    make_parsed_session,
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
)


def _analyze_laps(session):
    """Helper to analyze all laps in a session."""
    return [
        AnalyzedLap(
            lap_number=lap.lap_number,
            classification=lap.classification,
            is_invalid=lap.is_invalid,
            metrics=analyze_lap(lap, session.metadata),
        )
        for lap in session.laps
    ]


class TestGroupStints:
    def test_two_stints(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        assert len(stints) == 2
        assert stints[0].setup_filename == "setup_a.ini"
        assert stints[1].setup_filename == "setup_b.ini"

    def test_two_stints_lap_numbers(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        assert stints[0].lap_numbers == [0, 1]
        assert stints[1].lap_numbers == [2, 3]

    def test_two_stints_flying_count(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        assert stints[0].flying_lap_count == 1  # lap 1
        assert stints[1].flying_lap_count == 2  # laps 2, 3

    def test_single_stint(self, multi_lap_session):
        analyzed = _analyze_laps(multi_lap_session)
        stints = group_stints(analyzed, multi_lap_session.laps)
        assert len(stints) == 1
        assert stints[0].setup_filename == "setup_a.ini"

    def test_no_setup(self):
        """All laps with no setup → single stint."""
        laps = [
            make_lap_segment(lap_number=0, classification="flying", n_samples=100),
            make_lap_segment(
                lap_number=1, classification="flying", n_samples=100,
                base_ts=BASE_TIMESTAMP + 100 * SAMPLE_INTERVAL,
            ),
        ]
        session = make_parsed_session(laps=laps)
        analyzed = _analyze_laps(session)
        stints = group_stints(analyzed, session.laps)
        assert len(stints) == 1
        assert stints[0].setup_filename is None

    def test_aggregated_metrics(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        # Stint 2 has 2 flying laps → should have mean lap time
        assert stints[1].aggregated.lap_time_mean_s is not None


class TestComputeStintTrends:
    def test_with_two_flying_laps(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        # Stint 2 has 2 flying laps
        trends = compute_stint_trends(stints[1], analyzed)
        assert trends is not None
        assert trends.lap_time_slope is not None

    def test_with_one_flying_lap(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        # Stint 1 has 1 flying lap
        trends = compute_stint_trends(stints[0], analyzed)
        assert trends is None

    def test_trends_slope_direction(self):
        """3 flying laps with increasing lap time → positive slope."""
        base_ts = BASE_TIMESTAMP
        laps = []
        for i in range(3):
            n_samples = 100 + i * 10  # progressively longer laps
            lap = make_lap_segment(
                lap_number=i, classification="flying", n_samples=n_samples,
                base_ts=base_ts, active_setup=SETUP_A,
            )
            laps.append(lap)
            base_ts += n_samples * SAMPLE_INTERVAL

        session = make_parsed_session(laps=laps, setups=[SETUP_A])
        analyzed = _analyze_laps(session)
        stints = group_stints(analyzed, session.laps)
        trends = compute_stint_trends(stints[0], analyzed)
        assert trends is not None
        assert trends.lap_time_slope > 0  # increasing lap times


class TestCompareStints:
    def test_different_setups(self, two_stint_session):
        analyzed = _analyze_laps(two_stint_session)
        stints = group_stints(analyzed, two_stint_session.laps)
        comparison = compare_stints(
            stints[0], stints[1],
            SETUP_A, SETUP_B,
        )
        assert isinstance(comparison, StintComparison)
        assert comparison.stint_a_index == 0
        assert comparison.stint_b_index == 1
        # FRONT CAMBER changed from -2.5 to -3.0
        assert len(comparison.setup_changes) > 0
        camber_changes = [c for c in comparison.setup_changes if c.name == "CAMBER"]
        assert len(camber_changes) > 0

    def test_identical_setups(self):
        """Same setup → empty setup_changes."""
        base_ts = BASE_TIMESTAMP
        laps = []
        for i in range(4):
            lap = make_lap_segment(
                lap_number=i, classification="flying", n_samples=100,
                base_ts=base_ts, active_setup=SETUP_A,
            )
            laps.append(lap)
            base_ts += 100 * SAMPLE_INTERVAL

        session = make_parsed_session(laps=laps, setups=[SETUP_A])
        analyzed = _analyze_laps(session)
        # Manually create 2 stints from same setup
        from ac_engineer.analyzer.models import AggregatedStintMetrics
        stint_a = StintMetrics(
            stint_index=0, setup_filename="setup_a.ini",
            lap_numbers=[0, 1], flying_lap_count=2,
            aggregated=AggregatedStintMetrics(
                lap_time_mean_s=analyzed[0].metrics.timing.lap_time_s,
            ),
        )
        stint_b = StintMetrics(
            stint_index=1, setup_filename="setup_a.ini",
            lap_numbers=[2, 3], flying_lap_count=2,
            aggregated=AggregatedStintMetrics(
                lap_time_mean_s=analyzed[2].metrics.timing.lap_time_s,
            ),
        )
        comparison = compare_stints(stint_a, stint_b, SETUP_A, SETUP_A)
        assert comparison.setup_changes == []
