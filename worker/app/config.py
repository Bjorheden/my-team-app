"""Worker settings – thin wrapper around the shared config approach."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://myteams:myteams_secret@localhost:5432/myteams"
    redis_url: str = "redis://localhost:6379/0"
    app_env: str = "development"
    log_level: str = "INFO"

    # How often the periodic sync loop runs (seconds)
    worker_sync_interval_seconds: int = 300

    # Provider config
    provider_name: str = "mock"
    provider_api_key: str = ""
    provider_base_url: str = ""

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
