"""Unit tests for writer module."""
import csv
import json
import os

from writer import (
    generate_filename, ensure_output_dir, write_csv_header,
    append_csv_rows, write_metadata, write_early_metadata, write_final_metadata,
)
from channels import HEADER


class TestGenerateFilename:
    def test_produces_correct_pattern(self):
        # Use a fixed timestamp: 2026-03-02 14:30:00
        import time
        ts = time.mktime(time.strptime("2026-03-02 14:30:00", "%Y-%m-%d %H:%M:%S"))
        name = generate_filename("ks_ferrari_488_gt3", "monza", ts)
        assert name == "2026-03-02_1430_ks_ferrari_488_gt3_monza"

    def test_sanitizes_car_and_track(self):
        import time
        ts = time.mktime(time.strptime("2026-01-15 09:05:00", "%Y-%m-%d %H:%M:%S"))
        name = generate_filename("My Car (v2)", "Nürburg Ring", ts)
        assert "my_car_v2" in name
        assert "n_rburg_ring" in name

    def test_empty_car_uses_unknown(self):
        name = generate_filename("", "monza")
        assert "unknown" in name

    def test_empty_track_uses_unknown(self):
        name = generate_filename("car", "")
        assert "unknown" in name


class TestCSVWriter:
    def test_header_matches_contract(self, tmp_path):
        filepath = str(tmp_path / "test.csv")
        write_csv_header(filepath, HEADER)
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == HEADER
        assert len(header) == len(HEADER)

    def test_append_rows_produce_valid_csv(self, tmp_path):
        filepath = str(tmp_path / "test.csv")
        write_csv_header(filepath, ["a", "b", "c"])
        append_csv_rows(filepath, [[1, 2, 3], [4, 5, 6]])
        with open(filepath, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 3  # header + 2 data rows
        assert rows[1] == ["1", "2", "3"]
        assert rows[2] == ["4", "5", "6"]


class TestMetadataWriter:
    def test_json_has_all_required_fields(self, tmp_path):
        filepath = str(tmp_path / "test.meta.json")
        meta = {
            "app_version": "0.1.0",
            "session_start": "2026-03-02T14:30:00",
            "session_end": "2026-03-02T15:00:00",
            "car_name": "test_car",
            "track_name": "test_track",
            "track_config": "",
            "track_length_m": 5000.0,
            "session_type": "practice",
            "tyre_compound": "Soft",
            "laps_completed": 10,
            "total_samples": 25000,
            "sample_rate_hz": 25.0,
            "air_temp_c": 24.0,
            "road_temp_c": 32.0,
            "driver_name": "Test",
            "setup_filename": None,
            "setup_contents": None,
            "setup_confidence": None,
            "channels_available": ["throttle"],
            "channels_unavailable": ["handbrake"],
            "sim_info_available": True,
            "reduced_mode": False,
            "tyre_temp_zones_validated": True,
            "csv_filename": "test.csv",
        }
        write_metadata(filepath, meta)
        with open(filepath, "r") as f:
            loaded = json.load(f)
        required = [
            "app_version", "session_start", "session_end", "car_name",
            "track_name", "session_type", "csv_filename",
            "channels_available", "channels_unavailable",
            "sim_info_available", "reduced_mode", "tyre_temp_zones_validated",
        ]
        for key in required:
            assert key in loaded, "Missing key: %s" % key

    def test_write_early_metadata_has_null_deferred_fields(self, tmp_path):
        filepath = str(tmp_path / "test.meta.json")
        meta = {
            "app_version": "0.1.0",
            "session_start": "2026-03-02T14:30:00",
            "session_end": "2026-03-02T15:00:00",
            "car_name": "test_car",
            "track_name": "test_track",
            "laps_completed": 10,
            "total_samples": 25000,
            "sample_rate_hz": 25.0,
        }
        write_early_metadata(filepath, meta)
        with open(filepath, "r") as f:
            loaded = json.load(f)
        assert loaded["session_end"] is None
        assert loaded["laps_completed"] is None
        assert loaded["total_samples"] is None
        assert loaded["sample_rate_hz"] is None

    def test_write_final_metadata_has_all_fields(self, tmp_path):
        filepath = str(tmp_path / "test.meta.json")
        meta = {
            "app_version": "0.1.0",
            "session_end": "2026-03-02T15:00:00",
            "laps_completed": 10,
            "total_samples": 25000,
            "sample_rate_hz": 25.0,
        }
        write_final_metadata(filepath, meta)
        with open(filepath, "r") as f:
            loaded = json.load(f)
        assert loaded["session_end"] == "2026-03-02T15:00:00"
        assert loaded["laps_completed"] == 10
        assert loaded["total_samples"] == 25000


class TestEnsureOutputDir:
    def test_creates_nested_directories(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c")
        ensure_output_dir(nested)
        assert os.path.isdir(nested)


class TestFilenameEdgeCases:
    """T037/T038: Filename edge cases."""

    def test_long_name_truncation(self):
        long_name = "a" * 100
        name = generate_filename(long_name, "track")
        # Car part should be truncated to 50 chars
        parts = name.split("_")
        # date_time_car_track: car starts at index 2
        car_part = "_".join(parts[2:-1])  # everything between time and last part
        assert len(car_part) <= 50

    def test_special_chars_only_uses_unknown(self):
        name = generate_filename("@#$%", "!@#")
        assert "unknown" in name

    def test_two_filenames_one_minute_apart_are_unique(self):
        import time
        ts1 = time.mktime(time.strptime("2026-03-02 14:30:00", "%Y-%m-%d %H:%M:%S"))
        ts2 = time.mktime(time.strptime("2026-03-02 14:31:00", "%Y-%m-%d %H:%M:%S"))
        name1 = generate_filename("car", "track", ts1)
        name2 = generate_filename("car", "track", ts2)
        assert name1 != name2
