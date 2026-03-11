# Data Model: Principal Narrated Analysis

**Feature**: 033-principal-narrated-analysis | **Date**: 2026-03-11

## New Models

### PrincipalNarrative (backend/ac_engineer/engineer/models.py)

Pydantic AI structured output model for the principal agent synthesis step.

| Field       | Type | Constraints                              | Description                                                    |
|-------------|------|------------------------------------------|----------------------------------------------------------------|
| summary     | str  | 2–4 sentences, ≤80 words target          | Executive headline: dominant problem, severity, correction direction. Driver-friendly language. |
| explanation | str  | Multi-paragraph, ≤300 words target       | Detailed narrative connecting specialist findings causally. Trade-offs, technique integration, expected feel. |

**Validation**: Both fields must be non-empty strings (Pydantic default). No hard truncation — word limits are prompt-guided, not enforced programmatically.

## Modified Models

### EngineerResponse (backend/ac_engineer/engineer/models.py)

No schema changes. Fields `summary` and `explanation` already exist. Change is behavioral: they will now contain distinct, principal-agent-authored text instead of identical concatenated domain_summaries.

| Field       | Before (current)                        | After (this feature)                              |
|-------------|-----------------------------------------|---------------------------------------------------|
| summary     | Concatenated domain_summaries           | Principal-authored executive headline (2–4 sentences) |
| explanation | Identical to summary                    | Principal-authored detailed narrative (multi-paragraph) |

### Recommendation (SQLite table: recommendations)

Add `explanation` column.

| Column           | Type | Default | Migration                                        |
|------------------|------|---------|--------------------------------------------------|
| explanation      | TEXT | `''`    | ALTER TABLE recommendations ADD COLUMN explanation TEXT NOT NULL DEFAULT '' |

### save_recommendation() (backend/ac_engineer/storage/recommendations.py)

New parameter:

| Parameter   | Type | Default | Description                     |
|-------------|------|---------|---------------------------------|
| explanation | str  | `""`    | Explanation text to persist alongside summary |

### Recommendation return model (storage)

The `Recommendation` namedtuple/model returned by `get_recommendations()` gains an `explanation: str` field populated from the database.

## Unchanged Models

- **SpecialistResult**: No changes. `domain_summary` field unchanged.
- **SetupChange**: No changes.
- **DriverFeedback**: No changes.
- **AgentDeps**: No changes.
- **LlmEvent / LlmToolCall**: No changes. Principal agent usage tracked via existing infrastructure.
- **RecommendationDetailResponse** (API serializer): Already has `explanation: str = ""`. No schema change needed — just needs to be populated from DB.
- **RecommendationDetailResponse** (frontend types.ts): Already has `explanation: string`. No change needed.

## State Transitions

```
Specialist agents complete
  → _combine_results() produces EngineerResponse with concatenated summary/explanation
    → _resolve_conflicts() (existing)
    → _post_validate_changes() (existing)
    → Principal agent synthesis (NEW)
      → Success: replace summary + explanation with principal-authored text
      → Failure: keep concatenated text (fallback)
    → save_recommendation(summary=..., explanation=...) → SQLite
    → Cache EngineerResponse as JSON
    → Return to API → Frontend displays summary + expandable explanation
```

## Database Migration

Added to `_MIGRATIONS` list in `storage/db.py`:

```sql
ALTER TABLE recommendations ADD COLUMN explanation TEXT NOT NULL DEFAULT '';
```

Position: Appended after the last existing migration. The migration system applies migrations sequentially by index.
