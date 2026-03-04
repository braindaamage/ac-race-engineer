"""ACConfig Pydantic v2 model."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, field_validator, model_serializer


VALID_LLM_PROVIDERS = ("anthropic", "openai", "gemini")


class ACConfig(BaseModel):
    """User configuration for AC Race Engineer."""

    ac_install_path: Path | None = None
    setups_path: Path | None = None
    llm_provider: str = "anthropic"
    llm_model: str | None = None

    @field_validator("ac_install_path", "setups_path", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("llm_model", mode="before")
    @classmethod
    def _empty_model_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("llm_provider")
    @classmethod
    def _validate_provider(cls, v: str) -> str:
        if v not in VALID_LLM_PROVIDERS:
            raise ValueError(
                f"llm_provider must be one of {VALID_LLM_PROVIDERS}, got {v!r}"
            )
        return v

    @property
    def ac_cars_path(self) -> Path | None:
        if self.ac_install_path is None:
            return None
        return self.ac_install_path / "content" / "cars"

    @property
    def ac_tracks_path(self) -> Path | None:
        if self.ac_install_path is None:
            return None
        return self.ac_install_path / "content" / "tracks"

    @property
    def is_ac_configured(self) -> bool:
        return self.ac_install_path is not None and self.ac_install_path.is_dir()

    @property
    def is_setups_configured(self) -> bool:
        return self.setups_path is not None and self.setups_path.is_dir()

    @model_serializer
    def _serialize(self) -> dict[str, object]:
        return {
            "ac_install_path": str(self.ac_install_path) if self.ac_install_path else None,
            "setups_path": str(self.setups_path) if self.setups_path else None,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
        }
