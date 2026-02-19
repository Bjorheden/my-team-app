"""Provider factory + FastAPI dependency."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import ProviderName, get_settings
from app.services.api_football import ApiFootballProvider
from app.services.mock_provider import MockProvider
from app.services.provider import FootballProvider


@lru_cache(maxsize=1)
def get_provider() -> FootballProvider:
    settings = get_settings()
    effective = settings.effective_provider
    if effective == ProviderName.api_football:
        return ApiFootballProvider(
            api_key=settings.provider_api_key,
            base_url=settings.provider_base_url or "https://v3.football.api-sports.io",
        )
    # mock (default) or any unimplemented provider
    return MockProvider()
