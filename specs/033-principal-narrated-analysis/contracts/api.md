# API Contract Changes: Principal Narrated Analysis

## Modified Endpoints

### GET /sessions/{session_id}/recommendations/{recommendation_id}

**Change**: `explanation` field is now populated from the SQLite database (previously only from JSON cache).

**Response** (RecommendationDetailResponse — no schema change):
```json
{
  "recommendation_id": "uuid",
  "session_id": "session-id",
  "status": "proposed",
  "summary": "Principal-authored executive headline (2–4 sentences)",
  "explanation": "Principal-authored detailed narrative (multi-paragraph)",
  "confidence": "medium",
  "signals_addressed": ["high_understeer", "high_tyre_wear"],
  "setup_changes": [...],
  "driver_feedback": [...],
  "created_at": "2026-03-11T12:00:00"
}
```

**Behavior change**:
- Before: `explanation` came from cached JSON only; empty string if cache missing
- After: `explanation` comes from DB; cache used as secondary source for other fields

**Backwards compatibility**: No breaking changes. `explanation` was already in the response schema with default `""`. Clients that ignore the field continue to work. Legacy recommendations (pre-migration) return `explanation: ""`.

## No New Endpoints

No new endpoints are introduced. The principal agent synthesis is internal to the analysis pipeline.

## Internal Contract: save_recommendation()

```python
def save_recommendation(
    db_path: str | Path,
    session_id: str,
    summary: str,
    changes: list[SetupChange],
    explanation: str = "",        # NEW parameter
) -> Recommendation:
```

The returned `Recommendation` object now includes an `explanation: str` field.
