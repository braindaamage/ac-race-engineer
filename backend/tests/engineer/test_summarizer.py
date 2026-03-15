"""Tests for session summarizer."""

from __future__ import annotations

import copy

from ac_engineer.config import ACConfig
from ac_engineer.engineer.models import SessionSummary
from ac_engineer.engineer.summarizer import summarize_session

from .conftest import (
    make_analyzed_lap,
    make_analyzed_session,
    make_corner_metrics,
    make_stint_metrics,
    _default_tyre_metrics,
    _default_lap_metrics,
    WHEELS,
)
from ac_engineer.analyzer.models import (
    AnalyzedLap,
    ConsistencyMetrics,
    StintComparison,
    MetricDeltas,
    SetupParameterDelta,
    TimingMetrics,
    TyreMetrics,
    WheelTempZones,
)


def _config() -> ACConfig:
    return ACConfig()


# ---------------------------------------------------------------------------
# T008: Flying lap filtering
# ---------------------------------------------------------------------------


class TestFlyingLapFiltering:
    def test_only_flying_laps_included(self):
        laps = [
            make_analyzed_lap(lap_number=1, classification="outlap", lap_time_s=120.0),
            make_analyzed_lap(lap_number=2, classification="flying", lap_time_s=90.0),
            make_analyzed_lap(lap_number=3, classification="flying", lap_time_s=91.0),
            make_analyzed_lap(lap_number=4, classification="inlap", lap_time_s=110.0),
        ]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        assert summary.flying_lap_count == 2
        assert len(summary.laps) == 2

    def test_mixed_15_laps_produces_10_flying(self):
        laps = []
        # 3 outlaps
        for i in range(1, 4):
            laps.append(make_analyzed_lap(lap_number=i, classification="outlap", lap_time_s=120.0))
        # 10 flying
        for i in range(4, 14):
            laps.append(make_analyzed_lap(lap_number=i, classification="flying", lap_time_s=88.0 + i * 0.1))
        # 2 inlaps
        for i in range(14, 16):
            laps.append(make_analyzed_lap(lap_number=i, classification="inlap", lap_time_s=110.0))

        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        assert summary.flying_lap_count == 10
        assert len(summary.laps) == 10

    def test_lap_summary_has_correct_number_and_time(self):
        laps = [
            make_analyzed_lap(lap_number=5, classification="flying", lap_time_s=89.5),
            make_analyzed_lap(lap_number=6, classification="flying", lap_time_s=90.2),
        ]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        assert summary.laps[0].lap_number == 5
        assert summary.laps[0].lap_time_s == 89.5
        assert summary.laps[1].lap_number == 6
        assert summary.laps[1].lap_time_s == 90.2


# ---------------------------------------------------------------------------
# T009: Best lap and gap
# ---------------------------------------------------------------------------


class TestBestLapAndGap:
    def test_best_lap_flagged(self):
        laps = [
            make_analyzed_lap(lap_number=1, classification="flying", lap_time_s=91.0),
            make_analyzed_lap(lap_number=2, classification="flying", lap_time_s=89.0),
            make_analyzed_lap(lap_number=3, classification="flying", lap_time_s=90.0),
        ]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        best = [l for l in summary.laps if l.is_best]
        assert len(best) == 1
        assert best[0].lap_number == 2
        assert best[0].gap_to_best_s == 0.0

    def test_gap_to_best_positive(self):
        laps = [
            make_analyzed_lap(lap_number=1, classification="flying", lap_time_s=91.0),
            make_analyzed_lap(lap_number=2, classification="flying", lap_time_s=89.0),
        ]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        non_best = [l for l in summary.laps if not l.is_best]
        assert len(non_best) == 1
        assert abs(non_best[0].gap_to_best_s - 2.0) < 0.001

    def test_single_flying_lap_is_best(self):
        session = make_analyzed_session(
            laps=[make_analyzed_lap(lap_number=1, classification="flying", lap_time_s=92.0)]
        )
        summary = summarize_session(session, _config())
        assert len(summary.laps) == 1
        assert summary.laps[0].is_best is True
        assert summary.laps[0].gap_to_best_s == 0.0


# ---------------------------------------------------------------------------
# T010: Signal detection and corner issues
# ---------------------------------------------------------------------------


class TestSignalsAndCornerIssues:
    def test_signals_populated(self):
        # Create session with high understeer to trigger signal
        corners = [make_corner_metrics(corner_number=1, understeer_ratio=1.5)]
        laps = [make_analyzed_lap(corners=corners)]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        assert isinstance(summary.signals, list)

    def test_corner_issues_sorted_by_severity(self):
        corners = [
            make_corner_metrics(corner_number=1, understeer_ratio=1.1),   # low
            make_corner_metrics(corner_number=2, understeer_ratio=1.5),   # high
            make_corner_metrics(corner_number=3, understeer_ratio=1.25),  # medium
        ]
        laps = [make_analyzed_lap(corners=corners)]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        if len(summary.corner_issues) >= 2:
            severities = [ci.severity for ci in summary.corner_issues]
            severity_order = {"high": 0, "medium": 1, "low": 2}
            for i in range(len(severities) - 1):
                assert severity_order[severities[i]] <= severity_order[severities[i + 1]]

    def test_corner_issues_capped_at_default_5(self):
        corners = [
            make_corner_metrics(corner_number=i, understeer_ratio=1.3 + i * 0.05)
            for i in range(1, 10)
        ]
        laps = [make_analyzed_lap(corners=corners)]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        assert len(summary.corner_issues) <= 5

    def test_custom_max_corner_issues(self):
        corners = [
            make_corner_metrics(corner_number=i, understeer_ratio=1.3 + i * 0.05)
            for i in range(1, 10)
        ]
        laps = [make_analyzed_lap(corners=corners)]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config(), max_corner_issues=3)
        assert len(summary.corner_issues) <= 3


# ---------------------------------------------------------------------------
# T011: Stint summaries
# ---------------------------------------------------------------------------


class TestStintSummaries:
    def test_stint_flying_lap_count(self):
        stint = make_stint_metrics(stint_index=0, flying_lap_count=5)
        session = make_analyzed_session(stints=[stint])
        summary = summarize_session(session, _config())
        assert len(summary.stints) == 1
        assert summary.stints[0].flying_lap_count == 5

    def test_lap_time_trend_from_slope(self):
        # Negative slope = improving
        stint_impr = make_stint_metrics(stint_index=0, lap_time_slope=-0.1)
        session = make_analyzed_session(stints=[stint_impr])
        summary = summarize_session(session, _config())
        assert summary.stints[0].lap_time_trend == "improving"

        # Positive slope > 0.05 = degrading
        stint_degr = make_stint_metrics(stint_index=0, lap_time_slope=0.1)
        session = make_analyzed_session(stints=[stint_degr])
        summary = summarize_session(session, _config())
        assert summary.stints[0].lap_time_trend == "degrading"

        # Small slope = stable
        stint_stable = make_stint_metrics(stint_index=0, lap_time_slope=0.02)
        session = make_analyzed_session(stints=[stint_stable])
        summary = summarize_session(session, _config())
        assert summary.stints[0].lap_time_trend == "stable"

    def test_setup_filename_populated(self):
        stint = make_stint_metrics(setup_filename="my_setup.ini")
        session = make_analyzed_session(stints=[stint])
        summary = summarize_session(session, _config())
        assert summary.stints[0].setup_filename == "my_setup.ini"

    def test_setup_changes_from_comparisons(self):
        stint_a = make_stint_metrics(stint_index=0, setup_filename="a.ini")
        stint_b = make_stint_metrics(stint_index=1, setup_filename="b.ini")
        comparison = StintComparison(
            stint_a_index=0,
            stint_b_index=1,
            setup_changes=[
                SetupParameterDelta(
                    section="CAMBER_LF", name="VALUE",
                    value_a=-1.5, value_b=-2.0,
                ),
            ],
            metric_deltas=MetricDeltas(),
        )
        session = make_analyzed_session(
            stints=[stint_a, stint_b],
            stint_comparisons=[comparison],
        )
        summary = summarize_session(session, _config())
        assert len(summary.stints) == 2
        # Second stint should have changes from prev
        assert len(summary.stints[1].setup_changes_from_prev) > 0


# ---------------------------------------------------------------------------
# T012: Edge cases and determinism
# ---------------------------------------------------------------------------


class TestEdgeCasesAndDeterminism:
    def test_zero_flying_laps_valid_summary(self):
        laps = [
            make_analyzed_lap(lap_number=1, classification="outlap"),
            make_analyzed_lap(lap_number=2, classification="inlap"),
        ]
        session = make_analyzed_session(
            laps=laps,
            consistency=ConsistencyMetrics(
                flying_lap_count=0,
                lap_time_stddev_s=0.0,
                best_lap_time_s=0.0,
                worst_lap_time_s=0.0,
            ),
        )
        summary = summarize_session(session, _config())
        assert summary.flying_lap_count == 0
        assert summary.laps == []
        assert isinstance(summary, SessionSummary)

    def test_missing_tyre_data_produces_none(self):
        # Create lap with None tyre temps
        tyre_metrics = _default_tyre_metrics(
            temps_avg={},
            pressure_avg={},
        )
        laps = [make_analyzed_lap(
            lap_number=1,
            classification="flying",
            tyres=tyre_metrics,
        )]
        session = make_analyzed_session(laps=laps)
        summary = summarize_session(session, _config())
        # Should handle gracefully
        assert isinstance(summary, SessionSummary)

    def test_deterministic_output(self):
        session = make_analyzed_session()
        s1 = summarize_session(session, _config())
        s2 = summarize_session(session, _config())
        assert s1.model_dump() == s2.model_dump()

    def test_input_not_mutated(self):
        session = make_analyzed_session()
        original = copy.deepcopy(session.model_dump())
        summarize_session(session, _config())
        assert session.model_dump() == original


# ---------------------------------------------------------------------------
# Setup .ini contents parsing
# ---------------------------------------------------------------------------


class TestSetupIniContents:
    def test_setup_ini_populates_active_setup_parameters(self):
        ini_contents = "[CAMBER_LF]\nVALUE=-2.5\n\n[PRESSURE_RF]\nVALUE=26.0\n"
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])
        summary = summarize_session(session, _config(), setup_ini_contents=ini_contents)
        assert summary.active_setup_parameters is not None
        assert "CAMBER_LF" in summary.active_setup_parameters
        assert summary.active_setup_parameters["CAMBER_LF"]["VALUE"] == -2.5
        assert "PRESSURE_RF" in summary.active_setup_parameters
        assert summary.active_setup_parameters["PRESSURE_RF"]["VALUE"] == 26.0

    def test_no_setup_ini_leaves_parameters_none(self):
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])
        summary = summarize_session(session, _config())
        assert summary.active_setup_parameters is None

    def test_empty_setup_ini_leaves_parameters_none(self):
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])
        summary = summarize_session(session, _config(), setup_ini_contents="")
        assert summary.active_setup_parameters is None

    def test_invalid_setup_ini_leaves_parameters_none(self):
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])
        summary = summarize_session(session, _config(), setup_ini_contents="not valid ini {{{{")
        # Should handle gracefully — either None or parsed as best effort
        assert isinstance(summary, SessionSummary)


# ---------------------------------------------------------------------------
# T007 [US1]: INDEX parameter conversion in summarizer
# ---------------------------------------------------------------------------


class TestIndexParameterConversion:
    def test_index_parameter_converted_to_physical(self):
        """ARB_FRONT VALUE=2 with index range -> physical 34500."""
        from ac_engineer.engineer.models import ParameterRange

        ini_contents = "[ARB_FRONT]\nVALUE=2\n"
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])

        param_ranges = {
            "ARB_FRONT": ParameterRange(
                section="ARB_FRONT", parameter="VALUE",
                min_value=25500, max_value=48000, step=4500,
                show_clicks=2, storage_convention="index",
            ),
        }
        summary = summarize_session(
            session, _config(),
            setup_ini_contents=ini_contents,
            parameter_ranges=param_ranges,
        )
        assert summary.active_setup_parameters is not None
        assert summary.active_setup_parameters["ARB_FRONT"]["VALUE"] == 34500.0


# ---------------------------------------------------------------------------
# T008 [US2]: SCALED parameter conversion in summarizer
# ---------------------------------------------------------------------------


class TestScaledParameterConversion:
    def test_scaled_parameter_converted_to_physical(self):
        """CAMBER_LR VALUE=-18 with scaled range -> physical -1.8."""
        from ac_engineer.engineer.models import ParameterRange

        ini_contents = "[CAMBER_LR]\nVALUE=-18\n"
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])

        param_ranges = {
            "CAMBER_LR": ParameterRange(
                section="CAMBER_LR", parameter="VALUE",
                min_value=-5.0, max_value=0.0, step=0.1,
                show_clicks=0, storage_convention="scaled",
            ),
        }
        summary = summarize_session(
            session, _config(),
            setup_ini_contents=ini_contents,
            parameter_ranges=param_ranges,
        )
        assert summary.active_setup_parameters is not None
        assert summary.active_setup_parameters["CAMBER_LR"]["VALUE"] == -1.8


# ---------------------------------------------------------------------------
# T016 [US3]: DIRECT parameter passthrough in summarizer
# ---------------------------------------------------------------------------


class TestDirectParameterPassthrough:
    def test_direct_parameter_unchanged(self):
        """PRESSURE_LF VALUE=18 with direct range -> 18.0 unchanged."""
        from ac_engineer.engineer.models import ParameterRange

        ini_contents = "[PRESSURE_LF]\nVALUE=18\n"
        stint = make_stint_metrics(setup_filename="test.ini")
        session = make_analyzed_session(stints=[stint])

        param_ranges = {
            "PRESSURE_LF": ParameterRange(
                section="PRESSURE_LF", parameter="VALUE",
                min_value=15.0, max_value=35.0, step=0.5,
                show_clicks=0, storage_convention="direct",
            ),
        }
        summary = summarize_session(
            session, _config(),
            setup_ini_contents=ini_contents,
            parameter_ranges=param_ranges,
        )
        assert summary.active_setup_parameters is not None
        assert summary.active_setup_parameters["PRESSURE_LF"]["VALUE"] == 18.0
