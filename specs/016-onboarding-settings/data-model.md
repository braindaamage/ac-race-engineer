# Data Model: Onboarding Wizard & Settings

**Feature**: 016-onboarding-settings | **Date**: 2026-03-05

## Entity Changes

### ACConfig (modified)

The existing `ACConfig` Pydantic v2 model gains two new fields. No new entities are introduced.

| Field | Type | Default | Validation | Notes |
|-------|------|---------|------------|-------|
| ac_install_path | Path or None | None | Empty string → None | Existing |
| setups_path | Path or None | None | Empty string → None | Existing |
| llm_provider | str | "anthropic" | Must be in ("anthropic", "openai", "gemini") | Existing |
| llm_model | str or None | None | Empty string → None | Existing |
| ui_theme | str | "dark" | Must be in ("dark", "light") | Existing |
| **api_key** | **str or None** | **None** | **Empty string → None** | **NEW** |
| **onboarding_completed** | **bool** | **False** | **Must be boolean** | **NEW** |

**Serialization**: `api_key` serializes as `null` when None (not empty string). `onboarding_completed` serializes as `false`/`true`.

**Computed properties** (unchanged):
- `ac_cars_path`: `ac_install_path / "content" / "cars"` (or None)
- `ac_tracks_path`: `ac_install_path / "content" / "tracks"` (or None)
- `is_ac_configured`: `ac_install_path is not None and ac_install_path.is_dir()`
- `is_setups_configured`: `setups_path is not None and setups_path.is_dir()`

### PathValidationResult (new response model, API only)

Returned by the enhanced validation and new path validation endpoints.

| Field | Type | Description |
|-------|------|-------------|
| status | str | One of: "valid", "warning", "not_found", "empty" |
| message | str | Human-readable explanation of the validation result |

### ConnectionTestResult (new response model, API only)

Returned by the API key test endpoint.

| Field | Type | Description |
|-------|------|-------------|
| valid | bool | Whether the key was accepted by the provider |
| message | str | Human-readable result ("Key is valid", "Invalid API key", "Network error", etc.) |

### ConfigResponse (modified)

The existing `ConfigResponse` API model gains fields for the new ACConfig fields.

| Field | Type | Notes |
|-------|------|-------|
| ac_install_path | str | Existing (empty string if None) |
| setups_path | str | Existing (empty string if None) |
| llm_provider | str | Existing |
| llm_model | str | Existing (empty string if None) |
| ui_theme | str | Existing |
| **api_key** | **str** | **NEW — empty string if None (never expose raw key; masked in response)** |
| **onboarding_completed** | **bool** | **NEW** |

**Note on api_key in responses**: The `GET /config` response returns `api_key` as a masked string (e.g., `"sk-...****"` showing first 4 and last 4 characters) or empty string if not set. The raw key is never returned in API responses after being saved. For the wizard flow, the key is held in local state and sent via PATCH — the response confirms it was saved without echoing it back.

### ConfigValidationResponse (modified)

The existing flat-boolean response is replaced with detailed per-field results.

| Field | Type | Notes |
|-------|------|-------|
| ac_path | PathValidationResult | Detailed AC path validation |
| setups_path | PathValidationResult | Detailed setups path validation |
| llm_provider | PathValidationResult | Provider validity check |
| onboarding_completed | bool | Current onboarding state |
| is_valid | bool | Overall validity (ac_path valid AND setups_path valid) |

## State Transitions

### Onboarding Flow

```
[App Launch]
    │
    ▼
[GET /config] ──→ onboarding_completed: true ──→ [AppShell / Sessions View]
    │
    ▼
onboarding_completed: false
    │
    ▼
[Wizard Step 1: AC Path]
    │ ← POST /config/validate-path (on input change, debounced)
    ▼
[Wizard Step 2: Setups Path]
    │ ← POST /config/validate-path (on input change, debounced)
    ▼
[Wizard Step 3: AI Provider] (skippable)
    │ ← POST /config/validate-api-key (on "Test Connection" click)
    ▼
[Wizard Step 4: Review]
    │
    ▼
[PATCH /config] ──→ all fields + onboarding_completed: true
    │
    ▼
[AppShell / Sessions View]
```

### Settings Save Flow

```
[Settings Screen]
    │
    ▼
[GET /config] ──→ populate form fields
    │
    ▼
[User edits fields]
    │ ← POST /config/validate-path (debounced, for path fields)
    │ ← POST /config/validate-api-key (on "Test Connection" click)
    ▼
[User clicks "Save"]
    │
    ▼
[PATCH /config] ──→ updated fields only
    │
    ▼
[Success toast notification]
```

## Migration / Backwards Compatibility

- **Existing config.json files** (from Phase 7.1 or earlier): Missing `api_key` and `onboarding_completed` fields are handled by Pydantic defaults (`None` and `False` respectively). No migration script needed.
- **Existing backend tests**: The `ConfigResponse` model change (new fields) may require updating test assertions that check response shape. The `ConfigValidationResponse` structural change (flat booleans → nested objects) will break existing validation tests — these must be updated.
- **Existing frontend**: The `GET /config` response gains new fields — existing code that destructures the response will not break (extra fields are ignored). The SettingsView is completely replaced.
