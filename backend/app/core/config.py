"""Application settings via Pydantic Settings."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    development = "development"
    staging = "staging"
    production = "production"


class ProviderName(StrEnum):
    mock = "mock"
    api_football = "api_football"
    sportmonks = "sportmonks"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────
    app_env: AppEnv = AppEnv.development
    app_name: str = "MyTeams API"
    api_v1_prefix: str = "/v1"
    log_level: str = "INFO"

    # ── Security ─────────────────────────────────────────────────
    secret_key: str = Field(default="CHANGE_ME_IN_PRODUCTION_openssl_rand_hex_32")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── Database ─────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://myteams:myteams_secret@localhost:5432/myteams"
    )

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl_seconds: int = 300  # 5 minutes default cache TTL

    # ── Provider ─────────────────────────────────────────────────
    provider_name: ProviderName = ProviderName.mock
    provider_api_key: str = ""
    provider_base_url: str = ""

    # ── Pagination defaults ──────────────────────────────────────
    default_page_size: int = 20
    max_page_size: int = 100

    @field_validator("provider_name", mode="before")
    @classmethod
    def resolve_provider(cls, v: str, info: object) -> str:  # noqa: ANN001
        """Fall back to mock when no API key is provided."""
        return v

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnv.development

    @property
    def effective_provider(self) -> ProviderName:
        """Use mock if no API key is set, regardless of provider_name."""
        if not self.provider_api_key and self.provider_name != ProviderName.mock:
            return ProviderName.mock
        return self.provider_name


@lru_cache
def get_settings() -> Settings:
    return Settings()
