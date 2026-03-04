"""Integration tests for the full analyze_session pipeline."""

from __future__ import annotations

import copy

import pytest

from ac_engineer.analyzer import AnalyzedSession, analyze_session


class TestAnalyzeSessionMultiLap:
    """Test with multi_lap_session (outlap + 2 flying + inlap)."""

    def test_returns_analyzed_session(self, multi_lap_session):
        result = analyze_session(multi_lap_session)
        assert isinstance(result, AnalyzedSession)

    def test_lap_count_matches(self, multi_lap_session):
        result = analyze_session(multi_lap_session)
        assert len(result.laps) == len(multi_lap_session.laps)

    def test_each_lap_has_metrics(self, multi_lap_session):
        result = analyze_session(multi_lap_session)
        for lap in result.laps:
            assert lap.metrics.timing.lap_time_s > 0

    def test_flying_laps_have_corners(self, multi_lap_session):
        result = analyze_session(multi_lap_session)
        for lap in result.laps:
            if lap.classification == "flying":
                assert len(lap.corners) > 0

    def test_stints_grouped(self, multi_lap_session):
        result = analyze_session(multi_lap_session)
        assert len(result.stints) >= 1

    def test_consistency_present(self, multi_lap_session):
        result = analyze_session(multi_lap_session)
        assert result.consistency is not None
        assert result.consistency.flying_lap_count == 2


class TestAnalyzeSessionReducedMode:
    """Test with reduced_mode_session."""

    def test_fuel_none(self, reduced_mode_session):
        result = analyze_session(reduced_mode_session)
        for lap in result.laps:
            assert lap.metrics.fuel is None

    def test_timing_present(self, reduced_mode_session):
        result = analyze_session(reduced_mode_session)
        for lap in result.laps:
            assert lap.metrics.timing.lap_time_s > 0


class TestAnalyzeSessionAllInvalid:
    """Test with all_invalid_session."""

    def test_all_laps_invalid(self, all_invalid_session):
        result = analyze_session(all_invalid_session)
        for lap in result.laps:
            assert lap.is_invalid is True

    def test_metrics_still_computed(self, all_invalid_session):
        result = analyze_session(all_invalid_session)
        for lap in result.laps:
            assert lap.metrics.timing.lap_time_s > 0


class TestAnalyzeSessionSingleFlying:
    """Test with single_flying_lap_session."""

    def test_consistency_stddev_zero(self, single_flying_lap_session):
        result = analyze_session(single_flying_lap_session)
        assert result.consistency is not None
        assert result.consistency.lap_time_stddev_s == pytest.approx(0.0)

    def test_one_stint_no_trends(self, single_flying_lap_session):
        result = analyze_session(single_flying_lap_session)
        assert len(result.stints) == 1
        assert result.stints[0].trends is None


class TestAnalyzeSessionTwoStints:
    """Test with two_stint_session."""

    def test_two_stints(self, two_stint_session):
        result = analyze_session(two_stint_session)
        assert len(result.stints) == 2

    def test_stint_comparison(self, two_stint_session):
        result = analyze_session(two_stint_session)
        assert len(result.stint_comparisons) == 1
        comp = result.stint_comparisons[0]
        assert comp.stint_a_index == 0
        assert comp.stint_b_index == 1

    def test_setup_changes_detected(self, two_stint_session):
        result = analyze_session(two_stint_session)
        comp = result.stint_comparisons[0]
        assert len(comp.setup_changes) > 0


class TestAnalyzeSessionDeterminism:
    """Test that identical input produces identical output."""

    def test_deterministic(self, multi_lap_session):
        result1 = analyze_session(multi_lap_session)
        result2 = analyze_session(multi_lap_session)
        assert result1.model_dump() == result2.model_dump()


class TestAnalyzeSessionImmutability:
    """Test that input ParsedSession is not modified."""

    def test_input_not_modified(self, multi_lap_session):
        original = copy.deepcopy(multi_lap_session.model_dump())
        analyze_session(multi_lap_session)
        assert multi_lap_session.model_dump() == original


class TestAnalyzeSessionEmpty:
    """Test with no laps."""

    def test_empty_session(self):
        from .conftest import make_parsed_session
        session = make_parsed_session(laps=[])
        result = analyze_session(session)
        assert len(result.laps) == 0
        assert len(result.stints) == 0
        assert result.consistency is None
