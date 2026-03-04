"""Unit and integration tests for cache.py: save_session and load_session."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.parser.cache import load_session, save_session
from ac_engineer.parser.models import (
    CornerSegment,
    LapSegment,
    ParsedSession,
    QualityWarning,
    SessionMetadata,
    SetupEntry,
    SetupParameter,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal ParsedSession in-memory
# ---------------------------------------------------------------------------

def _make_setup(lap_start: int = 0) -> SetupEntry:
    return SetupEntry(
        lap_start=lap_start,
        trigger="session_start" if lap_start == 0 else "pit_exit",
        confidence="high",
        filename="test.ini",
        timestamp="2026-03-02T14:30:00",
        parameters=[
            SetupParameter(section="FRONT", name="CAMBER", value=-2.5),
            SetupParameter(section="REAR", name="CAMBER", value=-1.8),
        ],
    )


def _make_metadata() -> SessionMetadata:
    return SessionMetadata(
        car_name="ks_ferrari_488_gt3",
        track_name="monza",
        track_config="",
        track_length_m=5793.0,
        session_type="practice",
        tyre_compound="DHF",
        driver_name="Test Driver",
        session_start="2026-03-02T14:30:00",
        session_end="2026-03-02T15:00:00",
        laps_completed=3,
        total_samples=1500,
        sample_rate_hz=22.0,
        channels_available=["timestamp", "speed_kmh", "normalized_position"],
        channels_unavailable=["handbrake"],
        sim_info_available=True,
        reduced_mode=False,
        csv_filename="test_session.csv",
        app_version="0.2.0",
    )


def _make_lap(lap_number: int, setup: SetupEntry | None = None) -> LapSegment:
    n = 100
    data = {
        "timestamp": [1_740_000_000.0 + i * 0.045 for i in range(n)],
        "speed_kmh": [100.0 + i * 0.1 for i in range(n)],
        "normalized_position": [i / n for i in range(n)],
        "nan_channel": [None] * n,  # test NaN preservation
    }
    corner = CornerSegment(
        corner_number=1,
        entry_norm_pos=0.10,
        apex_norm_pos=0.15,
        exit_norm_pos=0.20,
        apex_speed_kmh=80.0,
        max_lat_g=1.5,
        entry_speed_kmh=130.0,
        exit_speed_kmh=110.0,
    )
    warning = QualityWarning(
        warning_type="time_series_gap",
        normalized_position=0.5,
        description="test warning",
    )
    return LapSegment(
        lap_number=lap_number,
        classification="flying" if lap_number > 0 else "outlap",
        is_invalid=False,
        start_timestamp=1_740_000_000.0 + lap_number * 90,
        end_timestamp=1_740_000_000.0 + lap_number * 90 + 89,
        start_norm_pos=0.0,
        end_norm_pos=0.99,
        sample_count=n,
        data=data,
        corners=[corner],
        active_setup=setup,
        quality_warnings=[warning],
    )


def _make_session() -> ParsedSession:
    setup = _make_setup(0)
    laps = [_make_lap(i, setup) for i in range(3)]
    return ParsedSession(
        metadata=_make_metadata(),
        setups=[setup],
        laps=laps,
    )


# ---------------------------------------------------------------------------
# Tests: save_session
# ---------------------------------------------------------------------------

class TestSaveSession:
    def test_creates_parquet_and_json(self, tmp_path):
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        assert (saved_dir / "telemetry.parquet").exists()
        assert (saved_dir / "session.json").exists()

    def test_returns_path_inside_output_dir(self, tmp_path):
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        assert saved_dir.parent == tmp_path

    def test_custom_base_name(self, tmp_path):
        session = _make_session()
        saved_dir = save_session(session, tmp_path, base_name="my_session")
        assert saved_dir.name == "my_session"

    def test_default_base_name_from_csv_filename(self, tmp_path):
        session = _make_session()
        # csv_filename = "test_session.csv" → base = "test_session"
        saved_dir = save_session(session, tmp_path)
        assert saved_dir.name == "test_session"

    def test_json_has_format_version(self, tmp_path):
        import json
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        data = json.loads((saved_dir / "session.json").read_text())
        assert data["format_version"] == "1.0"

    def test_json_has_laps_setups_session_keys(self, tmp_path):
        import json
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        data = json.loads((saved_dir / "session.json").read_text())
        assert "laps" in data
        assert "setups" in data
        assert "session" in data


# ---------------------------------------------------------------------------
# Tests: load_session
# ---------------------------------------------------------------------------

class TestLoadSession:
    def test_raises_file_not_found_for_missing_dir(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_session(tmp_path / "nonexistent")

    def test_raises_value_error_for_bad_format_version(self, tmp_path):
        import json
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        # Tamper with format_version
        json_path = saved_dir / "session.json"
        data = json.loads(json_path.read_text())
        data["format_version"] = "99.0"
        json_path.write_text(json.dumps(data))
        with pytest.raises(ValueError, match="format_version"):
            load_session(saved_dir)

    def test_raises_file_not_found_for_missing_json(self, tmp_path):
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        (saved_dir / "session.json").unlink()
        with pytest.raises(FileNotFoundError):
            load_session(saved_dir)

    def test_raises_file_not_found_for_missing_parquet(self, tmp_path):
        session = _make_session()
        saved_dir = save_session(session, tmp_path)
        (saved_dir / "telemetry.parquet").unlink()
        with pytest.raises(FileNotFoundError):
            load_session(saved_dir)


# ---------------------------------------------------------------------------
# Tests: round-trip identity
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def _roundtrip(self, session: ParsedSession, tmp_path: Path) -> ParsedSession:
        saved_dir = save_session(session, tmp_path)
        return load_session(saved_dir)

    def test_lap_count_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        assert len(reloaded.laps) == len(session.laps)

    def test_lap_numbers_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert orig.lap_number == rel.lap_number

    def test_classifications_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert orig.classification == rel.classification

    def test_is_invalid_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert orig.is_invalid == rel.is_invalid

    def test_sample_count_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert orig.sample_count == rel.sample_count

    def test_metadata_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        assert reloaded.metadata.car_name == session.metadata.car_name
        assert reloaded.metadata.track_name == session.metadata.track_name
        assert reloaded.metadata.laps_completed == session.metadata.laps_completed

    def test_setups_count_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        assert len(reloaded.setups) == len(session.setups)

    def test_setup_parameters_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        orig_params = {p.name: p.value for p in session.setups[0].parameters}
        rel_params = {p.name: p.value for p in reloaded.setups[0].parameters}
        assert orig_params == rel_params

    def test_active_setup_association_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for lap in reloaded.laps:
            if lap.active_setup is not None:
                assert lap.active_setup.lap_start == 0

    def test_corners_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert len(orig.corners) == len(rel.corners)
            if orig.corners:
                assert orig.corners[0].corner_number == rel.corners[0].corner_number
                assert abs(orig.corners[0].apex_speed_kmh - rel.corners[0].apex_speed_kmh) < 0.001

    def test_quality_warnings_preserved(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert len(orig.quality_warnings) == len(rel.quality_warnings)
            if orig.quality_warnings:
                assert orig.quality_warnings[0].warning_type == rel.quality_warnings[0].warning_type

    def test_nan_values_preserved_as_none(self, tmp_path):
        """None values in data dict should survive the Parquet round-trip as None."""
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for rel in reloaded.laps:
            if "nan_channel" in rel.data:
                values = rel.data["nan_channel"]
                # All values should be None (NaN serialized as None)
                assert all(v is None for v in values), f"Expected all None, got: {values[:5]}"

    def test_data_values_numerically_close(self, tmp_path):
        session = _make_session()
        reloaded = self._roundtrip(session, tmp_path)
        for orig, rel in zip(session.laps, reloaded.laps):
            if "speed_kmh" in orig.data and "speed_kmh" in rel.data:
                for ov, rv in zip(orig.data["speed_kmh"], rel.data["speed_kmh"]):
                    if ov is not None and rv is not None:
                        assert abs(ov - rv) < 1e-6
