# Contract: Config Module Public API

**Module**: `ac_engineer.config`
**Exports** (`__all__`): `ACConfig`, `read_config`, `write_config`, `update_config`, `get_effective_model`, `LLM_MODEL_DEFAULTS`

## ACConfig

Pydantic v2 `BaseModel` representing user configuration.

```python
class ACConfig(BaseModel):
    ac_install_path: Path | None = None
    setups_path: Path | None = None
    llm_provider: str = "anthropic"
    llm_model: str | None = None

    # Computed properties (not stored in JSON)
    ac_cars_path: Path | None     # ac_install_path / "content" / "cars" (None if ac_install_path is None)
    ac_tracks_path: Path | None   # ac_install_path / "content" / "tracks" (None if ac_install_path is None)
    is_ac_configured: bool        # True if ac_install_path is set AND is an existing directory
    is_setups_configured: bool    # True if setups_path is set AND is an existing directory
```

- Path fields (`ac_install_path`, `setups_path`) are `Path | None`. Serialized as strings in JSON.
- `llm_provider` defaults to `"anthropic"`. Validated against allowed values: `"anthropic"`, `"openai"`, `"gemini"` — raises `ValueError` otherwise.
- `llm_model` is optional with `None` default. Use `get_effective_model()` to resolve the effective model.
- Validates non-empty strings: a field set to `""` is treated as `None`.
- Computed properties are derived at access time, not persisted.
- Serializes to/from flat JSON via Pydantic's `.model_dump_json()` / `.model_validate_json()`.

## read_config

```python
def read_config(path: str | Path) -> ACConfig:
```

Read configuration from a JSON file. **Never raises** — returns `ACConfig()` with defaults on any error (missing file, invalid JSON, wrong types).

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| path | str \| Path | Path to config.json |
| **Returns** | ACConfig | Validated config, with defaults substituted for invalid/missing fields |

**Error handling**: All exceptions caught internally. Logs a warning on parse errors. Returns default `ACConfig()`.

## write_config

```python
def write_config(path: str | Path, config: ACConfig) -> None:
```

Write a complete configuration to file. **Atomic**: writes to `.tmp`, then `os.replace()`.

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| path | str \| Path | Path to config.json |
| config | ACConfig | Complete config to write |

**Error handling**: Raises `OSError` on filesystem failures (permission denied, disk full). Creates parent directories if they don't exist.

## update_config

```python
def update_config(path: str | Path, **kwargs: Any) -> ACConfig:
```

Partial update: reads current config, applies keyword overrides, writes back atomically. Returns the updated config.

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| path | str \| Path | Path to config.json |
| **kwargs | Any | Fields to update (e.g., `llm_provider="anthropic"`) |
| **Returns** | ACConfig | Updated config after write |

**Error handling**: Raises `ValueError` for unknown field names. Read errors fall back to defaults (same as `read_config`). Write errors propagate as `OSError`.

## get_effective_model

```python
def get_effective_model(config: ACConfig) -> str:
```

Returns the effective model name for the configured provider. If `config.llm_model` is set, returns it directly. Otherwise, returns the provider's default from `LLM_MODEL_DEFAULTS`.

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| config | ACConfig | Configuration to resolve model for |
| **Returns** | str | Effective model name |

**Constants**:

```python
LLM_MODEL_DEFAULTS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-5",
    "openai": "gpt-4o",
    "gemini": "gemini-1.5-pro",
}
```
