"""Tests for engineer Pydantic v2 models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ac_engineer.engineer.models import (
    ChangeOutcome,
    CornerIssue,
    DriverFeedback,
    EngineerResponse,
    LapSummary,
    ParameterRange,
    SessionSummary,
    SetupChange,
    StintSummary,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# LapSummary
# ---------------------------------------------------------------------------


class TestLapSummary:
    def test_rejects_negative_gap(self):
        with pytest.raises(ValidationError, match="gap_to_best_s"):
            LapSummary(
                lap_number=1, lap_time_s=90.0, gap_to_best_s=-0.1, is_best=False
            )

    def test_accepts_zero_gap(self):
        lap = LapSummary(
            lap_number=1, lap_time_s=90.0, gap_to_best_s=0.0, is_best=True
        )
        assert lap.gap_to_best_s == 0.0

    def test_optional_fields_default_none(self):
        lap = LapSummary(
            lap_number=1, lap_time_s=90.0, gap_to_best_s=0.5, is_best=False
        )
        assert lap.tyre_temp_avg_c is None
        assert lap.understeer_ratio_avg is None
        assert lap.peak_lat_g is None
        assert lap.peak_speed_kmh is None


# ---------------------------------------------------------------------------
# CornerIssue
# ---------------------------------------------------------------------------


class TestCornerIssue:
    def test_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            CornerIssue(
                corner_number=1,
                issue_type="understeer",
                severity="critical",
                description="bad",
            )

    def test_accepts_valid_severities(self):
        for sev in ("high", "medium", "low"):
            ci = CornerIssue(
                corner_number=1,
                issue_type="understeer",
                severity=sev,
                description="test",
            )
            assert ci.severity == sev


# ---------------------------------------------------------------------------
# StintSummary
# ---------------------------------------------------------------------------


class TestStintSummary:
    def test_rejects_invalid_trend(self):
        with pytest.raises(ValidationError):
            StintSummary(
                stint_index=0,
                flying_lap_count=5,
                lap_time_trend="unknown",
            )

    def test_accepts_valid_trends(self):
        for trend in ("improving", "degrading", "stable"):
            ss = StintSummary(
                stint_index=0, flying_lap_count=5, lap_time_trend=trend
            )
            assert ss.lap_time_trend == trend

    def test_default_empty_setup_changes(self):
        ss = StintSummary(
            stint_index=0, flying_lap_count=5, lap_time_trend="stable"
        )
        assert ss.setup_changes_from_prev == []


# ---------------------------------------------------------------------------
# ParameterRange
# ---------------------------------------------------------------------------


class TestParameterRange:
    def test_rejects_min_gt_max(self):
        with pytest.raises(ValidationError, match="min_value"):
            ParameterRange(
                section="CAM", parameter="VALUE",
                min_value=5.0, max_value=2.0, step=0.1,
            )

    def test_rejects_step_zero(self):
        with pytest.raises(ValidationError, match="step"):
            ParameterRange(
                section="CAM", parameter="VALUE",
                min_value=0.0, max_value=5.0, step=0.0,
            )

    def test_rejects_step_negative(self):
        with pytest.raises(ValidationError, match="step"):
            ParameterRange(
                section="CAM", parameter="VALUE",
                min_value=0.0, max_value=5.0, step=-1.0,
            )

    def test_accepts_valid_range_no_default(self):
        pr = ParameterRange(
            section="CAMBER_LF", parameter="VALUE",
            min_value=-5.0, max_value=0.0, step=0.1,
        )
        assert pr.default_value is None

    def test_accepts_equal_min_max(self):
        pr = ParameterRange(
            section="FIXED", parameter="VALUE",
            min_value=3.0, max_value=3.0, step=1.0,
        )
        assert pr.min_value == pr.max_value


# ---------------------------------------------------------------------------
# SetupChange / DriverFeedback / EngineerResponse
# ---------------------------------------------------------------------------


class TestSetupChange:
    def test_rejects_invalid_confidence(self):
        with pytest.raises(ValidationError):
            SetupChange(
                section="CAM", parameter="Camber",
                value_after=-2.0, reasoning="r", expected_effect="e",
                confidence="very_high",
            )


class TestDriverFeedback:
    def test_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            DriverFeedback(
                area="braking", observation="o", suggestion="s",
                severity="extreme",
            )


class TestEngineerResponse:
    def test_rejects_invalid_confidence(self):
        with pytest.raises(ValidationError):
            EngineerResponse(
                session_id="s1", summary="s", explanation="e",
                confidence="none",
            )

    def test_accepts_valid_response(self):
        er = EngineerResponse(
            session_id="s1", summary="s", explanation="e", confidence="high",
        )
        assert er.setup_changes == []
        assert er.driver_feedback == []
        assert er.signals_addressed == []


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_accepts_valid_with_no_clamp(self):
        vr = ValidationResult(
            section="CAM", parameter="VALUE",
            proposed_value=-2.0, is_valid=True,
        )
        assert vr.clamped_value is None
        assert vr.warning is None

    def test_accepts_clamped_result(self):
        vr = ValidationResult(
            section="CAM", parameter="VALUE",
            proposed_value=-7.0, clamped_value=-5.0, is_valid=False,
            warning="Out of range",
        )
        assert vr.clamped_value == -5.0


# ---------------------------------------------------------------------------
# SessionSummary serialization
# ---------------------------------------------------------------------------


class TestSessionSummary:
    def test_exclude_none_omits_fields(self):
        ss = SessionSummary(
            session_id="s1", car_name="car", track_name="track",
            total_lap_count=10, flying_lap_count=8,
        )
        dumped = ss.model_dump(exclude_none=True)
        assert "track_config" not in dumped
        assert "tyre_temp_averages" not in dumped
        assert "car_name" in dumped


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_lap_summary_roundtrip(self):
        orig = LapSummary(
            lap_number=1, lap_time_s=90.0, gap_to_best_s=0.5,
            is_best=False, tyre_temp_avg_c=80.0,
        )
        restored = LapSummary.model_validate(orig.model_dump())
        assert restored == orig

    def test_parameter_range_roundtrip(self):
        orig = ParameterRange(
            section="CAM", parameter="VALUE",
            min_value=-5.0, max_value=0.0, step=0.1, default_value=-2.5,
        )
        restored = ParameterRange.model_validate(orig.model_dump())
        assert restored == orig

    def test_engineer_response_roundtrip(self):
        orig = EngineerResponse(
            session_id="s1",
            setup_changes=[
                SetupChange(
                    section="CAM", parameter="Camber LF",
                    value_before=-1.5, value_after=-2.0,
                    reasoning="more grip", expected_effect="better turn-in",
                    confidence="high",
                ),
            ],
            driver_feedback=[
                DriverFeedback(
                    area="braking", observation="late braking",
                    suggestion="brake earlier", corners_affected=[3, 7],
                    severity="medium",
                ),
            ],
            signals_addressed=["high_understeer"],
            summary="Adjusted camber",
            explanation="Full explanation here",
            confidence="high",
        )
        restored = EngineerResponse.model_validate(orig.model_dump())
        assert restored == orig
