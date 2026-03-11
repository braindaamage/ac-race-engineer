"""Tests for agent orchestration: routing, model strings, combining, user prompts."""

from __future__ import annotations

import pytest

from ac_engineer.config import ACConfig
from ac_engineer.engineer.agents import (
    AERO_SECTIONS,
    DOMAIN_PARAMS,
    DOMAIN_PRIORITY,
    DOMAIN_TOOLS,
    SIGNAL_DOMAINS,
    _build_specialist_agent,
    _build_user_prompt,
    _combine_results,
    _select_knowledge_fragments,
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


# ===================================================================
# T016: Knowledge pre-loading tests
# ===================================================================


class TestSelectKnowledgeFragments:
    """Tests for _select_knowledge_fragments deterministic selection."""

    def test_returns_empty_for_unknown_signals(self):
        result = _select_knowledge_fragments(["unknown_xyz_signal"])
        assert result == []

    def test_returns_fragments_for_known_signals(self):
        result = _select_knowledge_fragments(["high_understeer"])
        assert len(result) > 0
        assert all(hasattr(f, "source_file") for f in result)

    def test_deterministic_output(self):
        """Same input always produces same output."""
        result1 = _select_knowledge_fragments(["high_understeer", "tyre_temp_spread_high"])
        result2 = _select_knowledge_fragments(["high_understeer", "tyre_temp_spread_high"])
        assert len(result1) == len(result2)
        for f1, f2 in zip(result1, result2):
            assert f1.source_file == f2.source_file
            assert f1.section_title == f2.section_title

    def test_caps_at_8_fragments(self):
        """Never returns more than 8 fragments."""
        all_signals = list(SIGNAL_DOMAINS.keys())
        result = _select_knowledge_fragments(all_signals)
        assert len(result) <= 8

    def test_empty_signal_list(self):
        result = _select_knowledge_fragments([])
        assert result == []


class TestBuildUserPromptKnowledge:
    """Tests for knowledge section in user prompt."""

    def test_includes_knowledge_section_with_fragments(self, sample_session_summary):
        fragments = _select_knowledge_fragments(["high_understeer"])
        prompt = _build_user_prompt(sample_session_summary, ["high_understeer"], fragments)
        assert "### Vehicle Dynamics Knowledge" in prompt
        assert "vehicle_balance_fundamentals.md" in prompt

    def test_includes_fallback_note_when_empty(self, sample_session_summary):
        prompt = _build_user_prompt(sample_session_summary, ["high_understeer"], [])
        assert "### Vehicle Dynamics Knowledge" in prompt
        assert "No pre-loaded knowledge" in prompt
        assert "search_kb" in prompt

    def test_no_fragments_param_shows_fallback(self, sample_session_summary):
        """Default (no fragments param) shows fallback note."""
        prompt = _build_user_prompt(sample_session_summary, ["high_understeer"])
        assert "No pre-loaded knowledge" in prompt


# ===================================================================
# T018: Agent turn limit tests
# ===================================================================


class TestAgentTurnLimit:
    """Tests for max_turns enforcement and error isolation."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("domain", ["balance", "tyre", "aero", "technique"])
    async def test_agent_registers_domain_scoped_tools(self, domain, sample_agent_deps):
        """Each specialist agent registers only the tools from DOMAIN_TOOLS."""
        agent = _build_specialist_agent(domain, "test")
        tool_names = set(agent._function_toolset.tools.keys())
        expected = {fn.__name__ for fn in DOMAIN_TOOLS[domain]}
        assert tool_names == expected, f"{domain}: expected {expected}, got {tool_names}"

    @pytest.mark.asyncio
    async def test_principal_domain_tools_defined(self):
        """DOMAIN_TOOLS['principal'] contains exactly get_lap_detail and get_corner_metrics."""
        expected = {"get_lap_detail", "get_corner_metrics"}
        actual = {fn.__name__ for fn in DOMAIN_TOOLS["principal"]}
        assert actual == expected

    @pytest.mark.asyncio
    async def test_analyze_handles_unexpected_model_behavior(self, sample_session_summary, tmp_path):
        """When an agent raises UnexpectedModelBehavior, others still run."""
        from unittest.mock import AsyncMock, patch

        from pydantic_ai.exceptions import UsageLimitExceeded

        from ac_engineer.config import ACConfig
        from ac_engineer.engineer.agents import analyze_with_engineer
        from ac_engineer.engineer.models import ParameterRange
        from ac_engineer.storage import init_db

        db_path = tmp_path / "test.db"
        init_db(db_path)
        config = ACConfig(llm_provider="anthropic", api_key="test-key")
        ranges = {
            "PRESSURE_LF": ParameterRange(section="PRESSURE_LF", parameter="VALUE", min_value=20.0, max_value=35.0, step=0.5),
        }

        call_count = 0

        async def mock_agent_run(prompt, *, deps, usage_limits=None, **kwargs):
            nonlocal call_count
            call_count += 1
            # First agent exceeds turn limit, second succeeds
            if call_count == 1:
                raise UsageLimitExceeded("Exceeded request_limit")
            # Return a mock result
            mock_result = AsyncMock()
            mock_result.output = SpecialistResult(
                setup_changes=[
                    SetupChange(
                        section="ARB_FRONT", parameter="VALUE",
                        value_after=2.0, reasoning="test",
                        expected_effect="test", confidence="high",
                    ),
                ],
                driver_feedback=[],
                domain_summary="OK",
            )
            mock_result.usage.return_value = AsyncMock(
                input_tokens=100, output_tokens=50, tool_calls=1, requests=1,
            )
            mock_result.all_messages.return_value = []
            return mock_result

        with patch("ac_engineer.engineer.agents._build_specialist_agent") as mock_build, \
             patch("ac_engineer.engineer.agents.build_model"):
            mock_agent = AsyncMock()
            mock_agent.run = mock_agent_run
            mock_build.return_value = mock_agent

            # Use signals that route to 2 domains
            summary = sample_session_summary.model_copy(
                update={"signals": ["high_understeer", "tyre_temp_spread_high"]}
            )

            response = await analyze_with_engineer(
                summary, config, db_path,
                parameter_ranges=ranges,
            )

        # One agent failed but we still got a response from the other
        assert response.summary != "Analysis could not be completed due to an error."

    @pytest.mark.asyncio
    async def test_all_agents_fail_returns_fallback(self, sample_session_summary, tmp_path):
        """When all agents hit turn limit, fallback response is returned."""
        from unittest.mock import AsyncMock, patch

        from pydantic_ai.exceptions import UsageLimitExceeded

        from ac_engineer.config import ACConfig
        from ac_engineer.engineer.agents import analyze_with_engineer
        from ac_engineer.engineer.models import ParameterRange
        from ac_engineer.storage import init_db

        db_path = tmp_path / "test.db"
        init_db(db_path)
        config = ACConfig(llm_provider="anthropic", api_key="test-key")
        ranges = {
            "PRESSURE_LF": ParameterRange(section="PRESSURE_LF", parameter="VALUE", min_value=20.0, max_value=35.0, step=0.5),
        }

        async def always_fail(prompt, *, deps, usage_limits=None, **kwargs):
            raise UsageLimitExceeded("Exceeded request_limit")

        with patch("ac_engineer.engineer.agents._build_specialist_agent") as mock_build, \
             patch("ac_engineer.engineer.agents.build_model"):
            mock_agent = AsyncMock()
            mock_agent.run = always_fail
            mock_build.return_value = mock_agent

            response = await analyze_with_engineer(
                sample_session_summary, config, db_path,
                parameter_ranges=ranges,
            )

        assert "error" in response.summary.lower() or "could not" in response.summary.lower()
        assert response.confidence == "low"


# ===================================================================
# Domain-scoped setup context tests (Phase 10)
# ===================================================================


class TestDomainScopedParams:
    """Tests for domain-scoped setup parameter filtering in _build_user_prompt."""

    @pytest.fixture
    def multi_domain_summary(self):
        """SessionSummary with sections spanning all domains."""
        from ac_engineer.engineer.models import SessionSummary

        return SessionSummary(
            session_id="test_domain",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=5,
            flying_lap_count=3,
            best_lap_time_s=89.5,
            signals=["high_understeer"],
            active_setup_parameters={
                "SPRING_RATE_LF": {"VALUE": 80000},
                "DAMP_BUMP_LF": {"VALUE": 5},
                "ARB_FRONT": {"VALUE": 3},
                "RIDE_HEIGHT_0": {"VALUE": 60},
                "BRAKE_BIAS": {"VALUE": 57.0},
                "PRESSURE_LF": {"VALUE": 26.5},
                "CAMBER_LF": {"VALUE": -2.0},
                "TOE_OUT_LF": {"VALUE": 0.10},
                "WING_1": {"VALUE": 5},
                "WING_2": {"VALUE": 7},
            },
        )

    # --- T004: User Story 1 tests ---

    def test_balance_domain_gets_only_balance_sections(self, multi_domain_summary):
        prompt = _build_user_prompt(multi_domain_summary, ["high_understeer"], domain="balance")
        assert "SPRING_RATE_LF" in prompt
        assert "DAMP_BUMP_LF" in prompt
        assert "ARB_FRONT" in prompt
        assert "RIDE_HEIGHT_0" in prompt
        assert "BRAKE_BIAS" in prompt
        assert "PRESSURE_LF" not in prompt
        assert "CAMBER_LF" not in prompt
        assert "TOE_OUT_LF" not in prompt
        assert "WING_1" not in prompt
        assert "WING_2" not in prompt

    def test_tyre_domain_gets_only_tyre_sections(self, multi_domain_summary):
        prompt = _build_user_prompt(multi_domain_summary, ["tyre_temp_spread_high"], domain="tyre")
        assert "PRESSURE_LF" in prompt
        assert "CAMBER_LF" in prompt
        assert "TOE_OUT_LF" in prompt
        assert "SPRING_RATE_LF" not in prompt
        assert "ARB_FRONT" not in prompt
        assert "WING_1" not in prompt

    def test_aero_domain_gets_only_aero_sections(self, multi_domain_summary):
        prompt = _build_user_prompt(multi_domain_summary, ["high_understeer"], domain="aero")
        assert "WING_1" in prompt
        assert "WING_2" in prompt
        assert "SPRING_RATE_LF" not in prompt
        assert "PRESSURE_LF" not in prompt
        assert "ARB_FRONT" not in prompt

    def test_technique_domain_gets_no_setup_params(self, multi_domain_summary):
        prompt = _build_user_prompt(multi_domain_summary, ["low_consistency"], domain="technique")
        assert "### Current Setup Parameters" not in prompt
        assert "No setup parameters available" in prompt

    def test_principal_domain_gets_no_setup_params(self, multi_domain_summary):
        prompt = _build_user_prompt(multi_domain_summary, ["high_understeer"], domain="principal")
        assert "### Current Setup Parameters" not in prompt
        assert "No setup parameters available" in prompt

    def test_domain_none_includes_all_params(self, multi_domain_summary):
        prompt = _build_user_prompt(multi_domain_summary, ["high_understeer"], domain=None)
        assert "SPRING_RATE_LF" in prompt
        assert "PRESSURE_LF" in prompt
        assert "WING_1" in prompt
        assert "CAMBER_LF" in prompt
        assert "ARB_FRONT" in prompt

    # --- T005: User Story 2 — tool fallback access ---

    def test_tool_fallback_access_unaffected(self, multi_domain_summary):
        """AgentDeps.parameter_ranges is never filtered — tools can access any parameter."""
        from ac_engineer.engineer.models import AgentDeps, ParameterRange

        ranges = {
            "SPRING_RATE_LF": ParameterRange(section="SPRING_RATE_LF", parameter="VALUE", min_value=50000, max_value=120000, step=5000),
            "PRESSURE_LF": ParameterRange(section="PRESSURE_LF", parameter="VALUE", min_value=20.0, max_value=35.0, step=0.5),
        }
        deps = AgentDeps(
            session_summary=multi_domain_summary,
            parameter_ranges=ranges,
            domain_signals=["tyre_temp_spread_high"],
            knowledge_fragments=[],
        )
        # Build prompt filtered to tyre — balance sections excluded from prompt
        prompt = _build_user_prompt(multi_domain_summary, ["tyre_temp_spread_high"], domain="tyre")
        assert "SPRING_RATE_LF" not in prompt
        # But deps still has balance ranges — tool can access them
        assert "SPRING_RATE_LF" in deps.parameter_ranges

    # --- T006: User Story 3 — mod cars ---

    def test_unrecognized_section_falls_back_to_balance(self, multi_domain_summary):
        summary = multi_domain_summary.model_copy(update={
            "active_setup_parameters": {
                **multi_domain_summary.active_setup_parameters,
                "CUSTOM_MOD_PARAM": {"VALUE": 42},
            },
        })
        prompt = _build_user_prompt(summary, ["high_understeer"], domain="balance")
        assert "CUSTOM_MOD_PARAM" in prompt

    def test_unrecognized_section_excluded_from_other_domains(self, multi_domain_summary):
        summary = multi_domain_summary.model_copy(update={
            "active_setup_parameters": {
                **multi_domain_summary.active_setup_parameters,
                "CUSTOM_MOD_PARAM": {"VALUE": 42},
            },
        })
        prompt = _build_user_prompt(summary, ["tyre_temp_spread_high"], domain="tyre")
        assert "CUSTOM_MOD_PARAM" not in prompt

    def test_empty_setup_params_preserves_existing_behavior(self):
        from ac_engineer.engineer.models import SessionSummary

        summary = SessionSummary(
            session_id="test_empty",
            car_name="c",
            track_name="t",
            total_lap_count=5,
            flying_lap_count=3,
            signals=["high_understeer"],
            active_setup_parameters={},
        )
        prompt = _build_user_prompt(summary, ["high_understeer"], domain="balance")
        assert "No setup parameters available" in prompt

    def test_summary_not_mutated_after_filtering(self, multi_domain_summary):
        original_params = dict(multi_domain_summary.active_setup_parameters)
        _build_user_prompt(multi_domain_summary, ["tyre_temp_spread_high"], domain="tyre")
        assert multi_domain_summary.active_setup_parameters == original_params


# ===================================================================
# Diagnostic trace capture tests
# ===================================================================


class TestAnalyzeWithEngineerTraceCapture:
    """Tests that analyze_with_engineer captures traces when diagnostic_mode=True."""

    @pytest.fixture()
    def basic_summary(self):
        from ac_engineer.engineer.models import SessionSummary

        return SessionSummary(
            session_id="trace_test_session",
            car_name="test_car",
            track_name="test_track",
            total_lap_count=5,
            flying_lap_count=3,
            best_lap_time_s=90.0,
            signals=["high_understeer"],
        )

    @pytest.fixture()
    def basic_config(self):
        return ACConfig(
            llm_provider="anthropic",
            llm_model="claude-sonnet-4-5",
            api_key="test-key",
            diagnostic_mode=True,
        )

    @pytest.mark.asyncio
    async def test_writes_trace_when_diagnostic_mode_true(
        self, basic_summary, basic_config, tmp_path,
    ):
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock, patch

        from ac_engineer.storage.db import init_db
        from ac_engineer.storage.models import SessionRecord
        from ac_engineer.storage.sessions import save_session

        db_path = tmp_path / "test.db"
        init_db(db_path)
        save_session(db_path, SessionRecord(
            session_id="trace_test_session", car="test_car", track="test_track",
            session_date="2026-03-11T12:00:00", lap_count=5, best_lap_time=90.0,
            state="analyzed",
        ))
        traces_dir = tmp_path / "traces"

        # Mock the agent.run() to return a simple result
        mock_result = MagicMock()
        mock_result.output = SpecialistResult(
            setup_changes=[],
            driver_feedback=[
                DriverFeedback(
                    area="Testing", observation="Test obs",
                    suggestion="Test sug", corners_affected=[1], severity="low",
                ),
            ],
            domain_summary="Test result",
        )
        mock_result.all_messages.return_value = []
        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_usage.cache_read_tokens = 0
        mock_usage.cache_write_tokens = 0
        mock_usage.requests = 1
        mock_usage.tool_calls = 0
        mock_result.usage.return_value = mock_usage

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent.tool = MagicMock()

        with patch("ac_engineer.engineer.agents._build_specialist_agent", return_value=mock_agent), \
             patch("ac_engineer.engineer.agents.build_model", return_value="test-model"):
            from ac_engineer.engineer.agents import analyze_with_engineer

            response = await analyze_with_engineer(
                basic_summary,
                basic_config,
                db_path,
                diagnostic_mode=True,
                traces_dir=traces_dir,
            )

        # The trace file should have been written
        trace_files = list(traces_dir.glob("rec_*.md"))
        assert len(trace_files) == 1
        content = trace_files[0].read_text(encoding="utf-8")
        assert "Diagnostic Trace" in content

    @pytest.mark.asyncio
    async def test_skips_trace_when_diagnostic_mode_false(
        self, basic_summary, basic_config, tmp_path,
    ):
        from unittest.mock import AsyncMock, MagicMock, patch

        from ac_engineer.storage.db import init_db

        db_path = tmp_path / "test.db"
        init_db(db_path)
        traces_dir = tmp_path / "traces"

        mock_result = MagicMock()
        mock_result.output = SpecialistResult(
            setup_changes=[],
            driver_feedback=[
                DriverFeedback(
                    area="Testing", observation="Test obs",
                    suggestion="Test sug", corners_affected=[1], severity="low",
                ),
            ],
            domain_summary="Test result",
        )
        mock_result.all_messages.return_value = []
        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_usage.cache_read_tokens = 0
        mock_usage.cache_write_tokens = 0
        mock_usage.requests = 1
        mock_usage.tool_calls = 0
        mock_result.usage.return_value = mock_usage

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent.tool = MagicMock()

        with patch("ac_engineer.engineer.agents._build_specialist_agent", return_value=mock_agent), \
             patch("ac_engineer.engineer.agents.build_model", return_value="test-model"):
            from ac_engineer.engineer.agents import analyze_with_engineer

            response = await analyze_with_engineer(
                basic_summary,
                basic_config,
                db_path,
                diagnostic_mode=False,
                traces_dir=traces_dir,
            )

        # No trace files should exist
        assert not traces_dir.exists() or len(list(traces_dir.glob("rec_*.md"))) == 0
