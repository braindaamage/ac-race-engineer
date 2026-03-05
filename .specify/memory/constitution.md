<!--
SYNC IMPACT REPORT
==================
Version change: 1.4.0 -> 1.5.0 (MINOR: new Principle XII added, Principle X
expanded with sidecar launch/health-check/shutdown rules, Quality Gates and
Development Environment updated for frontend tooling.)

Modified principles:
- X: "Desktop App Stack" -> expanded with sidecar lifecycle rules (port 57832,
  health poll, splash screen, shutdown endpoint)

Added principles:
- XII: "Frontend Architecture Constraints" (state management layers, design
  system tokens, font rules, storage prohibition, TypeScript strict, component
  reuse mandate)

Added sections:
- Quality Gates: 4 frontend quality requirements
- Development Environment: Node.js tooling requirements (Node 20 LTS, npm,
  dev/build commands)

Removed principles: None
Removed sections: None

Modified sections:
- Quality Gates: added frontend TypeScript strict, design system tests,
  no explicit any, API integration tests
- Development Environment: added Node.js 20 LTS, npm, dev/build commands

Templates requiring updates:
- .specify/templates/plan-template.md: No updates needed (generic)
- .specify/templates/spec-template.md: No updates needed (generic)
- .specify/templates/tasks-template.md: No updates needed (generic)
- No command templates exist (.specify/templates/commands/ is empty)

Follow-up TODOs: None
==================
-->

# AC Race Engineer AI Constitution

**Version**: 1.5.0 | **Ratified**: 2026-03-02 | **Last Amended**: 2026-03-05

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
receives only pre-processed metrics to reason about. All LLM interactions MUST
go through Pydantic AI agents and MUST NOT call provider SDKs directly.

- The LLM MUST NOT perform calculations (averages, deltas, physics formulas)
- Metrics passed to the LLM MUST be fully computed with clear labels and units
- Setup change suggestions MUST come via Pydantic AI tool calls, not free text
- The LLM's role is interpretation: "tire temps show understeer" not "avg 92.3C"
- Deterministic code MUST be testable independent of LLM behavior
- All LLM calls MUST be made via Pydantic AI agents (see Principle XI for
  provider abstraction details)

**Rationale**: LLMs are unreliable calculators. Reproducible numerical analysis
requires deterministic code. LLMs excel at pattern recognition and explanation.
Provider abstraction via Pydantic AI ensures no vendor lock-in.

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
- Driver feedback loop: change -> test -> report back -> refine

**Rationale**: Small changes let drivers feel and understand each modification.
Large rewrites make it impossible to know what helped or hurt.

### VII. Desktop App as Primary Interface

The Tauri + React desktop app (Phase 7) is the primary user interface. It wraps
the proven FastAPI backend without duplicating logic.

- The desktop app MUST communicate with the backend exclusively via the localhost
  HTTP API
- The frontend MUST NOT contain analysis logic, setup file access, or LLM calls
  of any kind
- All user-facing workflows (session list, lap analysis, setup compare, engineer
  chat, apply setup) MUST be driven by API responses, not locally derived data
- The app MUST handle background job progress via WebSocket streaming (job_id
  pattern from Phase 6.1)
- UI state MUST reflect data returned from the API—no client-side recalculation
  of metrics
- The backend MUST be launched as a Tauri sidecar subprocess
  (python -m api.server --port 57832) and terminated cleanly on app exit

**Rationale**: The CLI-first constraint (previous Principle VII) ensured the
backend was solid before any UI work began. That goal is achieved: Phase 6
delivered 26 HTTP endpoints + 1 WebSocket with 744 tests passing. The desktop
app now defines the user experience, and its architecture must be governed to
prevent logic duplication or direct file access from the frontend.

### VIII. API-First Design

All analysis logic MUST live in `backend/ac_engineer/` as pure Python functions.
FastAPI routes MUST be thin wrappers that delegate to these functions.

- `ac_engineer/` modules MUST NOT contain HTTP-specific code (no Request/Response
  objects, no web framework imports)
- The same `ac_engineer/` functions MUST be callable from the API, CLI, or tests
  without modification
- FastAPI routes MUST handle request validation (via Pydantic) and call `ac_engineer/`
  functions; no business logic lives in route handlers
- This ensures the analysis engine is independently testable without a running server

**Rationale**: Coupling analysis logic to HTTP transport creates untestable and
inflexible code. Keeping pure functions in `ac_engineer/` enables CLI, API, and
test consumers without duplication.

### IX. Separation of Concerns — Three Layers

The system MUST maintain strict separation across three layers, each with defined
responsibilities and prohibited cross-layer concerns.

- **`ac_engineer/` modules**: Pure computation only. Permitted: file reads,
  pandas/numpy operations, Pydantic AI agent calls. Prohibited: HTTP awareness,
  web framework imports, frontend concerns
- **`api/` routes**: HTTP interface only. Permitted: Pydantic request/response
  models, calling `ac_engineer/` functions, HTTP status codes. Prohibited:
  business logic, direct file I/O beyond what `ac_engineer/` exposes, LLM calls
- **`frontend/`**: Visualization and user interaction only. Permitted: HTTP calls
  to `api/` endpoints, UI state management. Prohibited: analysis logic, direct
  data file access, LLM calls of any kind
- Cross-layer imports MUST flow in one direction: `api/` -> `ac_engineer/`;
  `frontend/` -> `api/` (via HTTP only)
- Reverse imports (e.g., `ac_engineer/` importing from `api/`) are FORBIDDEN

**Rationale**: Clear layer boundaries make each component independently testable,
replaceable, and comprehensible. Violations create hidden coupling that makes
future changes expensive.

### X. Desktop App Stack

The desktop application (Phase 7) MUST use Tauri as the native Windows shell and
React with TypeScript as the UI layer, communicating with the backend via localhost
HTTP.

- The Tauri shell (`frontend/src-tauri/`) MUST contain minimal Rust configuration
  only—no business logic in Rust
- The React app (`frontend/src/`) MUST consume backend endpoints exclusively; no
  direct file system access from the frontend
- The backend FastAPI server MUST be started as a subprocess when the Tauri app
  launches
- The frontend MUST NOT duplicate any logic already present in `ac_engineer/`
  modules
- UI state MUST reflect data returned from the API, not locally derived analysis
- The backend sidecar MUST be launched as `python -m api.server --port 57832`
  and bound exclusively to `http://127.0.0.1:57832`
- The frontend MUST NOT hardcode any other port; the canonical port is 57832
- On app launch, the frontend MUST poll `GET /health` (max 30 retries x 500ms
  = 15s timeout) before rendering any UI
- During the health check wait, a splash screen MUST be shown—no other UI is
  accessible
- If the backend fails to respond within 15 seconds, an error state MUST be
  shown with a "Retry" button; the app MUST NOT crash silently
- On app exit, the frontend MUST call `POST /shutdown` before terminating the
  sidecar process

**Rationale**: Tauri provides native Windows integration without Electron's overhead.
Starting the backend as a subprocess keeps the distribution self-contained while
preserving the API-first architecture from Principle VIII. The health-check gate
ensures the UI never renders against an unavailable backend, preventing confusing
error states during startup.

### XI. LLM Provider Abstraction

All LLM interactions in `backend/ac_engineer/engineer/` MUST be implemented using
Pydantic AI agents. Direct calls to provider SDKs (Anthropic, OpenAI, Google) are
FORBIDDEN in application code.

- The active LLM provider MUST be selectable via configuration (environment variable
  or config file), not hardcoded in source
- Supported providers MUST include at minimum: Anthropic Claude, OpenAI, Google Gemini
- Pydantic AI tools (function calling) MUST be used for all structured interactions
  (setup reads, setup modifications, metric queries)
- Provider-specific behavior differences MUST NOT leak into `ac_engineer/` business
  logic
- Switching providers MUST require only a configuration change, not code changes

**Rationale**: Vendor lock-in to a single LLM provider creates dependency risk and
limits model selection. Pydantic AI provides a stable abstraction layer that allows
switching providers as models improve or pricing changes.

### XII. Frontend Architecture Constraints

The React frontend (Phase 7) MUST follow these structural rules across all subfases
(7.1 through 7.6). Violations in any subfase are automatic rejections during review.

- **State management layers**: Server/API state MUST be managed exclusively with
  TanStack Query v5. Zustand v5 MUST be used for global UI state (selected session,
  active view, job progress). React `useState` is permitted for component-local
  state only. These three layers MUST NOT be mixed
- **Immutable analysis data**: Telemetry analysis data (laps, corners, stints,
  consistency) is immutable once fetched and MUST use `staleTime: Infinity` in
  TanStack Query to prevent unnecessary refetches
- **Design system tokens**: The CSS custom properties defined in Phase 7.1
  (`--color-red`, `--color-blue-ai`, `--color-green`, `--color-amber`, `--bg`,
  `--surface`, `--text-primary`, `--text-secondary`, `--border`) are the ONLY
  permitted source of color values. Hardcoded hex values in component files are
  FORBIDDEN
- **Numeric font**: JetBrains Mono MUST be used for all numeric data: lap times,
  telemetry values, setup parameter values, deltas. Using Inter or any other font
  for numeric data is FORBIDDEN
- **No browser storage**: `localStorage` and `sessionStorage` MUST NOT be used
  anywhere in the frontend. All state is in-memory (TanStack Query cache + Zustand
  store) and rehydrated from the API on app launch
- **TypeScript strict mode**: TypeScript strict mode MUST be enabled. Explicit
  `any` type annotations are FORBIDDEN without a documented justification comment
- **Component reuse**: All design system components (Button, Card, Badge, DataCell,
  etc.) defined in Phase 7.1 MUST be used. Inline one-off styled elements that
  duplicate component behavior are FORBIDDEN

**Rationale**: These constraints ensure visual and behavioral consistency across all
6 subfases, prevent state management chaos, and guarantee the design system is the
single source of truth for the UI.

## Technical Boundaries

### Technology Stack

Three-component architecture:

1. **AC In-Game App** (Phases 1-1.5, completed):
   - Python ~3.3 (AC embedded runtime; conda does not apply)
   - Captures telemetry to CSV at 20-30Hz

2. **Backend** (Phases 2-6):
   - Python 3.11+ in conda env `ac-race-engineer`
   - FastAPI for HTTP API server
   - pandas, numpy, scipy for telemetry analysis
   - Pydantic AI for LLM agent framework (provider-agnostic)
   - pytest for testing

3. **Desktop App** (Phase 7):
   - Tauri (Rust) for native Windows shell
   - React with TypeScript for UI
   - Communicates with backend via localhost HTTP

**Storage**: CSV for in-game capture, Parquet for post-processed sessions, .ini for setups, SQLite (stdlib sqlite3) for local relational persistence of sessions index, recommendations, setup change history, and conversation messages

**LLM Providers** (selectable via config): Anthropic Claude, OpenAI, Google Gemini

### Project Structure

```
ac_app/                  # AC in-game app (Python ~3.3, completed)
backend/
  ac_engineer/           # Core Python package
    parser/              # Telemetry & setup file parsing
    analyzer/            # Metric calculation engine
    knowledge/           # Vehicle dynamics knowledge base + loader
    config/              # User configuration (ACConfig, read/write config.json)
    storage/             # Local SQLite persistence (sessions, recommendations, setup_changes, messages)
    engineer/            # Pydantic AI agents for setup reasoning
  api/                   # FastAPI server (thin HTTP wrappers)
  tests/                 # pytest tests for all backend modules
frontend/
  src/                   # React app (TypeScript)
  src-tauri/             # Tauri shell (Rust, minimal config only)
data/
  sessions/              # Telemetry CSV + metadata (.meta.json) per session
  setups/                # Setup .ini files
  config.json            # User configuration (ac_install_path, llm_provider, llm_model)
  ac_engineer.db         # SQLite database (sessions, recommendations, setup_changes, messages)
build/
  ac_engineer.spec       # PyInstaller spec for standalone .exe
  README_build.md        # Build and distribution documentation
```

### Data Flow Constraints

- Telemetry capture runs in-game at 20-30Hz via AC Python app
- Post-session analysis only—no real-time setup changes
- All analysis is local; LLM provider calls are the only external dependency
- Session metadata, engineer recommendations, setup change history, and conversation messages are persisted locally in SQLite (data/ac_engineer.db). User configuration is persisted in data/config.json. Both files are created automatically on first run.
- Setup files remain in AC's standard locations
- Frontend communicates with backend exclusively via localhost HTTP (FastAPI)

### Quality Gates

- All code MUST pass type checking (mypy or pyright)
- Test coverage MUST include unit tests for metric calculations
- Integration tests MUST verify end-to-end API workflows
- Parser tests MUST cover malformed .ini handling
- `ac_engineer/` modules MUST be testable without starting the FastAPI server
- Frontend MUST have TypeScript strict mode enabled with zero type errors on build
- Design system components MUST have unit tests covering all variants and states
- No explicit `any` in TypeScript without a justification comment
- All API integration points MUST be covered by integration tests using mock
  API responses

### Development Environment

All Python development outside of Assetto Corsa's embedded runtime MUST use
the project's conda environment.

- Environment name: `ac-race-engineer` with Python 3.11+
- Before running ANY Python code, script, test, or installation command,
  MUST activate with `conda activate ac-race-engineer`
- MUST NOT install packages or run scripts in the base conda environment or
  system Python
- If the environment does not exist, create it with
  `conda create -n ac-race-engineer python=3.11 -y` before proceeding
- Applies to: post-processing utilities, tests, CLI tools, analysis modules,
  FastAPI server
- SOLE EXCEPTION: Code running inside AC's embedded Python app (telemetry
  capture), which uses AC's own Python ~3.3 runtime with no conda access

All frontend development MUST use Node.js with the following requirements:

- Node.js 20 LTS or higher MUST be used for all frontend development
- Package manager: npm (the project's existing lock file format MUST be respected)
- Frontend development server runs via `npm run dev` from the `frontend/` directory
- Frontend builds via `npm run build` before Tauri packaging

**Rationale**: Consistent environment management prevents dependency conflicts
and ensures reproducible builds across all development phases.

## Development Workflow

### Code Review Requirements

- All changes MUST be reviewed for constitution compliance
- Car-specific logic is an automatic rejection
- LLM doing calculations is an automatic rejection
- Business logic in FastAPI route handlers is an automatic rejection
- `ac_engineer/` importing from `api/` is an automatic rejection
- Setup changes without explanations are incomplete

### Testing Discipline

- Metric calculation code MUST have unit tests with known inputs/outputs
- Parser code MUST have tests for edge cases (missing sections, unknown params)
- API endpoints MUST have integration tests
- `ac_engineer/` functions MUST have tests that run without a live API server
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
