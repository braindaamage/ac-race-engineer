"""Tests for keyword search."""

from __future__ import annotations

from ac_engineer.knowledge import search_knowledge


class TestKeywordSearch:
    def test_search_anti_roll_bar_oversteer(self):
        results = search_knowledge("rear anti-roll bar oversteer")
        assert len(results) > 0
        sources = {f.source_file for f in results}
        assert "suspension_and_springs.md" in sources or "vehicle_balance_fundamentals.md" in sources

    def test_search_camber_tyre_temperature(self):
        results = search_knowledge("camber tyre temperature")
        assert len(results) > 0
        sources = {f.source_file for f in results}
        assert "alignment.md" in sources

    def test_search_brake_bias(self):
        results = search_knowledge("brake bias")
        assert len(results) > 0
        assert results[0].source_file == "braking.md" or any(
            f.source_file == "braking.md" for f in results[:3]
        )

    def test_search_nonsense_returns_empty(self):
        results = search_knowledge("xyzzy foobar")
        assert results == []

    def test_search_empty_query_returns_empty(self):
        results = search_knowledge("")
        assert results == []

    def test_search_whitespace_only_returns_empty(self):
        results = search_knowledge("   ")
        assert results == []

    def test_search_results_ranked_by_relevance(self):
        results = search_knowledge("brake bias trail braking weight transfer")
        assert len(results) >= 2
        # First result should have a braking-related source
        top_sources = {results[0].source_file, results[1].source_file}
        assert "braking.md" in top_sources or "vehicle_balance_fundamentals.md" in top_sources

    def test_search_case_insensitive(self):
        upper = search_knowledge("BRAKE BIAS")
        lower = search_knowledge("brake bias")
        upper_pairs = {(f.source_file, f.section_title) for f in upper}
        lower_pairs = {(f.source_file, f.section_title) for f in lower}
        assert upper_pairs == lower_pairs
