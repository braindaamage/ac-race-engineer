"""Tests for recommendation CRUD operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.storage.models import SessionRecord, SetupChange
from ac_engineer.storage.recommendations import (
    get_recommendations,
    save_recommendation,
    update_recommendation_status,
)
from ac_engineer.storage.sessions import save_session


def _setup_session(db_path: Path, session_id: str = "sess1") -> None:
    save_session(
        db_path,
        SessionRecord(
            session_id=session_id,
            car="ferrari",
            track="monza",
            session_date="2026-03-04T14:00:00",
            lap_count=10,
        ),
    )


def _sample_changes() -> list[SetupChange]:
    return [
        SetupChange(
            section="ARB",
            parameter="FRONT",
            old_value="5",
            new_value="3",
            reasoning="Reduce understeer",
        ),
        SetupChange(
            section="TYRES",
            parameter="PRESSURE_LF",
            old_value="26.0",
            new_value="25.5",
            reasoning="Improve front grip",
        ),
    ]


class TestSaveRecommendation:
    def test_creates_with_proposed_status(self, db_path: Path) -> None:
        _setup_session(db_path)
        rec = save_recommendation(db_path, "sess1", "Fix understeer", _sample_changes())
        assert rec.status == "proposed"
        assert rec.recommendation_id  # non-empty
        assert rec.created_at  # non-empty
        assert len(rec.changes) == 2

    def test_auto_generates_ids(self, db_path: Path) -> None:
        _setup_session(db_path)
        rec = save_recommendation(db_path, "sess1", "Summary", _sample_changes())
        assert len(rec.recommendation_id) == 32  # uuid4 hex
        for change in rec.changes:
            assert len(change.change_id) == 32
            assert change.recommendation_id == rec.recommendation_id

    def test_invalid_session_raises(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="Session not found"):
            save_recommendation(db_path, "nonexistent", "Summary", _sample_changes())


class TestGetRecommendations:
    def test_returns_with_changes(self, db_path: Path) -> None:
        _setup_session(db_path)
        save_recommendation(db_path, "sess1", "Rec 1", _sample_changes())
        recs = get_recommendations(db_path, "sess1")
        assert len(recs) == 1
        assert len(recs[0].changes) == 2

    def test_empty_returns_empty(self, db_path: Path) -> None:
        _setup_session(db_path)
        assert get_recommendations(db_path, "sess1") == []


class TestUpdateRecommendationStatus:
    def test_update_to_applied(self, db_path: Path) -> None:
        _setup_session(db_path)
        rec = save_recommendation(db_path, "sess1", "Summary", _sample_changes())
        update_recommendation_status(db_path, rec.recommendation_id, "applied")
        recs = get_recommendations(db_path, "sess1")
        assert recs[0].status == "applied"

    def test_update_to_rejected(self, db_path: Path) -> None:
        _setup_session(db_path)
        rec = save_recommendation(db_path, "sess1", "Summary", _sample_changes())
        update_recommendation_status(db_path, rec.recommendation_id, "rejected")
        recs = get_recommendations(db_path, "sess1")
        assert recs[0].status == "rejected"

    def test_invalid_id_raises(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="Recommendation not found"):
            update_recommendation_status(db_path, "nonexistent", "applied")

    def test_invalid_status_raises(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="Status must be"):
            update_recommendation_status(db_path, "any_id", "invalid")


class TestExplanationColumn:
    """Tests for the explanation column on recommendations (Phase 12)."""

    def test_save_recommendation_persists_explanation(self, db_path: Path) -> None:
        _setup_session(db_path)
        rec = save_recommendation(
            db_path, "sess1", "Summary", _sample_changes(),
            explanation="Detailed narrative explanation.",
        )
        assert rec.explanation == "Detailed narrative explanation."

    def test_get_recommendations_returns_explanation(self, db_path: Path) -> None:
        _setup_session(db_path)
        save_recommendation(
            db_path, "sess1", "Summary", _sample_changes(),
            explanation="Multi-paragraph explanation.",
        )
        recs = get_recommendations(db_path, "sess1")
        assert len(recs) == 1
        assert recs[0].explanation == "Multi-paragraph explanation."

    def test_default_empty_string_when_no_explanation(self, db_path: Path) -> None:
        _setup_session(db_path)
        rec = save_recommendation(db_path, "sess1", "Summary", _sample_changes())
        assert rec.explanation == ""

    def test_legacy_rows_have_empty_explanation(self, db_path: Path) -> None:
        """Rows created before the migration have explanation = ''."""
        _setup_session(db_path)
        save_recommendation(db_path, "sess1", "Summary", _sample_changes())
        recs = get_recommendations(db_path, "sess1")
        assert recs[0].explanation == ""
