"""MockProvider – deterministic sample data for local development and testing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import ClassVar

from app.services.provider import (
    FootballProvider,
    ProviderEvent,
    ProviderFixture,
    ProviderLeague,
    ProviderStanding,
    ProviderTeam,
)

_NOW = datetime.now(UTC)


class MockProvider(FootballProvider):
    """Returns hard-coded sample data. Used when no real API key is configured."""

    LEAGUES: ClassVar[list[ProviderLeague]] = [
        ProviderLeague("mock-39", "Premier League", "England", "2024", None),
        ProviderLeague("mock-140", "La Liga", "Spain", "2024", None),
    ]

    TEAMS: ClassVar[list[ProviderTeam]] = [
        ProviderTeam("mock-50", "Manchester City", "MCI", "England", None, "mock-39"),
        ProviderTeam("mock-40", "Liverpool", "LIV", "England", None, "mock-39"),
        ProviderTeam("mock-42", "Arsenal", "ARS", "England", None, "mock-39"),
        ProviderTeam("mock-541", "Real Madrid", "RMA", "Spain", None, "mock-140"),
        ProviderTeam("mock-529", "FC Barcelona", "BAR", "Spain", None, "mock-140"),
        ProviderTeam("mock-530", "Atletico Madrid", "ATM", "Spain", None, "mock-140"),
    ]

    def _fixtures_for_team(self, team_id: str) -> list[ProviderFixture]:
        yesterday = (_NOW - timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
        tomorrow = (_NOW + timedelta(days=1)).replace(hour=17, minute=30, second=0, microsecond=0)
        next_week = (_NOW + timedelta(days=7)).replace(hour=21, minute=0, second=0, microsecond=0)

        all_fixtures = [
            ProviderFixture("mock-fix-1001", "mock-39", "2024", "mock-50", "mock-40", yesterday, "FT", 2, 1),
            ProviderFixture("mock-fix-1002", "mock-39", "2024", "mock-42", "mock-50", tomorrow, "NS"),
            ProviderFixture("mock-fix-1003", "mock-140", "2024", "mock-541", "mock-529", next_week, "NS"),
        ]
        return [
            f for f in all_fixtures
            if f.home_team_provider_id == team_id or f.away_team_provider_id == team_id
        ]

    async def get_leagues(self, country: str | None = None, season: str | None = None) -> list[ProviderLeague]:
        leagues = self.LEAGUES
        if country:
            leagues = [lg for lg in leagues if lg.country.lower() == country.lower()]
        if season:
            leagues = [lg for lg in leagues if lg.season == season]
        return leagues

    async def get_teams(self, league_provider_id: str) -> list[ProviderTeam]:
        return [t for t in self.TEAMS if t.league_provider_id == league_provider_id]

    async def search_teams(self, query: str, limit: int = 10) -> list[ProviderTeam]:
        q = query.lower()
        results = [t for t in self.TEAMS if q in t.name.lower()]
        return results[:limit]

    async def get_fixtures(
        self, team_provider_id: str, from_date: datetime, to_date: datetime
    ) -> list[ProviderFixture]:
        return [
            f for f in self._fixtures_for_team(team_provider_id)
            if from_date <= f.start_time <= to_date
        ]

    async def get_events(self, fixture_provider_id: str) -> list[ProviderEvent]:
        if fixture_provider_id == "mock-fix-1001":
            return [
                ProviderEvent("mock-fix-1001", "goal", 24, "mock-50", "Haaland"),
                ProviderEvent("mock-fix-1001", "goal", 58, "mock-50", "De Bruyne"),
                ProviderEvent("mock-fix-1001", "goal", 71, "mock-40", "Salah"),
            ]
        return []

    async def get_standings(self, league_provider_id: str, season: str) -> list[ProviderStanding]:
        if league_provider_id == "mock-39":
            return [
                ProviderStanding("mock-39", season, "mock-50", 1, 28, 20, 4, 4, 65, 28, 37, 64),
                ProviderStanding("mock-39", season, "mock-40", 2, 28, 19, 5, 4, 60, 30, 30, 62),
                ProviderStanding("mock-39", season, "mock-42", 3, 28, 18, 4, 6, 55, 32, 23, 58),
            ]
        if league_provider_id == "mock-140":
            return [
                ProviderStanding("mock-140", season, "mock-541", 1, 27, 21, 3, 3, 70, 25, 45, 66),
                ProviderStanding("mock-140", season, "mock-529", 2, 27, 18, 4, 5, 58, 32, 26, 58),
                ProviderStanding("mock-140", season, "mock-530", 3, 27, 16, 5, 6, 48, 28, 20, 53),
            ]
        return []
