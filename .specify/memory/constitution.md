<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (Initial ratification)

Modified principles: N/A (initial creation)

Added sections:
- 7 Core Principles (I-VII)
- Technical Boundaries section
- Development Workflow section
- Governance section

Removed sections: N/A

Templates requiring updates:
- .specify/templates/plan-template.md: ✅ No updates needed (Constitution Check placeholder works)
- .specify/templates/spec-template.md: ✅ No updates needed (generic structure compatible)
- .specify/templates/tasks-template.md: ✅ No updates needed (phase structure compatible)
- .specify/templates/commands/*.md: N/A (no command files exist yet)

Follow-up TODOs: None
==================
-->

# AC Race Engineer AI Constitution

## Core Principles

### I. Data Integrity First

The system MUST NOT make setup recommendations based on incomplete or inconsistent
telemetry data. All telemetry data MUST be validated before analysis.

- Telemetry sessions MUST have complete lap data before being processed
- Data gaps exceeding acceptable thresholds MUST trigger warnings, not guesses
- Modded cars with broken physics or inconsistent data MUST be detected and flagged
- The system MUST clearly communicate when data quality is insufficient for analysis
- No "best effort" recommendations on bad data—refuse and explain why

**Rationale**: Incorrect setup advice based on bad telemetry is worse than no advice.
Drivers will lose trust if recommendations don't match their on-track experience.

### II. Car-Agnostic Design

All systems MUST work with any car, including mods, without hardcoded car-specific
logic.

- Parser and analyzer code MUST NOT contain car name checks or model-specific branches
- Setup parameter discovery MUST be dynamic, reading what exists in the .ini file
- Telemetry channel mapping MUST handle variations across different car mods
- New cars MUST work without code changes—only potential knowledge base updates
- Test coverage MUST include at least one vanilla car and one popular mod

**Rationale**: Assetto Corsa's mod ecosystem is vast. Hardcoding car logic creates
an unmaintainable system that fails on new content.

### III. Setup File Autonomy

The system reads and writes Assetto Corsa .ini setup files directly, validating
parameter ranges before writing.

- Setup parser MUST handle arbitrary parameter names (mods add custom parameters)
- All parameter writes MUST validate against min/max ranges from the car's data files
- Write operations MUST preserve parameters the system doesn't understand
- Original setup MUST be backed up before any modification
- Parameter changes MUST be atomic—partial writes are unacceptable

**Rationale**: Direct file manipulation gives full control but requires safety.
Corrupted setups waste driver time and erode trust.

### IV. LLM as Interpreter, Not Calculator

All numerical analysis MUST be performed by deterministic Python code. The LLM
receives only pre-processed metrics to reason about.

- The LLM MUST NOT perform calculations (averages, deltas, physics formulas)
- Metrics passed to the LLM MUST be fully computed with clear labels and units
- Setup change suggestions MUST come via structured function calling, not free text
- The LLM's role is interpretation: "tire temps show understeer" not "avg 92.3°C"
- Deterministic code MUST be testable independent of LLM behavior

**Rationale**: LLMs are unreliable calculators. Reproducible numerical analysis
requires deterministic code. LLMs excel at pattern recognition and explanation.

### V. Educational Explanations

Every setup change MUST include a clear explanation of why it helps, accessible
to someone with little setup knowledge.

- Explanations MUST avoid jargon or define technical terms when first used
- Cause and effect MUST be explicit: "Increasing rear wing reduces oversteer because..."
- Trade-offs MUST be mentioned: "This will improve corner exit but reduce top speed"
- Explanations MUST relate to what the driver will feel, not just numbers
- The goal is teaching, not just fixing—drivers should learn from each session

**Rationale**: The system's value is not just faster lap times but driver education.
Understanding "why" builds driver intuition and trust.

### VI. Incremental Changes

The system MUST suggest small, testable setup changes rather than rewriting entire
setups.

- Recommend changing 1-3 related parameters per iteration, not wholesale rewrites
- Each change set MUST be independently testable on track
- Changes MUST be prioritized by expected impact on the identified problem
- The system MUST track change history to correlate adjustments with outcomes
- Driver feedback loop: change → test → report back → refine

**Rationale**: Small changes let drivers feel and understand each modification.
Large rewrites make it impossible to know what helped or hurt.

### VII. CLI-First MVP

The initial implementation MUST focus on a functional command-line interface before
any GUI or web interface.

- Core functionality MUST be fully usable via CLI commands
- CLI MUST support: analyze session, suggest changes, apply changes, compare setups
- Output MUST be both human-readable and machine-parseable (JSON option)
- No GUI work until CLI covers all core workflows
- CLI design MUST enable future GUI integration without architectural changes

**Rationale**: CLI-first ensures the core logic is solid and testable. GUI adds
complexity and should wrap proven functionality, not drive architecture.

## Technical Boundaries

### Technology Stack

- **Language**: Python 3.11+
- **Data Processing**: pandas, numpy, scipy for telemetry analysis
- **Storage**: Parquet for session data, .ini for setups
- **LLM Integration**: Claude API with function calling (Sonnet for fast analysis,
  Opus for complex reasoning)
- **CLI Framework**: Click or Typer
- **Testing**: pytest with fixtures for telemetry data

### Data Flow Constraints

- Telemetry capture runs in-game at 20-30Hz via AC Python app
- Post-session analysis only—no real-time setup changes
- All analysis is local; LLM calls are the only external dependency
- Setup files remain in AC's standard locations

### Quality Gates

- All code MUST pass type checking (mypy or pyright)
- Test coverage MUST include unit tests for metric calculations
- Integration tests MUST verify end-to-end CLI workflows
- Parser tests MUST cover malformed .ini handling

## Development Workflow

### Code Review Requirements

- All changes MUST be reviewed for constitution compliance
- Car-specific logic is an automatic rejection
- LLM doing calculations is an automatic rejection
- Setup changes without explanations are incomplete

### Testing Discipline

- Metric calculation code MUST have unit tests with known inputs/outputs
- Parser code MUST have tests for edge cases (missing sections, unknown params)
- CLI commands MUST have integration tests
- Test data MUST include both vanilla cars and mods

### Documentation Standards

- Public functions MUST have docstrings explaining purpose and parameters
- Complex algorithms MUST have inline comments explaining the physics reasoning
- CLI commands MUST have --help text that explains usage

## Governance

This constitution defines the non-negotiable principles for AC Race Engineer AI
development. All code, design decisions, and feature proposals MUST align with
these principles.

### Amendment Process

1. Propose amendment with rationale in writing
2. Review impact on existing code and architecture
3. Update constitution version following semantic versioning
4. Update any affected dependent artifacts
5. Document migration plan if breaking changes

### Compliance

- All pull requests MUST verify compliance with Core Principles
- Violations MUST be documented and justified in the Complexity Tracking section
  of the implementation plan
- Runtime guidance follows this constitution; conflicts resolve in favor of
  constitution principles

### Versioning Policy

- **MAJOR**: Principle removal or incompatible redefinition
- **MINOR**: New principle added or existing principle materially expanded
- **PATCH**: Clarifications, wording improvements, non-semantic changes

**Version**: 1.0.0 | **Ratified**: 2026-03-02 | **Last Amended**: 2026-03-02
