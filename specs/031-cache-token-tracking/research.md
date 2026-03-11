# Research: Cache Token Tracking

**Feature**: 031-cache-token-tracking | **Date**: 2026-03-11

## R1: Pydantic AI RunUsage Cache Fields

**Decision**: Read `cache_read_tokens` and `cache_write_tokens` directly from `result.usage()` return value.

**Rationale**: The Pydantic AI `RunUsage` dataclass already exposes `cache_read_tokens: int` and `cache_write_tokens: int` as top-level fields. These are populated by the framework's provider adapters for Anthropic (prompt caching), OpenAI (cached input), and Gemini (cached content). The values default to 0 when the provider doesn't report caching. No framework patches or custom extraction needed.

**Alternatives considered**:
- Parsing raw provider responses for cache headers → rejected; duplicates framework logic, provider-specific code violates Principle XI
- Inferring cache from token count differences → rejected; unreliable approximation

## R2: SQLite Additive Migration Strategy

**Decision**: Add migration 7 with two `ALTER TABLE ADD COLUMN` statements, each with `DEFAULT 0`.

**Rationale**: SQLite supports `ALTER TABLE ... ADD COLUMN ... DEFAULT <value>` which applies the default to all existing rows without rewriting the table. This is a constant-time operation regardless of table size. The project already uses this pattern (migrations 1-6 in `db.py`). Using `DEFAULT 0` ensures:
1. Existing rows get 0 automatically (no data migration script needed)
2. `NOT NULL` can be enforced with `CHECK(col >= 0)` matching existing column style
3. No destructive migration; no data loss risk

**Alternatives considered**:
- Separate cache tracking table → rejected; over-normalized for two integer columns, adds JOIN complexity
- JSON blob column → rejected; not queryable, loses type safety, breaks existing field-per-column pattern

## R3: Conditional UI Display Pattern

**Decision**: Check if `cache_read_tokens > 0 || cache_write_tokens > 0` before rendering cache UI elements. Use the same `formatTokenCount()` utility for display.

**Rationale**: The spec requires hiding cache info when all values are zero (FR-008). A simple conditional check at render time is the most straightforward approach. No new components needed — just conditional sections within existing `UsageSummaryBar` and `UsageDetailModal`.

**Alternatives considered**:
- Separate "cache-aware" component variants → rejected; over-engineering for conditional text display
- Backend omitting zero fields from JSON → rejected; inconsistent API shape complicates frontend typing

## R4: Cache Token Semantics Across Providers

**Decision**: Store raw values from `RunUsage` without provider-specific interpretation. Both fields are integers >= 0.

**Rationale**: All three providers report cache tokens as integer counts:
- **Anthropic**: `cache_read_input_tokens` (from cache), `cache_creation_input_tokens` (written to cache) — mapped by Pydantic AI to `cache_read_tokens`/`cache_write_tokens`
- **OpenAI**: `cached_tokens` within `prompt_tokens_details` — mapped to `cache_read_tokens`; write tokens typically 0
- **Gemini**: `cached_content_token_count` — mapped to `cache_read_tokens`; write tokens typically 0

The framework normalizes provider differences. Storing the normalized values preserves provider-agnostic design (Principle XI).

**Alternatives considered**:
- Storing provider-specific raw fields → rejected; violates provider abstraction, triples storage complexity
