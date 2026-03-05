# Data Model: Config, Knowledge & Packaging Endpoints

**Feature**: 014-config-knowledge-endpoints | **Date**: 2026-03-05

## Existing Entities (read-only reference)

### ACConfig
- **Source**: `ac_engineer.config.models.ACConfig`
- **Fields**: ac_install_path (Path|None), setups_path (Path|None), llm_provider (str, default "anthropic"), llm_model (str|None)
- **Computed**: is_ac_configured (bool), is_setups_configured (bool), ac_cars_path (Path|None), ac_tracks_path (Path|None)
- **Persistence**: JSON file at `data/config.json`
- **Constraint**: llm_provider must be one of ("anthropic", "openai", "gemini")

### KnowledgeFragment
- **Source**: `ac_engineer.knowledge.models.KnowledgeFragment`
- **Fields**: source_file (str), section_title (str), content (str), tags (list[str])
- **Persistence**: In-memory, loaded from markdown docs at startup

### SessionRecord
- **Source**: `ac_engineer.storage.models.SessionRecord`
- **Fields**: session_id (str), car (str), track (str), state (str), csv_path (str|None), meta_path (str|None), created_at (str)
- **State values**: "discovered", "analyzed", "engineered"

## New API Models (response/request only, no persistence)

### ConfigResponse
- **Purpose**: API response for GET /config
- **Fields**: ac_install_path (str), setups_path (str), llm_provider (str), llm_model (str)
- **Invariant**: All fields are strings, never null. None values from ACConfig coerced to ""
- **Relationship**: Built from ACConfig at the route handler level

### ConfigUpdateRequest
- **Purpose**: API request body for PATCH /config
- **Fields**: ac_install_path (str|None, optional), setups_path (str|None, optional), llm_provider (str|None, optional), llm_model (str|None, optional)
- **Constraint**: Extra fields are forbidden (rejected with 422)
- **Behavior**: Only fields present in the request body are updated. Absent fields are left unchanged. Uses `exclude_unset=True` to distinguish "not sent" from "sent as null".

### ConfigValidationResponse
- **Purpose**: API response for GET /config/validate
- **Fields**: ac_path_valid (bool), setups_path_valid (bool), llm_provider_valid (bool), is_valid (bool)
- **Invariant**: is_valid is True only when all three per-field checks pass
- **Validation rules**:
  - ac_path_valid: ac_install_path is not empty AND path exists on disk
  - setups_path_valid: setups_path is not empty AND path exists on disk
  - llm_provider_valid: llm_provider is non-empty and in the allowed list

### KnowledgeFragmentResponse
- **Purpose**: API representation of a knowledge fragment
- **Fields**: source_file (str), section_title (str), content (str), tags (list[str])
- **Relationship**: 1:1 mapping from KnowledgeFragment

### KnowledgeSearchResponse
- **Purpose**: API response for GET /knowledge/search
- **Fields**: query (str), results (list[KnowledgeFragmentResponse]), total (int)
- **Invariant**: len(results) <= 10; total is the unfiltered count before capping

### SessionKnowledgeResponse
- **Purpose**: API response for GET /sessions/{id}/knowledge
- **Fields**: session_id (str), signals (list[str]), fragments (list[KnowledgeFragmentResponse])
- **Relationship**: signals are detected from the AnalyzedSession; fragments are the knowledge base sections relevant to those signals
