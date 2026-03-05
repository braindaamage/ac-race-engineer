# API Contracts: Config Endpoints

**Feature**: 016-onboarding-settings | **Date**: 2026-03-05

## Existing Endpoints (modified)

### GET /config

Returns current configuration including new fields.

**Response** (200):
```json
{
  "ac_install_path": "C:\\Program Files\\Steam\\steamapps\\common\\assettocorsa",
  "setups_path": "C:\\Program Files\\Steam\\steamapps\\common\\assettocorsa\\setups",
  "llm_provider": "anthropic",
  "llm_model": "",
  "ui_theme": "dark",
  "api_key": "sk-a...****",
  "onboarding_completed": true
}
```

**Notes**:
- `api_key` is masked in the response (first 4 + last 4 chars visible, rest replaced with `****`). Returns empty string if not set.
- `onboarding_completed` is the primary field the frontend uses to decide wizard vs. main app.

### PATCH /config

Partial update — only provided fields are changed. Now accepts `api_key` and `onboarding_completed`.

**Request body** (all fields optional):
```json
{
  "ac_install_path": "C:\\Games\\assettocorsa",
  "setups_path": "C:\\Games\\assettocorsa\\setups",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "ui_theme": "light",
  "api_key": "sk-proj-abc123...",
  "onboarding_completed": true
}
```

**Response** (200): Same shape as GET /config (with masked api_key).

**Errors**:
- 422: Invalid `llm_provider`, `ui_theme`, or field type mismatch.

### GET /config/validate

Enhanced to return detailed per-field validation results instead of flat booleans.

**Response** (200):
```json
{
  "ac_path": {
    "status": "valid",
    "message": "Valid Assetto Corsa installation found."
  },
  "setups_path": {
    "status": "warning",
    "message": "Folder not found at this location."
  },
  "llm_provider": {
    "status": "valid",
    "message": "Provider 'anthropic' is supported."
  },
  "onboarding_completed": false,
  "is_valid": false
}
```

**Status values for path fields**: `"valid"`, `"warning"`, `"not_found"`, `"empty"`

**Breaking change**: Response shape changes from flat booleans to nested objects. Existing consumers (if any) must be updated.

## New Endpoints

### POST /config/validate-path

Validates a filesystem path without saving it to config. Used by the wizard to validate paths before the user finishes.

**Request body**:
```json
{
  "path": "C:\\Program Files\\Steam\\steamapps\\common\\assettocorsa",
  "path_type": "ac_install"
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| path | string | yes | Filesystem path to validate |
| path_type | string | yes | `"ac_install"` or `"setups"` |

**Response** (200):
```json
{
  "status": "valid",
  "message": "Valid Assetto Corsa installation found."
}
```

**Validation rules for `ac_install`**:

| Condition | Status | Message |
|-----------|--------|---------|
| Path is empty | empty | "Please provide the path to your Assetto Corsa installation." |
| Path does not exist | not_found | "Folder not found at this location." |
| Path exists, no `content/` | warning | "This folder doesn't appear to contain Assetto Corsa. Expected to find a 'content' subfolder." |
| Has `content/` but missing `content/cars/` | warning | "Found 'content' folder but 'content/cars' is missing. This may not be a complete AC installation." |
| Has `content/cars/` and `content/tracks/` | valid | "Valid Assetto Corsa installation found." |

**Validation rules for `setups`**:

| Condition | Status | Message |
|-----------|--------|---------|
| Path is empty | empty | "Please provide the path to your setup files." |
| Path does not exist | not_found | "Folder not found at this location." |
| Path exists and is a directory | valid | "Setups folder found." |

### POST /config/validate-api-key

Tests an API key by making a minimal request to the selected provider.

**Request body**:
```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-api03-..."
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| provider | string | yes | `"anthropic"`, `"openai"`, or `"gemini"` |
| api_key | string | yes | The API key to test |

**Response** (200):
```json
{
  "valid": true,
  "message": "API key is valid. Connected to Anthropic successfully."
}
```

**Error responses** (all return 200 with `valid: false` — not HTTP errors):

| Condition | valid | Message |
|-----------|-------|---------|
| Key accepted | true | "API key is valid. Connected to {Provider} successfully." |
| HTTP 401/403 from provider | false | "Invalid API key. Please check the key and try again." |
| Network timeout (10s) | false | "Could not reach {Provider}. Check your internet connection." |
| Connection refused | false | "Could not reach {Provider}. Check your internet connection." |
| HTTP 429 | false | "Rate limited by {Provider}. The key appears valid — try again in a moment." |
| Other HTTP error | false | "Unexpected error from {Provider} (HTTP {code}). The key may still be valid." |
| Invalid provider | false | "Unknown provider '{provider}'. Must be anthropic, openai, or gemini." |

**Timeout**: 10 seconds per provider request.

**Note**: This endpoint does NOT save the API key — it only tests it. The key is saved separately via PATCH /config.
