"""Tests for agent orchestration: routing, model strings, combining, user prompts."""

from __future__ import annotations

import pytest

from ac_engineer.config import ACConfig
from ac_engineer.engineer.agents import (
    AERO_SECTIONS,
    DOMAIN_PRIORITY,
    SIGNAL_DOMAINS,
    _build_specialist_agent,
    _build_user_prompt,
    _combine_results,
    get_model_string,
    route_signals,
)
from ac_engineer.engineer.models import (
    DriverFeedback,
    EngineerResponse,
    SetupChange,
    SpecialistResult,
)


# ===================================================================
# T008: route_signals tests (~8 tests)
# ===================================================================


class TestRouteSignals:
    """Tests for signal-to-domain routing."""

    def test_single_balance_signal(self):
        result = route_signals(["high_understeer"])
        assert result == ["balance"]

    def test_single_tyre_signal(self):
        result = route_signals(["tyre_temp_spread_high"])
        assert result == ["tyre"]

    def test_single_technique_signal(self):
        result = route_signals(["low_consistency"])
        assert result == ["technique"]

    def test_multi_domain_brake_balance(self):
        """brake_balance_issue routes to both balance and technique."""
        result = route_signals(["brake_balance_issue"])
        assert "balance" in result
        assert "technique" in result

    def test_multiple_signals_deduplicate_domains(self):
        result = route_signals(["high_understeer", "high_oversteer"])
        assert result == ["balance"]

    def test_aero_detection_from_setup_parameters(self):
        """Aero added when setup has aero sections AND balance/tyre signals present."""
        setup = {"WING_1": {"VALUE": 5}, "PRESSURE_LF": {"VALUE": 26}}
        result = route_signals(["high_understeer"], setup)
        assert "aero" in result
        assert "balance" in result

    def test_aero_not_added_without_signals(self):
        """Aero NOT added when no balance/tyre signals even if setup has aero."""
        setup = {"WING_1": {"VALUE": 5}}
        result = route_signals([], setup)
        assert result == []

    def test_no_signals_returns_empty(self):
        result = route_signals([])
        assert result == []

    def test_unknown_signals_ignored(self):
        result = route_signals(["unknown_signal", "another_unknown"])
        assert result == []

    def test_priority_ordering(self):
        """Domains returned in priority order: balance < tyre < technique."""
        result = route_signals(["high_understeer", "tyre_temp_spread_high", "low_consistency"])
        assert result == ["balance", "tyre", "technique"]

    def test_aero_not_added_without_aero_sections(self):
        """Aero NOT added when car has no aero sections."""
        setup = {"PRESSURE_LF": {"VALUE": 26}, "ARB_FRONT": {"VALUE": 3}}
        result = route_signals(["high_understeer"], setup)
        assert "aero" not in result


# ===================================================================
# T009: get_model_string tests (~4 tests)
# ===================================================================


class TestGetModelString:
    """Tests for model string building."""

    def test_anthropic_default(self):
        config = ACConfig(llm_provider="anthropic")
        result = get_model_string(config)
        assert result == "anthropic:claude-sonnet-4-5"

    def test_openai(self):
        config = ACConfig(llm_provider="openai")
        result = get_model_string(config)
        assert result == "openai:gpt-4o"

    def test_gemini_google_prefix(self):
        config = ACConfig(llm_provider="gemini")
        result = get_model_string(config)
        assert result.startswith("google-gla:")
        assert "gemini" in result

    def test_custom_model_override(self):
        config = ACConfig(llm_provider="anthropic", llm_model="claude-opus-4-5")
        result = get_model_string(config)
        assert result == "anthropic:claude-opus-4-5"


# ===================================================================
# T020: _combine_results and _build_user_prompt tests (~4 tests)
# (Additional tests — main tests in test_integration.py)
# ===================================================================


class TestCombineResultsUnit:
    """Unit tests for _combine_results confidence calculation."""

    def test_all_high_confidence(self):
        from ac_engineer.engineer.models import SessionSummary

        results = {
            "balance": SpecialistResult(
                setup_changes=[
                    SetupChange(
                        section="ARB_FRONT", parameter="VALUE",
                        value_after=2.0, reasoning="test",
                        expected_effect="test", confidence="high",
                    ),
                    SetupChange(
                        section="ARB_REAR", parameter="VALUE",
                        value_after=3.0, reasoning="test",
                        expected_effect="test", confidence="high",
                    ),
                ],
                driver_feedback=[],
                domain_summary="test",
            ),
        }
        summary = SessionSummary(
            session_id="test", car_name="c", track_name="t",
            total_lap_count=5, flying_lap_count=3, signals=["high_understeer"],
        )
        response = _combine_results("test", results, summary)
        assert response.confidence == "high"

    def test_mixed_confidence_averages(self):
        from ac_engineer.engineer.models import SessionSummary

        results = {
            "balance": SpecialistResult(
                setup_changes=[
                    SetupChange(
                        section="ARB_FRONT", parameter="VALUE",
                        value_after=2.0, reasoning="test",
                        expected_effect="test", confidence="high",
                    ),
                    SetupChange(
                        section="ARB_REAR", parameter="VALUE",
                        value_after=3.0, reasoning="test",
                        expected_effect="test", confidence="low",
                    ),
                ],
                driver_feedback=[],
                domain_summary="test",
            ),
        }
        summary = SessionSummary(
            session_id="test", car_name="c", track_name="t",
            total_lap_count=5, flying_lap_count=3, signals=["high_understeer"],
        )
        response = _combine_results("test", results, summary)
        assert response.confidence == "medium"

    def test_no_changes_defaults_to_medium(self):
        from ac_engineer.engineer.models import SessionSummary

        results = {
            "technique": SpecialistResult(
                setup_changes=[],
                driver_feedback=[
                    DriverFeedback(
                        area="Consistency", observation="test",
                        suggestion="test", severity="medium",
                    ),
                ],
                domain_summary="test",
            ),
        }
        summary = SessionSummary(
            session_id="test", car_name="c", track_name="t",
            total_lap_count=5, flying_lap_count=3, signals=["low_consistency"],
        )
        response = _combine_results("test", results, summary)
        assert response.confidence == "medium"


# ===================================================================
# T023: Specialist-specific tests using TestModel (~4 tests)
# ===================================================================


class TestSpecialistAgents:
    """Tests for individual specialist agent creation and execution."""

    @staticmethod
    def _make_function_model(domain: str):
        """Create a FunctionModel that returns valid SpecialistResult JSON."""
        from pydantic_ai.messages import ModelResponse, TextPart
        from pydantic_ai.models.function import FunctionModel

        def handler(messages, info):
            if domain == "technique":
                text = '{"setup_changes": [], "driver_feedback": [{"area": "Consistency", "observation": "test obs", "suggestion": "test sug", "corners_affected": [1], "severity": "medium"}], "domain_summary": "Technique analysis complete"}'
            else:
                text = '{"setup_changes": [{"section": "ARB_FRONT", "parameter": "VALUE", "value_after": 2.0, "reasoning": "test reasoning", "expected_effect": "test effect", "confidence": "high"}], "driver_feedback": [], "domain_summary": "Analysis complete"}'
            return ModelResponse(parts=[TextPart(content=text)])

        return FunctionModel(handler)

    @pytest.mark.asyncio
    async def test_balance_agent_with_understeer_signals(self, sample_agent_deps):
        agent = _build_specialist_agent("balance", "test")
        with agent.override(model=self._make_function_model("balance")):
            result = await agent.run("Test balance analysis", deps=sample_agent_deps)
            assert isinstance(result.output, SpecialistResult)
            assert len(result.output.setup_changes) > 0

    @pytest.mark.asyncio
    async def test_tyre_agent_creation(self, sample_agent_deps):
        deps = sample_agent_deps.model_copy(update={"domain_signals": ["tyre_temp_spread_high"]})
        agent = _build_specialist_agent("tyre", "test")
        with agent.override(model=self._make_function_model("tyre")):
            result = await agent.run("Test tyre analysis", deps=deps)
            assert isinstance(result.output, SpecialistResult)

    @pytest.mark.asyncio
    async def test_aero_agent_creation(self, sample_agent_deps):
        agent = _build_specialist_agent("aero", "test")
        with agent.override(model=self._make_function_model("aero")):
            result = await agent.run("Test aero analysis", deps=sample_agent_deps)
            assert isinstance(result.output, SpecialistResult)

    @pytest.mark.asyncio
    async def test_technique_agent_creation(self, sample_agent_deps):
        deps = sample_agent_deps.model_copy(update={"domain_signals": ["low_consistency"]})
        agent = _build_specialist_agent("technique", "test")
        with agent.override(model=self._make_function_model("technique")):
            result = await agent.run("Test technique analysis", deps=deps)
            assert isinstance(result.output, SpecialistResult)
            assert len(result.output.driver_feedback) > 0


# ===================================================================
# T024: Routing integration tests (~3 tests)
# ===================================================================


class TestRoutingIntegration:
    """Tests for signal routing to correct specialists."""

    def test_only_tyre_signals_routes_to_tyre(self):
        result = route_signals(["tyre_temp_spread_high", "high_slip_angle"])
        assert result == ["tyre"]

    def test_balance_tyre_consistency_routes_three(self):
        result = route_signals(["high_understeer", "tyre_temp_spread_high", "low_consistency"])
        assert result == ["balance", "tyre", "technique"]

    def test_aero_car_with_balance_adds_aero(self):
        setup = {"WING_1": {"VALUE": 5}, "WING_2": {"VALUE": 7}, "PRESSURE_LF": {"VALUE": 26}}
        result = route_signals(["high_understeer"], setup)
        assert result == ["balance", "aero"]


# ===================================================================
# T026: US3 — plain-language explanation tests (~3 tests)
# ===================================================================


class TestExplanationQuality:
    """Tests verifying non-empty reasoning and expected_effect."""

    def test_all_changes_have_reasoning(self):
        response = EngineerResponse(
            session_id="test",
            setup_changes=[
                SetupChange(
                    section="ARB_FRONT", parameter="VALUE",
                    value_after=2.0, reasoning="Front ARB too stiff for slow corners",
                    expected_effect="Better turn-in through corners 3 and 7",
                    confidence="high",
                ),
            ],
            summary="Balance adjustment recommended",
            explanation="The car understeers in slow corners",
            confidence="high",
        )

        for change in response.setup_changes:
            assert change.reasoning, "reasoning must be non-empty"
            assert change.expected_effect, "expected_effect must be non-empty"

    def test_summary_is_non_empty(self):
        response = EngineerResponse(
            session_id="test",
            summary="Test summary",
            explanation="Test explanation",
            confidence="medium",
        )
        assert response.summary
        assert response.explanation

    def test_driver_feedback_has_all_fields(self):
        fb = DriverFeedback(
            area="Braking",
            observation="Brake points vary by 10m",
            suggestion="Use the 100m board consistently",
            corners_affected=[3, 7],
            severity="medium",
        )
        assert fb.observation
        assert fb.suggestion
        assert len(fb.corners_affected) > 0
