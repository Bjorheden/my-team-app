"""Football data provider interface + adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProviderLeague:
    provider_id: str
    name: str
    country: str
    season: str
    logo_url: str | None = None


@dataclass
class ProviderTeam:
    provider_id: str
    name: str
    short_name: str | None = None
    country: str | None = None
    logo_url: str | None = None
    league_provider_id: str | None = None


@dataclass
class ProviderFixture:
    provider_id: str
    league_provider_id: str
    season: str
    home_team_provider_id: str
    away_team_provider_id: str
    start_time: datetime
    status: str = "NS"
    home_score: int | None = None
    away_score: int | None = None


@dataclass
class ProviderEvent:
    fixture_provider_id: str
    type: str
    minute: int | None = None
    team_provider_id: str | None = None
    player_name: str | None = None
    payload: dict = field(default_factory=dict)


@dataclass
class ProviderStanding:
    league_provider_id: str
    season: str
    team_provider_id: str
    rank: int
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_diff: int = 0
    points: int = 0


class FootballProvider(ABC):
    """Abstract interface for any football data provider."""

    @abstractmethod
    async def get_leagues(self, country: str | None = None, season: str | None = None) -> list[ProviderLeague]: ...

    @abstractmethod
    async def get_teams(self, league_provider_id: str) -> list[ProviderTeam]: ...

    @abstractmethod
    async def search_teams(self, query: str, limit: int = 10) -> list[ProviderTeam]: ...

    @abstractmethod
    async def get_fixtures(
        self, team_provider_id: str, from_date: datetime, to_date: datetime
    ) -> list[ProviderFixture]: ...

    @abstractmethod
    async def get_events(self, fixture_provider_id: str) -> list[ProviderEvent]: ...

    @abstractmethod
    async def get_standings(self, league_provider_id: str, season: str) -> list[ProviderStanding]: ...
