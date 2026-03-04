"""Tests for Pydantic v2 models in ac_engineer.parser.models."""

import math

import pandas as pd
import pytest

from ac_engineer.parser.models import (
    CornerSegment,
    LapClassification,
    LapSegment,
    ParsedSession,
    ParserError,
    QualityWarning,
    SessionMetadata,
    SetupEntry,
    SetupParameter,
    WarnType,
)


# ---------------------------------------------------------------------------
# QualityWarning
# ---------------------------------------------------------------------------

class TestQualityWarning:
    def test_valid_construction(self):
        w = QualityWarning(
            warning_type="time_series_gap",
            normalized_position=0.5,
            description="Gap of 1.2s detected",
        )
        assert w.warning_type == "time_series_gap"
        assert w.normalized_position == 0.5
        assert w.description == "Gap of 1.2s detected"

    def test_all_warn_types_accepted(self):
        types: list[WarnType] = [
            "time_series_gap", "position_jump", "zero_speed_mid_lap",
            "incomplete", "duplicate_timestamp",
        ]
        for wt in types:
            w = QualityWarning(warning_type=wt, normalized_position=0.0, description="x")
            assert w.warning_type == wt

    def test_invalid_warn_type_rejected(self):
        with pytest.raises(Exception):
            QualityWarning(warning_type="unknown_type", normalized_position=0.0, description="x")


# ---------------------------------------------------------------------------
# SetupParameter
# ---------------------------------------------------------------------------

class TestSetupParameter:
    def test_float_value(self):
        p = SetupParameter(section="FRONT", name="CAMBER", value=-2.5)
        assert isinstance(p.value, float)
        assert p.value == -2.5

    def test_string_value(self):
        p = SetupParameter(section="TYRES", name="COMPOUND", value="SOFT")
        assert isinstance(p.value, str)
        assert p.value == "SOFT"

    def test_section_and_name_preserved(self):
        p = SetupParameter(section="MY_SECTION", name="my_param", value=1.0)
        assert p.section == "MY_SECTION"
        assert p.name == "my_param"


# ---------------------------------------------------------------------------
# SetupEntry
# ---------------------------------------------------------------------------

class TestSetupEntry:
    def test_valid_construction(self):
        e = SetupEntry(
            lap_start=0,
            trigger="session_start",
            confidence="high",
            filename="test.ini",
            timestamp="2026-03-02T14:30:00",
            parameters=[SetupParameter(section="FRONT", name="CAMBER", value=-2.5)],
        )
        assert e.lap_start == 0
        assert len(e.parameters) == 1

    def test_optional_fields_default_none(self):
        e = SetupEntry(
            lap_start=5,
            trigger="pit_exit",
            timestamp="2026-03-02T14:45:00",
        )
        assert e.confidence is None
        assert e.filename is None
        assert e.parameters == []


# ---------------------------------------------------------------------------
# CornerSegment
# ---------------------------------------------------------------------------

class TestCornerSegment:
    def test_valid_construction(self):
        c = CornerSegment(
            corner_number=1,
            entry_norm_pos=0.10,
            apex_norm_pos=0.15,
            exit_norm_pos=0.20,
            apex_speed_kmh=80.0,
            max_lat_g=1.5,
            entry_speed_kmh=130.0,
            exit_speed_kmh=110.0,
        )
        assert c.corner_number == 1
        assert c.apex_speed_kmh == 80.0


# ---------------------------------------------------------------------------
# LapSegment
# ---------------------------------------------------------------------------

class TestLapSegment:
    def _make_lap(self, classification: LapClassification = "flying", is_invalid: bool = False):
        return LapSegment(
            lap_number=1,
            classification=classification,
            is_invalid=is_invalid,
            start_timestamp=1_740_000_100.0,
            end_timestamp=1_740_000_190.0,
            start_norm_pos=0.0,
            end_norm_pos=0.99,
            sample_count=10,
            data={"speed_kmh": [100.0, 110.0, 120.0, 130.0, 140.0, 130.0, 120.0, 110.0, 100.0, 90.0]},
        )

    def test_default_is_invalid_false(self):
        lap = self._make_lap()
        assert lap.is_invalid is False

    def test_is_invalid_true_independent_of_classification(self):
        lap = self._make_lap(classification="outlap", is_invalid=True)
        assert lap.classification == "outlap"
        assert lap.is_invalid is True

    def test_to_dataframe_roundtrip(self):
        lap = self._make_lap()
        df = lap.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["speed_kmh"]
        assert len(df) == 10
        assert df["speed_kmh"].iloc[0] == 100.0

    def test_all_classifications_accepted(self):
        for cls in ["flying", "outlap", "inlap", "invalid", "incomplete"]:
            lap = self._make_lap(classification=cls)
            assert lap.classification == cls

    def test_invalid_classification_rejected(self):
        with pytest.raises(Exception):
            LapSegment(
                lap_number=1,
                classification="unknown",
                start_timestamp=1.0,
                end_timestamp=2.0,
                start_norm_pos=0.0,
                end_norm_pos=0.99,
                sample_count=1,
                data={},
            )

    def test_corners_and_warnings_default_empty(self):
        lap = self._make_lap()
        assert lap.corners == []
        assert lap.quality_warnings == []


# ---------------------------------------------------------------------------
# SessionMetadata
# ---------------------------------------------------------------------------

class TestSessionMetadata:
    def test_nullable_fields(self):
        meta = SessionMetadata(
            car_name="test_car",
            track_name="monza",
            track_config="",
            session_type="practice",
            tyre_compound="DHF",
            driver_name="Test",
            session_start="2026-03-02T14:30:00",
            csv_filename="test.csv",
            app_version="0.2.0",
        )
        assert meta.track_length_m is None
        assert meta.session_end is None
        assert meta.laps_completed is None
        assert meta.total_samples is None
        assert meta.sample_rate_hz is None


# ---------------------------------------------------------------------------
# ParsedSession
# ---------------------------------------------------------------------------

class TestParsedSession:
    def _make_session(self) -> ParsedSession:
        meta = SessionMetadata(
            car_name="test_car",
            track_name="monza",
            track_config="",
            session_type="practice",
            tyre_compound="DHF",
            driver_name="Test",
            session_start="2026-03-02T14:30:00",
            csv_filename="test.csv",
            app_version="0.2.0",
        )

        def _lap(number, cls):
            return LapSegment(
                lap_number=number,
                classification=cls,
                start_timestamp=float(number * 100),
                end_timestamp=float(number * 100 + 90),
                start_norm_pos=0.0,
                end_norm_pos=0.99,
                sample_count=100,
                data={},
            )

        laps = [
            _lap(0, "outlap"),
            _lap(1, "flying"),
            _lap(2, "flying"),
            _lap(3, "inlap"),
        ]
        return ParsedSession(metadata=meta, laps=laps)

    def test_flying_laps_property(self):
        session = self._make_session()
        flying = session.flying_laps
        assert len(flying) == 2
        assert all(l.classification == "flying" for l in flying)

    def test_lap_by_number_found(self):
        session = self._make_session()
        lap = session.lap_by_number(1)
        assert lap is not None
        assert lap.lap_number == 1

    def test_lap_by_number_not_found(self):
        session = self._make_session()
        assert session.lap_by_number(99) is None

    def test_flying_laps_empty_when_none(self):
        meta = SessionMetadata(
            car_name="c", track_name="t", track_config="",
            session_type="practice", tyre_compound="DHF", driver_name="D",
            session_start="2026-01-01T00:00:00", csv_filename="x.csv", app_version="0.2.0",
        )
        session = ParsedSession(metadata=meta)
        assert session.flying_laps == []


# ---------------------------------------------------------------------------
# ParserError
# ---------------------------------------------------------------------------

class TestParserError:
    def test_is_exception(self):
        err = ParserError("something went wrong")
        assert isinstance(err, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ParserError, match="structural error"):
            raise ParserError("structural error")
