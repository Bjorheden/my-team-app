"""API-Football adapter (https://www.api-football.com/)."""

from __future__ import annotations

from datetime import datetime

import httpx

from app.services.provider import (
    FootballProvider,
    ProviderEvent,
    ProviderFixture,
    ProviderLeague,
    ProviderStanding,
    ProviderTeam,
)


class ApiFootballProvider(FootballProvider):
    """Adapter for API-Football v3 (RapidAPI / direct)."""

    def __init__(self, api_key: str, base_url: str = "https://v3.football.api-sports.io") -> None:
        self._base = base_url.rstrip("/")
        self._headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": api_key,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=self._headers, timeout=15.0)

    async def get_leagues(self, country: str | None = None, season: str | None = None) -> list[ProviderLeague]:
        params: dict[str, str] = {}
        if country:
            params["country"] = country
        if season:
            params["season"] = season
        async with self._client() as client:
            r = await client.get(f"{self._base}/leagues", params=params)
            r.raise_for_status()
        return [
            ProviderLeague(
                provider_id=str(item["league"]["id"]),
                name=item["league"]["name"],
                country=item["country"]["name"],
                season=str(item["seasons"][-1]["year"]) if item.get("seasons") else (season or ""),
                logo_url=item["league"].get("logo"),
            )
            for item in r.json().get("response", [])
        ]

    async def get_teams(self, league_provider_id: str) -> list[ProviderTeam]:
        async with self._client() as client:
            r = await client.get(f"{self._base}/teams", params={"league": league_provider_id})
            r.raise_for_status()
        return [
            ProviderTeam(
                provider_id=str(item["team"]["id"]),
                name=item["team"]["name"],
                short_name=item["team"].get("code"),
                country=item["team"].get("country"),
                logo_url=item["team"].get("logo"),
                league_provider_id=league_provider_id,
            )
            for item in r.json().get("response", [])
        ]

    async def search_teams(self, query: str, limit: int = 10) -> list[ProviderTeam]:
        async with self._client() as client:
            r = await client.get(f"{self._base}/teams", params={"search": query})
            r.raise_for_status()
        return [
            ProviderTeam(
                provider_id=str(item["team"]["id"]),
                name=item["team"]["name"],
                short_name=item["team"].get("code"),
                country=item["team"].get("country"),
                logo_url=item["team"].get("logo"),
            )
            for item in r.json().get("response", [])[:limit]
        ]

    async def get_fixtures(
        self, team_provider_id: str, from_date: datetime, to_date: datetime
    ) -> list[ProviderFixture]:
        params = {
            "team": team_provider_id,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        }
        async with self._client() as client:
            r = await client.get(f"{self._base}/fixtures", params=params)
            r.raise_for_status()
        results = []
        for item in r.json().get("response", []):
            f = item["fixture"]
            goals = item.get("goals", {})
            results.append(
                ProviderFixture(
                    provider_id=str(f["id"]),
                    league_provider_id=str(item["league"]["id"]),
                    season=str(item["league"]["season"]),
                    home_team_provider_id=str(item["teams"]["home"]["id"]),
                    away_team_provider_id=str(item["teams"]["away"]["id"]),
                    start_time=datetime.fromisoformat(f["date"]),
                    status=f["status"]["short"],
                    home_score=goals.get("home"),
                    away_score=goals.get("away"),
                )
            )
        return results

    async def get_events(self, fixture_provider_id: str) -> list[ProviderEvent]:
        async with self._client() as client:
            r = await client.get(f"{self._base}/fixtures/events", params={"fixture": fixture_provider_id})
            r.raise_for_status()
        results = []
        for item in r.json().get("response", []):
            results.append(
                ProviderEvent(
                    fixture_provider_id=fixture_provider_id,
                    type=item["type"].lower(),
                    minute=item["time"].get("elapsed"),
                    team_provider_id=str(item["team"]["id"]) if item.get("team") else None,
                    player_name=item["player"].get("name") if item.get("player") else None,
                    payload={"detail": item.get("detail"), "comments": item.get("comments")},
                )
            )
        return results

    async def get_standings(self, league_provider_id: str, season: str) -> list[ProviderStanding]:
        params = {"league": league_provider_id, "season": season}
        async with self._client() as client:
            r = await client.get(f"{self._base}/standings", params=params)
            r.raise_for_status()
        results = []
        for group in r.json().get("response", []):
            for league_obj in group.get("league", {}).get("standings", []):
                for entry in league_obj:
                    all_stats = entry.get("all", {})
                    goals = all_stats.get("goals", {})
                    results.append(
                        ProviderStanding(
                            league_provider_id=league_provider_id,
                            season=season,
                            team_provider_id=str(entry["team"]["id"]),
                            rank=entry["rank"],
                            played=all_stats.get("played", 0),
                            wins=all_stats.get("win", 0),
                            draws=all_stats.get("draw", 0),
                            losses=all_stats.get("lose", 0),
                            goals_for=goals.get("for", 0),
                            goals_against=goals.get("against", 0),
                            goal_diff=entry.get("goalsDiff", 0),
                            points=entry.get("points", 0),
                        )
                    )
        return results
