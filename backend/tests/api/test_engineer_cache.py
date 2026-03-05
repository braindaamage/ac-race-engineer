"""Tests for engineer response cache helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.engineer.models import EngineerResponse

from api.engineer.cache import load_engineer_response, save_engineer_response


def _make_response(session_id: str = "s1") -> EngineerResponse:
    return EngineerResponse(
        session_id=session_id,
        setup_changes=[],
        driver_feedback=[],
        signals_addressed=["high_understeer"],
        summary="Test summary",
        explanation="Test explanation",
        confidence="high",
    )


class TestSaveLoadRoundTrip:
    def test_save_and_load(self, tmp_path: Path) -> None:
        response = _make_response()
        save_engineer_response(tmp_path, "rec123", response)
        loaded = load_engineer_response(tmp_path, "rec123")
        assert loaded is not None
        assert loaded.session_id == "s1"
        assert loaded.summary == "Test summary"
        assert loaded.confidence == "high"
        assert loaded.signals_addressed == ["high_understeer"]

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nested"
        response = _make_response()
        path = save_engineer_response(nested, "rec1", response)
        assert path.exists()
        assert path.name == "recommendation_rec1.json"

    def test_save_returns_path(self, tmp_path: Path) -> None:
        response = _make_response()
        path = save_engineer_response(tmp_path, "rec1", response)
        assert path == tmp_path / "recommendation_rec1.json"


class TestLoadMissing:
    def test_load_returns_none_when_missing(self, tmp_path: Path) -> None:
        result = load_engineer_response(tmp_path, "nonexistent")
        assert result is None


class TestLoadCorrupted:
    def test_load_returns_none_on_bad_json(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "recommendation_bad.json"
        bad_file.write_text("not valid json{{{", encoding="utf-8")
        result = load_engineer_response(tmp_path, "bad")
        assert result is None

    def test_load_returns_none_on_invalid_data(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "recommendation_invalid.json"
        bad_file.write_text('{"wrong_field": true}', encoding="utf-8")
        result = load_engineer_response(tmp_path, "invalid")
        assert result is None
