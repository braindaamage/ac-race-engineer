# Data Model: Engineer Endpoints

## Existing Entities (no modifications)

### SessionRecord (storage/models.py)
- `session_id: str` (PK)
- `car: str`
- `track: str`
- `session_date: str`
- `lap_count: int`
- `best_lap_time: float | None`
- `state: str` — "discovered" | "parsed" | "analyzed" | "engineered"
- `session_type: str | None`
- `csv_path: str | None`
- `meta_path: str | None`

**State transitions in this phase**: analyzed → engineered (on successful engineer job)

### Recommendation (storage/models.py)
- `recommendation_id: str` (PK, uuid4 hex)
- `session_id: str` (FK → sessions)
- `status: str` — "proposed" | "applied" | "rejected"
- `summary: str`
- `created_at: str` (ISO 8601 UTC)
- `changes: list[SetupChange]`

**Status transitions in this phase**: proposed → applied (via POST /apply)

### SetupChange (storage/models.py)
- `change_id: str` (PK, uuid4 hex)
- `recommendation_id: str` (FK → recommendations)
- `section: str`
- `parameter: str`
- `old_value: str`
- `new_value: str`
- `reasoning: str`

### Message (storage/models.py)
- `message_id: str` (PK, uuid4 hex)
- `session_id: str` (FK → sessions)
- `role: str` — "user" | "assistant"
- `content: str`
- `created_at: str` (ISO 8601 UTC)

## New Entities (API layer only — not persisted in SQLite)

### EngineerResponse Cache File
Full `EngineerResponse` JSON saved to `{sessions_dir}/{session_id}/recommendation_{rec_id}.json` after the engineer job completes. Preserves fields not in the SQLite schema:
- `driver_feedback: list[DriverFeedback]`
- `explanation: str`
- `confidence: str`
- `signals_addressed: list[str]`
- `setup_changes: list[SetupChange]` (engineer model, richer than storage model)

### API Response Models (api/engineer/serializers.py)

**EngineerJobResponse** — returned by POST /engineer (202)
- `job_id: str`
- `session_id: str`

**RecommendationSummary** — item in recommendation list
- `recommendation_id: str`
- `session_id: str`
- `status: str`
- `summary: str`
- `change_count: int`
- `created_at: str`

**RecommendationListResponse** — returned by GET /recommendations
- `session_id: str`
- `recommendations: list[RecommendationSummary]`

**SetupChangeDetail** — rich setup change for recommendation detail
- `section: str`
- `parameter: str`
- `old_value: str`
- `new_value: str`
- `reasoning: str`
- `expected_effect: str` (from cache file, or "" if unavailable)
- `confidence: str` (from cache file, or "medium" if unavailable)

**DriverFeedbackDetail** — driver feedback item
- `area: str`
- `observation: str`
- `suggestion: str`
- `corners_affected: list[int]`
- `severity: str`

**RecommendationDetailResponse** — returned by GET /recommendations/{rec_id}
- `recommendation_id: str`
- `session_id: str`
- `status: str`
- `summary: str`
- `explanation: str`
- `confidence: str`
- `signals_addressed: list[str]`
- `setup_changes: list[SetupChangeDetail]`
- `driver_feedback: list[DriverFeedbackDetail]`
- `created_at: str`

**ApplyRequest** — body for POST /recommendations/{rec_id}/apply
- `setup_path: str`

**ApplyResponse** — returned by POST /apply
- `recommendation_id: str`
- `status: str` (always "applied")
- `backup_path: str`
- `changes_applied: int`

**ChatRequest** — body for POST /messages
- `content: str`

**ChatJobResponse** — returned by POST /messages (202)
- `job_id: str`
- `message_id: str`

**MessageResponse** — single message in history
- `message_id: str`
- `role: str`
- `content: str`
- `created_at: str`

**MessageListResponse** — returned by GET /messages
- `session_id: str`
- `messages: list[MessageResponse]`

**ClearMessagesResponse** — returned by DELETE /messages
- `session_id: str`
- `deleted_count: int`
