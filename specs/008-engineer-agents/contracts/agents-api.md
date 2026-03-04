# Contract: Engineer Agents Public API

**Module**: `ac_engineer.engineer`
**Feature**: 008-engineer-agents

## Public Functions

### analyze_with_engineer()

Primary entry point for AI-powered session analysis.

```python
async def analyze_with_engineer(
    summary: SessionSummary,
    config: ACConfig,
    db_path: Path,
    ac_install_path: Path | None = None,
) -> EngineerResponse:
```

**Parameters**:
- `summary` — Pre-computed session summary (from `summarize_session()`)
- `config` — User configuration (LLM provider, model, paths)
- `db_path` — Path to SQLite database for persisting the recommendation
- `ac_install_path` — AC installation path for reading parameter ranges. If None, uses `config.ac_install_path`

**Returns**: `EngineerResponse` with setup changes, driver feedback, summary, and confidence.

**Behavior**:
1. Read parameter ranges for the car (`read_parameter_ranges()`)
2. Route signals to specialist domains (`route_signals()`)
3. Pre-load knowledge fragments for each domain
4. Run relevant specialist agents (Pydantic AI)
5. Combine specialist results
6. Validate all proposed setup changes against parameter ranges
7. Resolve conflicts (domain priority: balance > tyre > aero)
8. Build final EngineerResponse
9. Persist recommendation to database
10. Return EngineerResponse

**Error handling**:
- LLM errors → returns EngineerResponse with `confidence="low"`, empty changes, error in explanation
- No flying laps → returns EngineerResponse with summary noting insufficient data
- No signals → returns EngineerResponse with positive summary, no changes

**Guarantees**:
- All `value_after` in setup changes are within valid parameter ranges (clamped)
- `signals_addressed` lists exactly the signals that were analyzed
- Recommendation is persisted to DB before returning (on success)

---

### apply_recommendation()

Apply a previously generated recommendation to a setup file.

```python
async def apply_recommendation(
    recommendation_id: str,
    setup_path: Path,
    db_path: Path,
    ac_install_path: Path | None = None,
    car_name: str | None = None,
) -> list[ChangeOutcome]:
```

**Parameters**:
- `recommendation_id` — UUID of the recommendation to apply
- `setup_path` — Path to the .ini setup file to modify
- `db_path` — Path to SQLite database
- `ac_install_path` — AC installation path for reading parameter ranges
- `car_name` — Car name for parameter range lookup

**Returns**: List of `ChangeOutcome` (old_value → new_value for each applied change).

**Behavior**:
1. Load recommendation from database
2. Read parameter ranges for the car
3. Validate changes against current ranges (re-validate in case ranges changed)
4. Create backup of setup file
5. Apply changes atomically
6. Update recommendation status to "applied" in database
7. Return list of outcomes

**Error handling**:
- Recommendation not found → raises `ValueError`
- Setup file not found → raises `FileNotFoundError`
- Write failure → original file intact, recommendation status unchanged, raises `OSError`

**Guarantees**:
- Backup always created before modification
- Atomic write: either all changes apply or none
- Database status only updated on successful write

---

### route_signals()

Deterministic signal-to-domain routing (not async, no LLM).

```python
def route_signals(
    signals: list[str],
    setup_parameters: dict[str, dict[str, float | str]] | None = None,
) -> list[str]:
```

**Parameters**:
- `signals` — Detected signal names from SessionSummary
- `setup_parameters` — Current setup sections/values (to detect aero presence)

**Returns**: Sorted list of unique domain names to invoke (e.g., `["balance", "tyre"]`).

**Behavior**:
- Maps each signal to its domain(s) via `SIGNAL_DOMAINS`
- Adds "aero" domain if setup contains aero-related sections AND any balance/tyre signals present
- Returns domains sorted by priority (balance first, technique last)

---

### get_model_string()

Build Pydantic AI model identifier from config.

```python
def get_model_string(config: ACConfig) -> str:
```

**Returns**: Model string like `"anthropic:claude-sonnet-4-5"` or `"openai:gpt-4o"`.

## Exported from `ac_engineer.engineer`

After Phase 5.3, the module's `__init__.py` exports:

```python
# Phase 5.2 (existing)
from ac_engineer.engineer.summarizer import summarize_session
from ac_engineer.engineer.setup_reader import read_parameter_ranges, get_parameter_range
from ac_engineer.engineer.setup_writer import validate_changes, apply_changes, create_backup
from ac_engineer.engineer.models import (
    SessionSummary, LapSummary, CornerIssue, StintSummary,
    ParameterRange, ValidationResult, ChangeOutcome,
    SetupChange, DriverFeedback, EngineerResponse,
)

# Phase 5.3 (new)
from ac_engineer.engineer.agents import (
    analyze_with_engineer,
    apply_recommendation,
    route_signals,
    get_model_string,
    SpecialistResult,
    AgentDeps,
    SIGNAL_DOMAINS,
    DOMAIN_PRIORITY,
)
```
