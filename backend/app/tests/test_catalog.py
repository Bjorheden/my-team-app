"""Tests for catalog endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import League, Team


async def _seed_league_and_team(db: AsyncSession) -> tuple[League, Team]:
    from datetime import UTC, datetime

    league = League(
        id="test-league-1",
        provider_league_id="test-prov-lg-1",
        name="Test League",
        country="Testland",
        season="2024",
    )
    db.add(league)
    team = Team(
        id="test-team-1",
        provider_team_id="test-prov-t-1",
        name="Test United",
        short_name="TU",
        league_id="test-league-1",
        country="Testland",
    )
    db.add(team)
    await db.flush()
    return league, team


@pytest.mark.asyncio
async def test_search_teams_from_db(client: AsyncClient, db: AsyncSession) -> None:
    await _seed_league_and_team(db)
    response = await client.get("/v1/teams/search?q=Test")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(t["name"] == "Test United" for t in data["items"])


@pytest.mark.asyncio
async def test_search_teams_fallback_to_provider(client: AsyncClient) -> None:
    """When no DB match, mock provider returns results."""
    response = await client.get("/v1/teams/search?q=Manchester")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_leagues(client: AsyncClient, db: AsyncSession) -> None:
    await _seed_league_and_team(db)
    response = await client.get("/v1/leagues")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_league_teams(client: AsyncClient, db: AsyncSession) -> None:
    await _seed_league_and_team(db)
    response = await client.get("/v1/leagues/test-league-1/teams")
    assert response.status_code == 200
    names = [t["name"] for t in response.json()]
    assert "Test United" in names
