# Research: Principal Narrated Analysis

**Feature**: 033-principal-narrated-analysis | **Date**: 2026-03-11

## R-001: Principal Agent Structured Output via Pydantic AI

**Decision**: Use Pydantic AI's `result_type` parameter on `Agent` to enforce structured output (a new `PrincipalNarrative` model with `summary: str` and `explanation: str` fields).

**Rationale**: The project already uses `result_type=SpecialistResult` for specialist agents (`_build_specialist_agent` in agents.py). Using the same pattern for the principal agent ensures consistency and guarantees the two fields are always returned as distinct values. Pydantic AI handles JSON schema enforcement with the LLM provider.

**Alternatives considered**:
- Free-text output with post-hoc regex parsing: Fragile, provider-dependent formatting.
- Two separate LLM calls (one for summary, one for explanation): Doubles token cost, loses cross-field coherence.

## R-002: Where to Inject the Principal Agent Call

**Decision**: Invoke the principal agent after `_combine_results()`, `_resolve_conflicts()`, and `_post_validate_changes()` have all completed in `analyze_with_engineer()`. The principal agent replaces the `summary` and `explanation` fields on the `EngineerResponse` object that already has its final, clean set of changes.

**Rationale**: At this point, all specialist results are collected, merged, conflicts resolved by domain priority, and values clamped to valid ranges. The principal agent sees the exact set of changes the driver will receive, ensuring the narrative accurately describes the final recommendation.

**Alternatives considered**:
- Before conflict resolution/post-validation: The principal would narrate changes that may later be removed or modified, creating a mismatch between narrative and actual recommendation.
- Inside `_combine_results()`: Couples combination logic with LLM calls. Violates single-responsibility.

## R-003: Principal Agent — No Tools, Text-Only Synthesis

**Decision**: The principal agent for synthesis receives NO tools. All data (specialist domain_summaries, setup_changes with reasoning, driver_feedback, signals_addressed) is formatted into the user prompt as structured text. The existing `DOMAIN_TOOLS["principal"]` mapping is unchanged and continues to serve only the chat agent.

**Rationale**: The synthesis step is pure narrative generation from pre-computed data. Adding tools would create unnecessary LLM roundtrips and complexity. The spec explicitly states "this is a text-only synthesis pass, not a data-querying agent."

**Alternatives considered**:
- Providing read-only tools for the principal agent: Unnecessary complexity; all data is already available from specialist results.

## R-004: Database Migration Strategy

**Decision**: Add `explanation TEXT NOT NULL DEFAULT ''` to the recommendations table via ALTER TABLE in the existing `_MIGRATIONS` list in `storage/db.py`. Use the pattern: `ALTER TABLE recommendations ADD COLUMN explanation TEXT NOT NULL DEFAULT ''`.

**Rationale**: SQLite supports `ALTER TABLE ADD COLUMN` with default values. The existing migration system in `_MIGRATIONS` handles sequential schema changes. Default empty string ensures existing rows are valid and the frontend hides the expandable section for legacy data.

**Alternatives considered**:
- Recreate table with new schema: Destructive, risks data loss, unnecessary for a simple column addition.

## R-005: Fallback Behavior on Principal Agent Failure

**Decision**: Wrap the principal agent call in `try/except Exception`. On failure, log a warning and keep the `_combine_results()` output (concatenated domain_summaries) as both `summary` and `explanation`. The analysis proceeds normally.

**Rationale**: The spec requires graceful degradation (FR-011). The concatenated output is the current behavior and is known to work. A principal agent failure (network, provider, malformed response) must never block an analysis.

**Alternatives considered**:
- Retry with exponential backoff: Adds latency; the fallback text is adequate.
- Return error to user: Violates FR-011 and degrades UX.

## R-006: Token Budget and Usage Limits

**Decision**: Apply `UsageLimits(request_limit=5)` to the principal agent, matching the spec's instruction. The principal prompt will instruct concise output: summary under 80 words, explanation under 300 words.

**Rationale**: The principal agent is a single-turn synthesis (no tools, no multi-turn). `request_limit=5` is generous — it should complete in 1 request. The word limits keep token consumption predictable and within Phase 9 optimization targets.

## R-007: Existing Infrastructure That Requires No Changes

**Decision**: The following are already in place and need no modification:
- `EngineerResponse.explanation` field (models.py) — exists, currently set to concatenated text
- `RecommendationDetailResponse.explanation` field (serializers.py) — exists with default `""`
- `RecommendationDetailResponse` in frontend types.ts — already has `explanation: string`
- `DOMAIN_TOOLS["principal"]` — unchanged, used only by chat agent
- LLM event tracking infrastructure (save_llm_event, extract_tool_calls) — reusable as-is

**Rationale**: The feature was partially anticipated in earlier phases. The existing scaffolding reduces implementation scope to: (1) principal agent synthesis function, (2) DB migration + save_recommendation update, (3) API route update to read explanation from DB, (4) frontend expandable section.

## R-008: Frontend Expandable Explanation Section

**Decision**: Use a collapsible `<details>`-style pattern within `RecommendationCard.tsx`. Collapsed by default. Hidden entirely when `explanation` is empty. Render explanation with paragraph breaks (split on `\n\n`).

**Rationale**: Consistent with the existing card layout. No new UI components needed — the expandable pattern can be implemented with a toggle state and CSS transition. The spec requires collapsed-by-default (FR-009) and hidden-when-empty (FR-009).

**Alternatives considered**:
- Modal dialog for explanation: Too heavy; explanation is part of the recommendation context.
- Always-visible section: Clutters the card for quick scanning.
