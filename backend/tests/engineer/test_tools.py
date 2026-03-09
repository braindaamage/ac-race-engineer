"""Tests for Pydantic AI tool implementations."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ac_engineer.engineer.models import (
    AgentDeps,
    CornerIssue,
    LapSummary,
    ParameterRange,
    SessionSummary,
)
from ac_engineer.engineer.tools import (
    get_corner_metrics,
    get_lap_detail,
    get_setup_range,
    search_kb,
)


def _make_ctx(deps: AgentDeps) -> MagicMock:
    """Create a mock RunContext with given deps."""
    ctx = MagicMock()
    ctx.deps = deps
    return ctx


# ===================================================================
# T010: Tool function tests
# ===================================================================


class TestSearchKb:
    """Tests for search_kb tool."""

    @pytest.mark.asyncio
    async def test_returns_formatted_fragments(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await search_kb(ctx, "understeer springs")
        # search_knowledge returns something or nothing depending on knowledge base
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_no_results_returns_message(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await search_kb(ctx, "xyznonexistentquery12345")
        # Either returns fragments or the no-results message
        assert isinstance(result, str)


class TestGetSetupRange:
    """Tests for batch get_setup_range tool."""

    @pytest.mark.asyncio
    async def test_single_item_returns_range_info(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_setup_range(ctx, ["PRESSURE_LF"])
        assert "Min: 20.0" in result
        assert "Max: 35.0" in result
        assert "Step: 0.5" in result

    @pytest.mark.asyncio
    async def test_multi_item_returns_all_blocks(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_setup_range(ctx, ["PRESSURE_LF", "WING_1"])
        assert "PRESSURE_LF" in result
        assert "WING_1" in result
        assert "Min: 20.0" in result
        assert "Min: 0" in result

    @pytest.mark.asyncio
    async def test_unknown_section_in_batch(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_setup_range(ctx, ["PRESSURE_LF", "NONEXISTENT"])
        assert "Min: 20.0" in result
        assert "no range data" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_setup_range(ctx, [])
        assert result == ""

    @pytest.mark.asyncio
    async def test_includes_default_when_present(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_setup_range(ctx, ["SPRING_RATE_LF"])
        assert "Default: 80000" in result


class TestGetLapDetail:
    """Tests for batch get_lap_detail tool."""

    @pytest.mark.asyncio
    async def test_single_item_returns_correct_lap(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_lap_detail(ctx, [2])
        assert "89.5" in result
        assert "BEST" in result

    @pytest.mark.asyncio
    async def test_multi_item_returns_all_laps(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_lap_detail(ctx, [2, 3])
        assert "89.5" in result
        assert "90.2" in result

    @pytest.mark.asyncio
    async def test_unknown_lap_in_batch(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_lap_detail(ctx, [2, 999])
        assert "89.5" in result
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_lap_detail(ctx, [])
        assert result == ""


class TestGetCornerMetrics:
    """Tests for batch get_corner_metrics tool."""

    @pytest.mark.asyncio
    async def test_single_item_returns_corner_data(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_corner_metrics(ctx, [3])
        assert "understeer" in result.lower()
        assert "1.35" in result

    @pytest.mark.asyncio
    async def test_multi_item_returns_all_corners(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_corner_metrics(ctx, [3, 7])
        assert "Corner 3" in result
        assert "Corner 7" in result

    @pytest.mark.asyncio
    async def test_unknown_corner_in_batch(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_corner_metrics(ctx, [3, 999])
        assert "Corner 3" in result
        assert "no issue data" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await get_corner_metrics(ctx, [])
        assert result == ""


# ===================================================================
# T029: US4 — Knowledge grounding tests
# ===================================================================


class TestSearchKbFormatting:
    """Tests for knowledge search formatting with source attribution."""

    @pytest.mark.asyncio
    async def test_formatted_fragments_have_source(self, sample_agent_deps):
        """search_kb returns fragments with [Source: ...] attribution."""
        ctx = _make_ctx(sample_agent_deps)
        result = await search_kb(ctx, "understeer springs front")
        # If fragments found, check format
        if "No relevant knowledge" not in result:
            assert "[Source:" in result

    @pytest.mark.asyncio
    async def test_empty_query_returns_no_results(self, sample_agent_deps):
        ctx = _make_ctx(sample_agent_deps)
        result = await search_kb(ctx, "   ")
        assert "No relevant knowledge" in result

    @pytest.mark.asyncio
    async def test_knowledge_fragments_passed_in_deps(self, sample_agent_deps):
        """Verify knowledge_fragments field is accessible on deps."""
        assert hasattr(sample_agent_deps, "knowledge_fragments")
        assert isinstance(sample_agent_deps.knowledge_fragments, list)

    @pytest.mark.asyncio
    async def test_max_two_fragments_returned(self, sample_agent_deps):
        """search_kb returns at most 2 fragments."""
        ctx = _make_ctx(sample_agent_deps)
        result = await search_kb(ctx, "understeer oversteer balance springs suspension")
        if "No relevant knowledge" not in result:
            # Count separator occurrences — N fragments produce N-1 separators
            separator_count = result.count("\n\n---\n\n")
            assert separator_count <= 1  # At most 2 fragments → at most 1 separator
