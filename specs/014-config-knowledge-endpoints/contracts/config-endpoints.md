# API Contract: Config Endpoints

**Prefix**: `/config`

---

## GET /config

Retrieve the current user configuration.

**Response** `200 OK`:
```json
{
  "ac_install_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa",
  "setups_path": "C:\\Users\\user\\Documents\\Assetto Corsa\\setups",
  "llm_provider": "anthropic",
  "llm_model": ""
}
```

**Field rules**:
- All fields are strings, never null
- Unset paths are returned as `""`
- Unset llm_model is returned as `""`
- llm_provider defaults to `"anthropic"` if config file is missing

---

## PATCH /config

Partially update user configuration. Only provided fields are modified.

**Request body** (all fields optional):
```json
{
  "llm_provider": "openai",
  "llm_model": "gpt-4o"
}
```

**Response** `200 OK` — returns the full updated config (same shape as GET /config):
```json
{
  "ac_install_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa",
  "setups_path": "C:\\Users\\user\\Documents\\Assetto Corsa\\setups",
  "llm_provider": "openai",
  "llm_model": "gpt-4o"
}
```

**Error** `422 Unprocessable Entity` — invalid llm_provider or unknown fields:
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "llm_provider must be one of ('anthropic', 'openai', 'gemini'), got 'bedrock'"
    }
  ]
}
```

**Behavior**:
- Empty body `{}` is valid — returns current config unchanged
- Unknown fields are rejected (extra="forbid")
- Invalid llm_provider is rejected before persisting
- Omitted fields retain their current values

---

## GET /config/validate

Check whether the current configuration is valid for running the engineer.

**Response** `200 OK`:
```json
{
  "ac_path_valid": true,
  "setups_path_valid": true,
  "llm_provider_valid": true,
  "is_valid": true
}
```

**Example with failures**:
```json
{
  "ac_path_valid": false,
  "setups_path_valid": true,
  "llm_provider_valid": true,
  "is_valid": false
}
```

**Validation rules**:
- `ac_path_valid`: ac_install_path is non-empty AND the directory exists on disk
- `setups_path_valid`: setups_path is non-empty AND the directory exists on disk
- `llm_provider_valid`: llm_provider is non-empty and in the allowed list
- `is_valid`: all three above are true
