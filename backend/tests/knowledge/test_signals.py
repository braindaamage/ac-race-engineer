"""Tests for signal detection functions."""

from __future__ import annotations

from ac_engineer.knowledge.signals import detect_signals
from tests.knowledge.conftest import make_analyzed_session, make_corner_metrics, make_stint_metrics


class TestSignalDetection:
    def test_understeer_detected(self, understeer_session):
        signals = detect_signals(understeer_session)
        assert "high_understeer" in signals

    def test_no_signals_clean_session(self, clean_session):
        signals = detect_signals(clean_session)
        assert signals == []

    def test_tyre_temp_spread_detected(self, tyre_temp_session):
        signals = detect_signals(tyre_temp_session)
        assert "tyre_temp_spread_high" in signals

    def test_lap_time_degradation_detected(self, degradation_session):
        signals = detect_signals(degradation_session)
        assert "lap_time_degradation" in signals

    def test_none_fields_no_crash(self):
        session = make_analyzed_session(
            laps=[],
            stints=[],
            consistency=None,
        )
        signals = detect_signals(session)
        assert isinstance(signals, list)

    def test_empty_laps_no_crash(self):
        session = make_analyzed_session(laps=[])
        signals = detect_signals(session)
        assert isinstance(signals, list)
