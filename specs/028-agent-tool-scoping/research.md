# Research: Agent Tool Scoping

**Date**: 2026-03-10

## R1: Current Tool Registration Mechanism

**Question**: How does Pydantic AI register tools on agents, and how do we scope them per domain?

**Finding**: In `agents.py:203-220`, `_build_specialist_agent()` creates an `Agent` instance and then calls `agent.tool(fn)` for each of the 4 tool functions. The fix is to look up which tools to register from a domain-keyed dictionary instead of hardcoding all 4.

**Decision**: Add a `DOMAIN_TOOLS` constant (dict[str, list[Callable]]) at module level, right after the existing `AERO_SECTIONS` constant. The `_build_specialist_agent()` function will use `DOMAIN_TOOLS[domain]` to get the tool list.

**Alternatives considered**:
- Decorating tools with domain metadata → more complex, less readable, harder to audit
- Reading tool lists from the skill .md files at runtime → fragile, ties code to markdown parsing
- Per-domain agent subclasses → over-engineered for a simple mapping

## R2: Principal Agent Status

**Question**: Does the principal agent exist in code, or only as a skill prompt?

**Finding**: `principal.md` exists in `skills/` but there is no code that builds a principal agent. The only agent factory is `_build_specialist_agent()`, called for domains: balance, tyre, aero, technique. No code references `_build_specialist_agent("principal", ...)`.

**Decision**: Include "principal" in `DOMAIN_TOOLS` for forward-compatibility (it documents the intended tool set), but no code change is needed to scope a principal agent that doesn't yet exist. If/when a principal agent is built, it will use the same mapping.

## R3: Test Impact

**Question**: Which tests need updating?

**Finding**: `test_agents.py:404-410` (`test_agent_registers_4_tools`) explicitly asserts all 4 tools are registered for the "balance" domain. After scoping, balance gets only 3 tools (no `get_lap_detail`). This test must be updated to assert per-domain tool sets.

No other tests directly assert on tool registration. The integration tests in `test_integration.py` mock `_build_specialist_agent` entirely, so they are unaffected. The tool tests in `test_tools.py` test tool functions directly, not agent registration.

**Decision**: Replace the single `test_agent_registers_4_tools` test with per-domain assertions. Each domain test verifies the exact tool set from `DOMAIN_TOOLS`.

## R4: Existing `DOMAIN_TOOLS` Export

**Question**: Should `DOMAIN_TOOLS` be exported in `__init__.py`?

**Decision**: Yes, add it to the public exports in `engineer/__init__.py` so it can be imported for testing and auditing. This matches the spec requirement that the mapping be inspectable.
