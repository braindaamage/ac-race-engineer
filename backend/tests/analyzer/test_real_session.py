"""Validation tests against real BMW M235i Mugello session data."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.analyzer import AnalyzedSession, analyze_session
from ac_engineer.parser import parse_session

EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "examples" / "sessions"
CSV_PATH = EXAMPLES_DIR / "2026-03-03_2150_ks_bmw_m235i_racing_mugello.csv"
META_PATH = EXAMPLES_DIR / "2026-03-03_2150_ks_bmw_m235i_racing_mugello.meta.json"

pytestmark = pytest.mark.skipif(
    not CSV_PATH.exists(), reason="Real session data not available"
)


@pytest.fixture(scope="module")
def real_session():
    """Parse and analyze the real session once for all tests."""
    parsed = parse_session(CSV_PATH, META_PATH)
    return parsed, analyze_session(parsed)


class TestRealSessionStructure:
    def test_returns_analyzed_session(self, real_session):
        _, result = real_session
        assert isinstance(result, AnalyzedSession)

    def test_lap_count_matches(self, real_session):
        parsed, result = real_session
        assert len(result.laps) == len(parsed.laps)

    def test_flying_laps_have_timing(self, real_session):
        _, result = real_session
        for lap in result.laps:
            if lap.classification == "flying":
                assert lap.metrics.timing.lap_time_s is not None
                assert lap.metrics.timing.lap_time_s > 0


class TestRealSessionPlausibility:
    def test_lap_times_plausible(self, real_session):
        _, result = real_session
        for lap in result.laps:
            if lap.classification == "flying":
                t = lap.metrics.timing.lap_time_s
                assert t > 30.0, f"Lap {lap.lap_number} too fast: {t}s"
                assert t < 300.0, f"Lap {lap.lap_number} too slow: {t}s"

    def test_speeds_positive(self, real_session):
        _, result = real_session
        for lap in result.laps:
            assert lap.metrics.speed.max_speed > 0
            assert lap.metrics.speed.avg_speed > 0

    def test_temperatures_positive(self, real_session):
        _, result = real_session
        for lap in result.laps:
            for w in ("fl", "fr", "rl", "rr"):
                assert lap.metrics.tyres.temps_avg[w].core > 0

    def test_throttle_percentages_valid(self, real_session):
        _, result = real_session
        for lap in result.laps:
            di = lap.metrics.driver_inputs
            total = di.full_throttle_pct + di.partial_throttle_pct + di.off_throttle_pct
            assert total == pytest.approx(100.0, abs=0.1)

    def test_fuel_metrics_present(self, real_session):
        _, result = real_session
        flying = [l for l in result.laps if l.classification == "flying"]
        # At least some flying laps should have fuel data
        has_fuel = any(l.metrics.fuel is not None for l in flying)
        assert has_fuel


class TestRealSessionCorners:
    def test_flying_laps_have_corners(self, real_session):
        _, result = real_session
        flying = [l for l in result.laps if l.classification == "flying"]
        for lap in flying:
            assert len(lap.corners) > 0, f"Lap {lap.lap_number} has no corners"

    def test_corner_speeds_positive(self, real_session):
        _, result = real_session
        for lap in result.laps:
            for c in lap.corners:
                assert c.performance.apex_speed_kmh > 0
                assert c.performance.entry_speed_kmh > 0


class TestRealSessionStints:
    def test_stints_detected(self, real_session):
        _, result = real_session
        assert len(result.stints) >= 1

    def test_stint_comparison_if_multiple(self, real_session):
        _, result = real_session
        if len(result.stints) >= 2:
            assert len(result.stint_comparisons) == len(result.stints) - 1


class TestRealSessionConsistency:
    def test_consistency_present(self, real_session):
        _, result = real_session
        assert result.consistency is not None

    def test_best_worst_relationship(self, real_session):
        _, result = real_session
        c = result.consistency
        assert c.best_lap_time_s <= c.worst_lap_time_s


class TestRealSessionDeterminism:
    def test_deterministic(self, real_session):
        parsed, result1 = real_session
        result2 = analyze_session(parsed)
        assert result1.model_dump() == result2.model_dump()
