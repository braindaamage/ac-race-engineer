from __future__ import annotations

import os
import struct
from pathlib import Path

from ac_engineer.acd_reader import AcdResult, read_acd

# build_acd is imported from conftest via sys.path manipulation by pytest
# We access it through a fixture instead
from tests.acd_reader.conftest import build_acd


class TestReadAcdSuccess:
    """US1: Successful extraction tests."""

    def test_extracts_all_files(self, tmp_path, sample_car_name, sample_entries):
        acd_data = build_acd(sample_entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)

        result = read_acd(acd_path, sample_car_name)

        assert result.ok is True
        assert result.error is None
        assert set(result.files.keys()) == set(sample_entries.keys())

    def test_content_fidelity(self, tmp_path, sample_car_name, sample_entries):
        acd_data = build_acd(sample_entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)

        result = read_acd(acd_path, sample_car_name)

        assert result.ok is True
        for name, content in sample_entries.items():
            assert result.files[name] == content, f"Content mismatch for {name}"

    def test_single_file_archive(self, tmp_path, sample_car_name):
        entries = {"car.ini": b"[HEADER]\nVERSION=1\n"}
        acd_data = build_acd(entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)

        result = read_acd(acd_path, sample_car_name)

        assert result.ok is True
        assert len(result.files) == 1
        assert result.files["car.ini"] == b"[HEADER]\nVERSION=1\n"

    def test_empty_archive(self, tmp_path, sample_car_name):
        acd_path = tmp_path / "data.acd"
        # An empty archive is just a file with no entries but nonzero size
        # Write a single null byte so it's not empty (empty file is a different error)
        # Actually, build_acd with empty dict produces b"" which is 0 bytes.
        # We need the file to be non-empty for it to pass the size check.
        # Per task: "empty bytes or just EOF" → but the file must not be 0 bytes
        # since that triggers "File is empty". Let's write a minimal non-empty
        # file that has no valid entries. Actually, let's test build_acd({}).
        acd_data = build_acd({}, sample_car_name)
        if len(acd_data) == 0:
            # Empty archive produces 0 bytes, which hits "File is empty".
            # This is correct behavior — an empty file IS empty.
            acd_path.write_bytes(b"\x00")
            result = read_acd(acd_path, sample_car_name)
            # A single null byte can't be parsed as a valid entry
            assert result.ok is False
            return

        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, sample_car_name)
        assert result.ok is True
        assert result.files == {}

    def test_read_only_operation(self, tmp_path, sample_car_name, sample_entries):
        acd_data = build_acd(sample_entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        files_before = set(tmp_path.iterdir())

        read_acd(acd_path, sample_car_name)

        files_after = set(tmp_path.iterdir())
        assert files_before == files_after, "read_acd should not create new files"


class TestReadAcdFailure:
    """US2: Failure mode tests."""

    def test_file_not_found(self, tmp_path):
        result = read_acd(tmp_path / "nonexistent.acd", "some_car")
        assert result.ok is False
        assert result.files == {}
        assert "File not found" in result.error

    def test_path_is_directory(self, tmp_path):
        result = read_acd(tmp_path, "some_car")
        assert result.ok is False
        assert result.files == {}
        assert "Not a file" in result.error

    def test_empty_file(self, tmp_path):
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(b"")
        result = read_acd(acd_path, "some_car")
        assert result.ok is False
        assert result.files == {}
        assert "File is empty" in result.error

    def test_empty_car_name(self, tmp_path, sample_entries):
        acd_data = build_acd(sample_entries, "dummy")
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, "")
        assert result.ok is False
        assert result.files == {}
        assert "Invalid car name" in result.error

    def test_whitespace_car_name(self, tmp_path, sample_entries):
        acd_data = build_acd(sample_entries, "dummy")
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, "  ")
        assert result.ok is False
        assert result.files == {}
        assert "Invalid car name" in result.error

    def test_truncated_archive(self, tmp_path, sample_car_name, sample_entries):
        acd_data = build_acd(sample_entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data[:10])
        result = read_acd(acd_path, sample_car_name)
        assert result.ok is False
        assert result.files == {}
        assert "Corrupted archive" in result.error

    def test_unsupported_encryption(self, tmp_path):
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(os.urandom(200))
        result = read_acd(acd_path, "some_car")
        assert result.ok is False
        assert result.error is not None
        assert len(result.error) > 0

    def test_negative_entry_size(self, tmp_path, sample_car_name):
        # Craft bytes with valid filename length but negative content size
        fname = b"car.ini"
        data = struct.pack("<i", len(fname)) + fname + struct.pack("<i", -1)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(data)
        result = read_acd(acd_path, sample_car_name)
        assert result.ok is False
        assert result.files == {}
        assert "Corrupted archive" in result.error


class TestReadAcdDiverse:
    """US3: Diverse car names and file contents."""

    def test_car_name_with_parentheses(self, tmp_path, sample_entries):
        name = "ks_ferrari_488_gt3_(2018)"
        acd_data = build_acd(sample_entries, name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, name)
        assert result.ok is True
        assert set(result.files.keys()) == set(sample_entries.keys())

    def test_car_name_with_spaces(self, tmp_path, sample_entries):
        name = "my custom car"
        acd_data = build_acd(sample_entries, name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, name)
        assert result.ok is True

    def test_car_name_with_accents(self, tmp_path, sample_entries):
        name = "coche_rápido"
        acd_data = build_acd(sample_entries, name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, name)
        assert result.ok is True

    def test_car_name_with_unicode(self, tmp_path, sample_entries):
        name = "車_mod_01"
        acd_data = build_acd(sample_entries, name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, name)
        assert result.ok is True

    def test_archive_with_lut_file(self, tmp_path, sample_car_name):
        entries = {"power.lut": b"0|0\n1000|50\n2000|120\n"}
        acd_data = build_acd(entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, sample_car_name)
        assert result.ok is True
        assert "power.lut" in result.files

    def test_archive_with_mixed_extensions(self, tmp_path, sample_car_name):
        entries = {
            "car.ini": b"[HEADER]\nVERSION=1\n",
            "power.lut": b"0|0\n100|50\n",
            "readme.txt": b"Some readme text\n",
            "data": b"extensionless file content\n",
        }
        acd_data = build_acd(entries, sample_car_name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, sample_car_name)
        assert result.ok is True
        assert set(result.files.keys()) == set(entries.keys())

    def test_long_car_name(self, tmp_path, sample_entries):
        name = "a" * 120
        acd_data = build_acd(sample_entries, name)
        acd_path = tmp_path / "data.acd"
        acd_path.write_bytes(acd_data)
        result = read_acd(acd_path, name)
        assert result.ok is True
