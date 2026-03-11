# Research: Agent Diagnostic Traces

**Feature**: 032-agent-diagnostic-traces | **Date**: 2026-03-11

## R1: Pydantic AI Message Serialization

**Decision**: Manually iterate `result.all_messages()` and serialize each message part to a structured dict, then format as Markdown.

**Rationale**: Pydantic AI's `ModelRequest` and `ModelResponse` are not Pydantic BaseModel instances — they lack `model_dump()`. The message parts (`SystemPromptPart`, `UserPromptPart`, `TextPart`, `ToolCallPart`, `ToolReturnPart`) have typed fields that must be accessed directly. The codebase already does this in `extract_tool_calls()` (agents.py:196-217), which iterates `result.all_messages()` and checks `isinstance(part, ToolReturnPart)`.

For trace serialization, we iterate all messages and handle each part type:
- `SystemPromptPart` → system prompt text
- `UserPromptPart` → user prompt text
- `TextPart` → assistant text response
- `ToolCallPart` → tool name + arguments (JSON)
- `ToolReturnPart` → tool name + response content

**Alternatives considered**:
- Using `repr()` or `str()` on message objects → rejected; output is not human-readable and format may change across Pydantic AI versions
- Storing raw Python objects via pickle → rejected; not human-readable (violates FR-007), not portable
- Using `json.dumps()` on messages → rejected; not serializable without custom encoder, and raw JSON is harder to scan than formatted Markdown

## R2: Trace File Format — Markdown

**Decision**: Write traces as Markdown (`.md`) files. Each agent gets a section with its system prompt, user prompt, and conversation turns formatted with code blocks and headings.

**Rationale**: Markdown is human-readable in any text editor (satisfies FR-007), renders nicely in viewers (GitHub, VS Code preview), and supports structured formatting (headings, code blocks, lists). Tool call parameters and responses are formatted as JSON code blocks for readability. The spec requires that "a developer should be able to open the file in a text editor and understand the full agent interaction" — Markdown excels at this.

**Alternatives considered**:
- JSON files → rejected; deeply nested structure is hard to scan visually; satisfies machine-readability but not human-readability for multi-turn conversations
- Plain text → rejected; lacks structure; hard to distinguish system prompts from user prompts from tool calls
- YAML → rejected; indentation-sensitive format is fragile for large content blocks; less universal tooling support than Markdown

## R3: Trace File Storage Location

**Decision**: Store traces in `data/traces/` directory, with filenames keyed by type and ID: `rec_{recommendation_id}.md` for analysis traces, `msg_{message_id}.md` for chat traces.

**Rationale**: The `data/` directory already houses session-specific and ephemeral data (sessions, setups, config, database). Traces are ephemeral diagnostic files — they belong alongside other data artifacts, not in the source tree. Using a flat directory with type-prefixed filenames keeps the implementation simple and avoids nested directory creation. The recommendation_id and message_id are UUID4 strings, so there's no collision risk.

**Alternatives considered**:
- Storing traces inside session directories (`data/sessions/{session_id}/trace_*.md`) → rejected; traces for the same session could accumulate, session directory cleanup would need to consider traces, and the session_id is not directly available from a recommendation_id without a DB lookup
- Using a `traces/` subdirectory per session → rejected; over-complex directory structure for diagnostic files
- Temp directory → rejected; traces should survive application restarts for later inspection

## R4: Config Field vs Separate Config File

**Decision**: Add `diagnostic_mode: bool = False` to the existing `ACConfig` Pydantic model.

**Rationale**: ACConfig already holds all application settings and is read/written atomically via `config.json`. Adding one boolean field follows the established pattern (same as `onboarding_completed`). The config is read at pipeline entry points (`make_engineer_job`, `make_chat_job`), so the diagnostic_mode flag is naturally available where trace capture decisions are made.

**Alternatives considered**:
- Separate diagnostic config file → rejected; unnecessary complexity; user would need to manage two config files
- Environment variable → rejected; not configurable from the Settings UI; inconsistent with other settings
- Database flag → rejected; would require DB access at trace decision point; ACConfig is already passed into pipeline functions

## R5: Trace Capture Integration Points

**Decision**: Capture traces at two points: (1) inside `analyze_with_engineer()` after each `agent.run()` in the specialist loop, collecting all agent messages, then writing the combined trace after the recommendation is persisted; (2) inside `make_chat_job()` after `agent.run()` and after `save_message()`, writing the single-agent trace.

**Rationale**: These are the exact points where `result.all_messages()` is available and the context IDs (recommendation_id, message_id) are known. The existing usage capture code follows this same pattern — it accesses `result.usage()` and `result.all_messages()` at these points, wrapped in try-except to prevent pipeline failures.

The trace write must happen AFTER the primary result is saved (recommendation or message), so the association ID is known and the user gets their result even if trace writing fails. This mirrors the existing usage capture pattern (non-critical, try-except wrapped).

**Alternatives considered**:
- Middleware/decorator approach → rejected; the result object is only available inside the pipeline function, not at the middleware level
- Background task for trace writing → rejected; trace files are small (< 100KB typically); synchronous write after the result is negligible overhead and avoids task management complexity
- Pydantic AI agent hooks/callbacks → rejected; would couple trace logic to agent construction; harder to test independently

## R6: Diagnostic Mode Guard — Read Config Once at Pipeline Start

**Decision**: Read `config.diagnostic_mode` once at the start of each pipeline function and pass it as a boolean flag. Do not re-read config during execution.

**Rationale**: The spec's edge case section states "The toggle state at the moment the agent pipeline starts determines whether traces are captured for that run." Reading config once and using it throughout ensures consistent behavior even if the user toggles diagnostic mode mid-analysis. This also avoids unnecessary file I/O during the agent loop.

The config object is already passed to `make_engineer_job()` and `make_chat_job()` — checking `config.diagnostic_mode` is a simple boolean read.

**Alternatives considered**:
- Re-reading config before each trace write → rejected; inconsistent behavior if toggled during analysis; extra I/O
- Global diagnostic state → rejected; thread-safety concerns; config is the single source of truth
