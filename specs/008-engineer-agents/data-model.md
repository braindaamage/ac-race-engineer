# Data Model: Engineer Agents

**Feature**: 008-engineer-agents
**Date**: 2026-03-04

## Existing Models (Phase 5.2 — no changes)

### SessionSummary (input to agents)
- `session_id: str`
- `car_name: str`, `track_name: str`, `track_config: str | None`
- `recorded_at: str | None`
- `total_lap_count: int`, `flying_lap_count: int`
- `best_lap_time_s: float | None`, `worst_lap_time_s: float | None`, `lap_time_stddev_s: float | None`
- `avg_understeer_ratio: float | None`
- `active_setup_filename: str | None`
- `active_setup_parameters: dict[str, dict[str, float | str]] | None`
- `laps: list[LapSummary]`
- `signals: list[str]`
- `corner_issues: list[CornerIssue]`
- `stints: list[StintSummary]`
- `tyre_temp_averages: dict[str, float] | None`
- `tyre_pressure_averages: dict[str, float] | None`
- `slip_angle_averages: dict[str, float] | None`

### SetupChange (output from specialists)
- `section: str`, `parameter: str`
- `value_before: float | None`, `value_after: float`
- `reasoning: str`, `expected_effect: str`
- `confidence: Literal["high", "medium", "low"]`

### DriverFeedback (output from technique specialist)
- `area: str`, `observation: str`, `suggestion: str`
- `corners_affected: list[int]`
- `severity: Literal["high", "medium", "low"]`

### EngineerResponse (final combined output)
- `session_id: str`
- `setup_changes: list[SetupChange]`
- `driver_feedback: list[DriverFeedback]`
- `signals_addressed: list[str]`
- `summary: str`, `explanation: str`
- `confidence: Literal["high", "medium", "low"]`

### ParameterRange (validation context)
- `section: str`, `parameter: str`
- `min_value: float`, `max_value: float`, `step: float`
- `default_value: float | None`

### ValidationResult (validation output)
- `section: str`, `parameter: str`
- `proposed_value: float`, `clamped_value: float | None`
- `is_valid: bool`, `warning: str | None`

## New Models (Phase 5.3)

### SpecialistResult (agent output_type)
Intermediate output from each specialist agent before combination into EngineerResponse.

- `setup_changes: list[SetupChange]` — changes proposed by this specialist (empty for technique)
- `driver_feedback: list[DriverFeedback]` — driving observations (empty for setup specialists)
- `domain_summary: str` — specialist's assessment of its domain findings

**Relationships**: One SpecialistResult per invoked specialist. Multiple SpecialistResults combine into one EngineerResponse.

**Validation**: `setup_changes` and `driver_feedback` cannot both be empty (specialist must produce at least one type of output). `domain_summary` must be non-empty.

### AgentDeps (Pydantic AI dependency container)
Shared context passed to all specialist agents via `RunContext[AgentDeps]`.

- `session_summary: SessionSummary` — the session being analyzed
- `parameter_ranges: dict[str, ParameterRange]` — valid ranges for the car
- `domain_signals: list[str]` — subset of signals relevant to this specialist
- `knowledge_fragments: list[KnowledgeFragment]` — pre-loaded knowledge for the domain signals

**Relationships**: Created once per specialist invocation. Contains references to existing models.

### SignalDomainMapping (routing configuration)
Static mapping from signal names to specialist domains.

- `SIGNAL_DOMAINS: dict[str, list[str]]` — signal → list of domain names
- `DOMAIN_PRIORITY: dict[str, int]` — domain → priority (lower = higher priority)
- `AERO_SECTIONS: set[str]` — setup section prefixes that indicate aero presence

**Not a Pydantic model** — module-level constants.

## State Transitions

### Recommendation Lifecycle
```
[not exists] → save_recommendation() → "pending"
"pending" → apply_recommendation() success → "applied"
"pending" → user rejects → "rejected"
"pending" → apply_recommendation() failure → "pending" (unchanged)
```

## Data Flow

```
SessionSummary
    ↓
route_signals() → set of domains to invoke
    ↓
For each domain:
    AgentDeps (summary + ranges + domain signals + knowledge)
        ↓
    Specialist Agent (Pydantic AI) → SpecialistResult
        ↓
Combine SpecialistResults
    ↓
validate_changes() on all proposed SetupChanges
    ↓
Resolve conflicts (domain priority)
    ↓
Build EngineerResponse
    ↓
save_recommendation() to SQLite
    ↓
Return EngineerResponse
```
