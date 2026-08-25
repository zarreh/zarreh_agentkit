"""Typed application settings, sourced from the environment.

Both consuming services arrived at the identical shape: a `pydantic-settings`
`BaseSettings` subclass with `env_prefix`, secrets read from env only, and a
cached `get_settings()` factory. This module carries the shared base so each
service subclasses it, sets its own `env_prefix`, and adds app-specific fields.

Usage::

    class Settings(AgentSettings):
        model_config = SettingsConfigDict(env_prefix="MYAPP_", extra="ignore")
        my_field: str = "default"

    @lru_cache
    def get_settings() -> Settings:
        return Settings()
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Fields every agent service shares.

    Secrets are sourced from the environment only — never hard-coded. Subclass
    and override `model_config` to set the service's own `env_prefix`; add
    app-specific fields on the subclass.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    openai_api_key: str = ""

    langsmith_api_key: str = ""
    langsmith_project: str = "agent-service"

    data_dir: str = "data"
    run_store_path: str = "data/runs.db"

    rate_limit_per_minute: int = 20
    max_request_body_bytes: int = 16_384
