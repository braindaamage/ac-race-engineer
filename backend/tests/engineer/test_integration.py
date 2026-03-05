"""End-to-end integration tests for the AI engineer pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from ac_engineer.config import ACConfig
from ac_engineer.engineer.agents import (
    _build_specialist_agent,
    _build_user_prompt,
    _combine_results,
    _post_validate_changes,
    _resolve_conflicts,
    analyze_with_engineer,
    route_signals,
)
from ac_engineer.engineer.models import (
    AgentDeps,
    DriverFeedback,
    EngineerResponse,
    LapSummary,
    ParameterRange,
    SessionSummary,
    SetupChange,
    SpecialistResult,
    StintSummary,
)


def _make_function_model(domain: str = "balance"):
    """Create a FunctionModel returning valid SpecialistResult."""
    from pydantic_ai.messages import ModelResponse, TextPart

    def handler(messages, info):
        if domain == "technique":
            text = '{"setup_changes": [], "driver_feedback": [{"area": "Consistency", "observation": "test", "suggestion": "test", "corners_affected": [1], "severity": "medium"}], "domain_summary": "Technique analysis"}'
        else:
            text = '{"setup_changes": [{"section": "ARB_FRONT", "parameter": "VALUE", "value_after": 2.0, "reasoning": "test", "expected_effect": "test", "confidence": "high"}], "driver_feedback": [], "domain_summary": "Analysis done"}'
        return ModelResponse(parts=[TextPart(content=text)])
    return FunctionModel(handler)


# ===================================================================
# T019: analyze_with_engineer integration tests (~5 tests)
# ===================================================================


class TestAnalyzeWithEngineer:
    """Integration tests for the main orchestrator."""

    @pytest.mark.asyncio
    async def test_no_flying_laps_returns_insufficient_data(self, tmp_path):
        """Session with no flying laps → insufficient data response."""
        summary = SessionSummary(
            session_id="test_no_laps",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=2,
            flying_lap_count=0,
        )
        config = ACConfig(ac_install_path=tmp_path)
        db_path = tmp_path / "test.db"

        response = await analyze_with_engineer(summary, config, db_path)

        assert response.confidence == "low"
        assert "insufficient" in response.summary.lower() or "no flying" in response.summary.lower()
        assert response.setup_changes == []

    @pytest.mark.asyncio
    async def test_no_signals_returns_positive_summary(self, tmp_path):
        """Session with no detected signals → positive summary, no changes."""
        summary = SessionSummary(
            session_id="test_no_signals",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=5,
            flying_lap_count=3,
            best_lap_time_s=89.5,
            signals=[],
            laps=[
                LapSummary(lap_number=2, lap_time_s=89.5, gap_to_best_s=0.0, is_best=True),
            ],
        )
        config = ACConfig(ac_install_path=tmp_path)
        db_path = tmp_path / "test.db"

        response = await analyze_with_engineer(summary, config, db_path)

        assert response.confidence == "high"
        assert "no issues" in response.summary.lower() or "well-balanced" in response.summary.lower()
        assert response.setup_changes == []

    @pytest.mark.asyncio
    async def test_balance_signals_only_runs_balance_agent(
        self, sample_session_summary, tmp_path
    ):
        """Session with only balance signals → only balance agent runs."""
        summary = sample_session_summary.model_copy(
            update={"signals": ["high_understeer"], "active_setup_parameters": None}
        )
        config = ACConfig(ac_install_path=tmp_path)
        db_path = tmp_path / "test.db"

        real_agent = _build_specialist_agent("balance", "test")
        with real_agent.override(model=_make_function_model("balance")):
            with patch("ac_engineer.engineer.agents._build_specialist_agent", return_value=real_agent):
                with patch("ac_engineer.storage.recommendations.save_recommendation"):
                    response = await analyze_with_engineer(summary, config, db_path)

        assert isinstance(response, EngineerResponse)
        assert response.session_id == summary.session_id

    @pytest.mark.asyncio
    async def test_multiple_domains_all_run(self, sample_session_summary, tmp_path):
        """Session with balance + tyre signals → both agents run."""
        summary = sample_session_summary.model_copy(
            update={
                "signals": ["high_understeer", "tyre_temp_spread_high"],
                "active_setup_parameters": None,
            }
        )
        config = ACConfig(ac_install_path=tmp_path)
        db_path = tmp_path / "test.db"

        domains = route_signals(summary.signals, summary.active_setup_parameters)
        assert "balance" in domains
        assert "tyre" in domains

    @pytest.mark.asyncio
    async def test_all_specialists_fail_returns_error_response(
        self, sample_session_summary, tmp_path
    ):
        """When all specialist agents fail → error response with low confidence."""
        summary = sample_session_summary.model_copy(
            update={"signals": ["high_understeer"], "active_setup_parameters": None}
        )
        config = ACConfig(ac_install_path=tmp_path)
        db_path = tmp_path / "test.db"

        with patch(
            "ac_engineer.engineer.agents._build_specialist_agent",
            side_effect=RuntimeError("Agent creation failed"),
        ):
            response = await analyze_with_engineer(summary, config, db_path)

        assert response.confidence == "low"
        assert "error" in response.summary.lower() or "could not" in response.summary.lower()


# ===================================================================
# T020: _combine_results and _build_user_prompt tests (~4 tests)
# ===================================================================


class TestCombineResults:
    """Tests for combining specialist results into EngineerResponse."""

    def test_multiple_specialists_merged(self):
        """Multiple specialist results are merged correctly."""
        results = {
            "balance": SpecialistResult(
                setup_changes=[
                    SetupChange(
                        section="ARB_FRONT", parameter="VALUE",
                        value_after=2.0, reasoning="Less front ARB",
                        expected_effect="Better turn-in", confidence="high",
                    ),
                ],
                driver_feedback=[],
                domain_summary="Front ARB reduction recommended",
            ),
            "tyre": SpecialistResult(
                setup_changes=[
                    SetupChange(
                        section="PRESSURE_LF", parameter="VALUE",
                        value_after=27.0, reasoning="Increase pressure",
                        expected_effect="Lower temps", confidence="medium",
                    ),
                ],
                driver_feedback=[],
                domain_summary="Pressure adjustment needed",
            ),
        }

        summary = SessionSummary(
            session_id="test",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=5,
            flying_lap_count=3,
            signals=["high_understeer", "tyre_temp_spread_high"],
        )

        response = _combine_results("test", results, summary)

        assert len(response.setup_changes) == 2
        assert response.setup_changes[0].section == "ARB_FRONT"  # Balance first (priority)
        assert response.setup_changes[1].section == "PRESSURE_LF"
        assert "Balance" in response.summary
        assert "Tyre" in response.summary

    def test_signals_addressed_populated(self):
        """signals_addressed includes exactly the analyzed signals."""
        results = {
            "balance": SpecialistResult(
                setup_changes=[
                    SetupChange(
                        section="ARB_FRONT", parameter="VALUE",
                        value_after=2.0, reasoning="test", expected_effect="test",
                        confidence="high",
                    ),
                ],
                driver_feedback=[],
                domain_summary="test",
            ),
        }

        summary = SessionSummary(
            session_id="test",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=5,
            flying_lap_count=3,
            signals=["high_understeer", "tyre_temp_spread_high"],
        )

        response = _combine_results("test", results, summary)
        assert "high_understeer" in response.signals_addressed
        # tyre_temp_spread_high NOT addressed since no tyre specialist ran
        assert "tyre_temp_spread_high" not in response.signals_addressed

    def test_technique_feedback_included(self):
        """Technique specialist feedback is included in response."""
        results = {
            "technique": SpecialistResult(
                setup_changes=[],
                driver_feedback=[
                    DriverFeedback(
                        area="Consistency",
                        observation="Lap times vary by 1.5s",
                        suggestion="Focus on braking points",
                        corners_affected=[3, 7],
                        severity="medium",
                    ),
                ],
                domain_summary="Consistency needs improvement",
            ),
        }

        summary = SessionSummary(
            session_id="test",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=5,
            flying_lap_count=3,
            signals=["low_consistency"],
        )

        response = _combine_results("test", results, summary)
        assert len(response.driver_feedback) == 1
        assert response.driver_feedback[0].area == "Consistency"

    def test_empty_specialists_returns_no_findings(self):
        """No specialist results → 'No specialist findings' summary."""
        response = _combine_results(
            "test",
            {},
            SessionSummary(
                session_id="test",
                car_name="test_car",
                track_name="test_track",
                total_lap_count=5,
                flying_lap_count=3,
                signals=[],
            ),
        )
        assert "No specialist findings" in response.summary


class TestBuildUserPrompt:
    """Tests for user prompt building."""

    def test_includes_session_info(self, sample_session_summary):
        prompt = _build_user_prompt(sample_session_summary, ["high_understeer"])
        assert "test_car" in prompt
        assert "test_track" in prompt
        assert "89.5" in prompt

    def test_includes_domain_signals(self, sample_session_summary):
        prompt = _build_user_prompt(
            sample_session_summary,
            ["high_understeer", "suspension_bottoming"],
        )
        assert "high_understeer" in prompt
        assert "suspension_bottoming" in prompt

    def test_includes_corner_issues(self, sample_session_summary):
        prompt = _build_user_prompt(sample_session_summary, ["high_understeer"])
        assert "Corner 3" in prompt
        assert "understeer" in prompt


# ===================================================================
# T032: Post-validation and conflict resolution tests (~4 tests)
# ===================================================================


class TestPostValidation:
    """Tests for parameter validation and clamping."""

    def test_value_above_max_clamped(self):
        ranges = {
            "WING_1": ParameterRange(
                section="WING_1", parameter="VALUE",
                min_value=0, max_value=20, step=1,
            ),
        }
        changes = [
            SetupChange(
                section="WING_1", parameter="VALUE",
                value_after=25.0, reasoning="Increase downforce",
                expected_effect="More grip", confidence="high",
            ),
        ]

        result = _post_validate_changes(changes, ranges)
        assert result[0].value_after == 20.0
        assert "clamped" in result[0].reasoning.lower()

    def test_value_below_min_clamped(self):
        ranges = {
            "PRESSURE_LF": ParameterRange(
                section="PRESSURE_LF", parameter="VALUE",
                min_value=20.0, max_value=35.0, step=0.5,
            ),
        }
        changes = [
            SetupChange(
                section="PRESSURE_LF", parameter="VALUE",
                value_after=15.0, reasoning="Lower pressure",
                expected_effect="More grip", confidence="medium",
            ),
        ]

        result = _post_validate_changes(changes, ranges)
        assert result[0].value_after == 20.0
        assert "clamped" in result[0].reasoning.lower()

    def test_unknown_parameter_has_warning(self):
        ranges = {}
        changes = [
            SetupChange(
                section="UNKNOWN_PARAM", parameter="VALUE",
                value_after=5.0, reasoning="test",
                expected_effect="test", confidence="low",
            ),
        ]

        result = _post_validate_changes(changes, ranges)
        assert result[0].value_after == 5.0  # Not clamped
        assert "warning" in result[0].reasoning.lower() or "no range" in result[0].reasoning.lower()

    def test_valid_value_unchanged(self):
        ranges = {
            "WING_1": ParameterRange(
                section="WING_1", parameter="VALUE",
                min_value=0, max_value=20, step=1,
            ),
        }
        changes = [
            SetupChange(
                section="WING_1", parameter="VALUE",
                value_after=10.0, reasoning="Moderate setting",
                expected_effect="Balanced", confidence="high",
            ),
        ]

        result = _post_validate_changes(changes, ranges)
        assert result[0].value_after == 10.0
        assert result[0].reasoning == "Moderate setting"


class TestConflictResolution:
    """Tests for conflict resolution when multiple specialists change same param."""

    def test_first_occurrence_wins(self):
        """Balance change wins over tyre change for same section."""
        changes = [
            SetupChange(
                section="PRESSURE_LF", parameter="VALUE",
                value_after=27.0, reasoning="Balance says",
                expected_effect="test", confidence="high",
            ),
            SetupChange(
                section="PRESSURE_LF", parameter="VALUE",
                value_after=25.0, reasoning="Tyre says",
                expected_effect="test", confidence="medium",
            ),
        ]

        result = _resolve_conflicts(changes)
        assert len(result) == 1
        assert result[0].value_after == 27.0  # First (balance priority) wins

    def test_different_sections_kept(self):
        """Different sections are all kept."""
        changes = [
            SetupChange(
                section="ARB_FRONT", parameter="VALUE",
                value_after=2.0, reasoning="test",
                expected_effect="test", confidence="high",
            ),
            SetupChange(
                section="PRESSURE_LF", parameter="VALUE",
                value_after=27.0, reasoning="test",
                expected_effect="test", confidence="medium",
            ),
        ]

        result = _resolve_conflicts(changes)
        assert len(result) == 2


# ===================================================================
# T034: US6 — Persistence tests (~3 tests)
# ===================================================================


class TestPersistence:
    """Tests for recommendation persistence via analyze_with_engineer."""

    @pytest.mark.asyncio
    async def test_recommendation_saved_on_success(
        self, sample_session_summary, tmp_path
    ):
        """Recommendation is saved to DB after successful analysis."""
        from ac_engineer.storage import init_db, save_session
        from ac_engineer.storage.models import SessionRecord

        db_path = tmp_path / "test.db"
        init_db(db_path)
        save_session(db_path, SessionRecord(
            session_id="test_session_001",
            car="test_car",
            track="test_track",
            session_date="2026-03-02",
            lap_count=5,
        ))

        summary = sample_session_summary.model_copy(
            update={"signals": ["high_understeer"], "active_setup_parameters": None}
        )
        config = ACConfig(ac_install_path=tmp_path)

        real_agent = _build_specialist_agent("balance", "test")
        with real_agent.override(model=_make_function_model("balance")):
            with patch("ac_engineer.engineer.agents._build_specialist_agent", return_value=real_agent):
                response = await analyze_with_engineer(summary, config, db_path)

        assert isinstance(response, EngineerResponse)
        # Verify recommendation was saved
        from ac_engineer.storage import get_recommendations
        recs = get_recommendations(db_path, "test_session_001")
        assert len(recs) >= 1

    @pytest.mark.asyncio
    async def test_response_returned_even_if_db_save_fails(
        self, sample_session_summary, tmp_path
    ):
        """Response returned even if DB save fails."""
        summary = sample_session_summary.model_copy(
            update={"signals": ["high_understeer"], "active_setup_parameters": None}
        )
        config = ACConfig(ac_install_path=tmp_path)
        db_path = tmp_path / "nonexistent_dir" / "test.db"

        real_agent = _build_specialist_agent("balance", "test")
        with real_agent.override(model=_make_function_model("balance")):
            with patch("ac_engineer.engineer.agents._build_specialist_agent", return_value=real_agent):
                response = await analyze_with_engineer(summary, config, db_path)

        # Should still return a valid response
        assert isinstance(response, EngineerResponse)
        assert response.session_id == summary.session_id

    @pytest.mark.asyncio
    async def test_feedback_only_response_saved(
        self, sample_session_summary, tmp_path
    ):
        """Response with only technique feedback (no setup changes) still saved."""
        from ac_engineer.storage import init_db, save_session
        from ac_engineer.storage.models import SessionRecord

        db_path = tmp_path / "test.db"
        init_db(db_path)
        save_session(db_path, SessionRecord(
            session_id="test_session_001",
            car="test_car",
            track="test_track",
            session_date="2026-03-02",
            lap_count=5,
        ))

        summary = sample_session_summary.model_copy(
            update={
                "signals": ["low_consistency"],
                "active_setup_parameters": None,
            }
        )
        config = ACConfig(ac_install_path=tmp_path)

        real_agent = _build_specialist_agent("technique", "test")
        with real_agent.override(model=_make_function_model("technique")):
            with patch("ac_engineer.engineer.agents._build_specialist_agent", return_value=real_agent):
                response = await analyze_with_engineer(summary, config, db_path)

        assert isinstance(response, EngineerResponse)
        from ac_engineer.storage import get_recommendations
        recs = get_recommendations(db_path, "test_session_001")
        assert len(recs) >= 1


# ===================================================================
# T036: US7 — Apply recommendation tests (~3 tests)
# ===================================================================


class TestApplyRecommendation:
    """Tests for applying recommendations to setup files."""

    @pytest.mark.asyncio
    async def test_successful_apply(self, tmp_path, sample_setup_ini, sample_car_data_dir):
        """Successful apply → backup + values written + status applied."""
        import textwrap

        from ac_engineer.engineer.agents import apply_recommendation
        from ac_engineer.storage import init_db, save_session
        from ac_engineer.storage.models import SessionRecord
        from ac_engineer.storage.models import SetupChange as StorageChange
        from ac_engineer.storage.recommendations import (
            save_recommendation,
        )

        db_path = tmp_path / "test.db"
        init_db(db_path)
        save_session(db_path, SessionRecord(
            session_id="test_session",
            car="test_car",
            track="test_track",
            session_date="2026-03-02",
            lap_count=5,
        ))

        rec = save_recommendation(
            db_path,
            "test_session",
            "Test recommendation",
            [StorageChange(
                section="PRESSURE_LF",
                parameter="VALUE",
                old_value="26.5",
                new_value="27.5",
                reasoning="Increase pressure",
            )],
        )

        outcomes = await apply_recommendation(
            recommendation_id=rec.recommendation_id,
            setup_path=sample_setup_ini,
            db_path=db_path,
            ac_install_path=sample_car_data_dir,
            car_name="test_car",
        )

        assert len(outcomes) >= 1
        # Verify backup exists
        import glob as glob_mod
        backups = glob_mod.glob(str(sample_setup_ini) + ".bak.*")
        assert len(backups) >= 1

        # Verify status updated
        from ac_engineer.storage.recommendations import get_recommendations
        recs = get_recommendations(db_path, "test_session")
        assert any(r.status == "applied" for r in recs)

    @pytest.mark.asyncio
    async def test_invalid_recommendation_id_raises(self, tmp_path):
        """apply with invalid recommendation_id → ValueError."""
        from ac_engineer.engineer.agents import apply_recommendation
        from ac_engineer.storage import init_db

        db_path = tmp_path / "test.db"
        init_db(db_path)

        with pytest.raises(ValueError, match="not found"):
            await apply_recommendation(
                recommendation_id="nonexistent_id",
                setup_path=tmp_path / "setup.ini",
                db_path=db_path,
            )

    @pytest.mark.asyncio
    async def test_missing_setup_file_raises(self, tmp_path, sample_car_data_dir):
        """apply with missing setup file → FileNotFoundError."""
        from ac_engineer.engineer.agents import apply_recommendation
        from ac_engineer.storage import init_db, save_session
        from ac_engineer.storage.models import SessionRecord
        from ac_engineer.storage.models import SetupChange as StorageChange
        from ac_engineer.storage.recommendations import save_recommendation

        db_path = tmp_path / "test.db"
        init_db(db_path)
        save_session(db_path, SessionRecord(
            session_id="test_session",
            car="test_car",
            track="test_track",
            session_date="2026-03-02",
            lap_count=5,
        ))

        rec = save_recommendation(
            db_path,
            "test_session",
            "Test",
            [StorageChange(
                section="PRESSURE_LF",
                parameter="VALUE",
                old_value="26.5",
                new_value="27.5",
                reasoning="test",
            )],
        )

        with pytest.raises(FileNotFoundError):
            await apply_recommendation(
                recommendation_id=rec.recommendation_id,
                setup_path=tmp_path / "nonexistent_setup.ini",
                db_path=db_path,
                ac_install_path=sample_car_data_dir,
                car_name="test_car",
            )
