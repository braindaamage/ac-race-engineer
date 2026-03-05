# Research: Engineer Agents (Phase 5.3)

**Feature**: 008-engineer-agents
**Date**: 2026-03-04

## R1: Pydantic AI Agent Architecture

**Decision**: Use Pydantic AI `Agent` class with `output_type` for structured responses, `deps_type` for shared context, and `@agent.tool`/`@agent.tool_plain` decorators for tool registration.

**Rationale**: Pydantic AI provides type-safe agent definitions with built-in structured output, dependency injection via `RunContext`, and provider-agnostic model selection via string identifiers (`"anthropic:claude-sonnet-4-5"`, `"openai:gpt-4o"`, `"google:gemini-1.5-pro"`). This matches the project's constitution (Principle XI) requiring all LLM calls through Pydantic AI.

**Alternatives considered**:
- LangChain: Heavier, more complex, not aligned with project's Pydantic-first approach
- Direct SDK calls: Violates constitution Principle XI
- Custom agent framework: Unnecessary given Pydantic AI covers the needs

**Key patterns**:
```python
# Agent creation with model string
agent = Agent(
    "anthropic:claude-sonnet-4-5",
    deps_type=AgentDeps,
    output_type=SpecialistResult,
    system_prompt=prompt_text,
)

# Tool with context access
@agent.tool
async def search_knowledge(ctx: RunContext[AgentDeps], query: str) -> str:
    fragments = knowledge_search(query)
    return "\n".join(f.content for f in fragments)

# Running
result = await agent.run(user_prompt, deps=deps)
output = result.output  # typed as SpecialistResult
```

## R2: Multi-Agent Orchestration Pattern

**Decision**: Use programmatic orchestration (not agent delegation). The principal is plain Python that routes signals to specialist agents and combines outputs. Specialists are independent Pydantic AI agents.

**Rationale**: Agent delegation (one agent calling another via tool) adds unnecessary nesting and makes testing harder. Since signal routing is deterministic (based on signal-to-domain mapping), plain Python orchestration is simpler, more testable, and more predictable. Each specialist runs independently with its own prompt and tools.

**Alternatives considered**:
- Agent delegation via tools: More complex, harder to test, unnecessary since routing is deterministic
- Pydantic Graphs: Overkill for 4 specialist agents with simple routing
- Single monolithic agent: Loses domain specialization, prompts become too long

**Pattern**:
```python
async def analyze_with_engineer(summary, config, db_path, ranges):
    # 1. Deterministic routing (Python, not LLM)
    domains = route_signals(summary.signals, summary.active_setup_parameters)

    # 2. Run relevant specialists (async)
    specialist_results = []
    for domain in domains:
        agent = get_specialist_agent(domain, config)
        result = await agent.run(build_prompt(summary, domain), deps=deps)
        specialist_results.append(result.output)

    # 3. Combine, validate, persist (Python)
    return build_engineer_response(summary, specialist_results, ranges)
```

## R3: Signal-to-Domain Routing

**Decision**: Static mapping dict with deterministic routing. `brake_balance_issue` routes to both balance AND technique domains. Aero domain triggers when setup contains aero parameters (WING_*, RIDE_HEIGHT_*) regardless of specific signals.

**Rationale**: The 10 signals from Phase 4 map cleanly to domains. `brake_balance_issue` is the one signal that spans domains: balance specialist addresses brake bias settings, technique specialist addresses braking technique. Aero is setup-presence-based because there's no dedicated aero signal — aero problems manifest as balance/grip signals on cars with aero.

**Mapping**:
```python
SIGNAL_DOMAINS = {
    "high_understeer": ["balance"],
    "high_oversteer": ["balance"],
    "brake_balance_issue": ["balance", "technique"],
    "suspension_bottoming": ["balance"],
    "tyre_temp_spread_high": ["tyre"],
    "tyre_temp_imbalance": ["tyre"],
    "tyre_wear_rapid": ["tyre"],
    "high_slip_angle": ["tyre"],
    "low_consistency": ["technique"],
    "lap_time_degradation": ["tyre"],
}

AERO_SECTIONS = {"WING_1", "WING_2", "RIDE_HEIGHT_0", "RIDE_HEIGHT_1", ...}
```

## R4: Testing Strategy with Pydantic AI

**Decision**: Use `TestModel` for basic tests, `FunctionModel` for tests requiring specific tool call sequences or custom responses. Set `ALLOW_MODEL_REQUESTS = False` globally to prevent accidental real API calls.

**Rationale**: Pydantic AI's built-in test models provide deterministic, cost-free testing. `TestModel` auto-calls all tools and returns valid structured data. `FunctionModel` allows custom response logic for testing specific scenarios (e.g., agent proposes out-of-range values).

**Alternatives considered**:
- Mocking at HTTP level: Too low-level, breaks on Pydantic AI internal changes
- Real model calls with VCR/cassettes: Expensive, flaky, slow
- Custom mock framework: Unnecessary given Pydantic AI's built-in test support

**Pattern**:
```python
from pydantic_ai.models.test import TestModel
from pydantic_ai import models

models.ALLOW_MODEL_REQUESTS = False  # in conftest.py

def test_balance_agent():
    with balance_agent.override(model=TestModel()):
        result = await balance_agent.run(prompt, deps=deps)
        assert len(result.output.setup_changes) > 0
```

## R5: Model Provider Selection

**Decision**: Build model string dynamically from ACConfig using `f"{config.llm_provider}:{get_effective_model(config)}"` format. Pass as string to Agent constructor or use `agent.override(model=model_string)`.

**Rationale**: Pydantic AI accepts model strings like `"anthropic:claude-sonnet-4-5"` and auto-selects the right provider class. This aligns with existing `get_effective_model()` and `LLM_MODEL_DEFAULTS` from config module.

**Mapping**:
```python
def get_model_string(config: ACConfig) -> str:
    provider = config.llm_provider       # "anthropic", "openai", "gemini"
    model = get_effective_model(config)   # e.g., "claude-sonnet-4-5"
    # Pydantic AI uses "google" prefix for Gemini
    prefix = "google" if provider == "gemini" else provider
    return f"{prefix}:{model}"
```

## R6: System Prompts as Markdown Files

**Decision**: Store each specialist's system prompt as a markdown file in `skills/` directory. Load at module import time using `Path.read_text()`. Prompts include role definition, domain knowledge summary, tool usage instructions, and output format guidance.

**Rationale**: Markdown files are easy to iterate on without code changes. They can be reviewed independently and updated without touching Python code. The `skills/` directory name is descriptive and avoids confusion with "prompts" (which could mean user prompts).

**Alternatives considered**:
- Inline Python strings: Hard to read and maintain for long prompts
- YAML/JSON config: Adds parsing complexity for no benefit
- Database-stored prompts: Overkill for 5 static prompts

## R7: Specialist Output Model

**Decision**: Create a `SpecialistResult` Pydantic model as the `output_type` for specialist agents. This separates the agent's raw output from the final `EngineerResponse` (which is assembled by the orchestrator after validation).

**Rationale**: Specialists should not produce a full `EngineerResponse` — they don't know about other specialists' outputs or conflict resolution. A lighter intermediate model lets each specialist focus on its domain.

```python
class SpecialistResult(BaseModel):
    setup_changes: list[SetupChange] = []
    driver_feedback: list[DriverFeedback] = []
    domain_summary: str  # specialist's assessment of its domain
```

## R8: Conflict Resolution

**Decision**: When multiple specialists propose changes to the same setup section/parameter, keep the change from the first specialist in priority order: balance > tyre > aero > technique. Log the conflict in the explanation.

**Rationale**: Balance issues (understeer/oversteer) are the most impactful for safety and lap time. Tyre issues come next. Aero is supplementary. Technique doesn't produce setup changes (only feedback), so it never conflicts.

**Domain priority**: balance(1) > tyre(2) > aero(3) > technique(4)

## R9: apply_recommendation() Pipeline

**Decision**: Single function that orchestrates: load recommendation from DB → validate changes against current ranges → create_backup → apply_changes → update_recommendation_status("applied"). Returns list of ChangeOutcome.

**Rationale**: Reuses all existing Phase 5.2 functions. The orchestration is thin — it just sequences the calls and handles errors (rolling back status on failure).

## R10: Dependency Installation

**Decision**: Add `pydantic-ai>=0.1.0` to `backend/pyproject.toml` dependencies. Install into conda env via `pip install -e .` or `pip install pydantic-ai`.

**Rationale**: pydantic-ai is the only new external dependency. It brings its own provider SDKs (anthropic, openai, google-genai) as optional extras. The project should install with provider extras as needed: `pydantic-ai[anthropic]` for default setup.
