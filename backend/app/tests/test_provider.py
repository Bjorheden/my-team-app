"""Tests for MockProvider."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_get_leagues_returns_all(mock_provider: MockProvider) -> None:
    leagues = await mock_provider.get_leagues()
    assert len(leagues) >= 2


@pytest.mark.asyncio
async def test_get_leagues_filter_by_country(mock_provider: MockProvider) -> None:
    leagues = await mock_provider.get_leagues(country="England")
    assert all(lg.country == "England" for lg in leagues)


@pytest.mark.asyncio
async def test_search_teams_case_insensitive(mock_provider: MockProvider) -> None:
    results = await mock_provider.search_teams("manchester")
    assert any("Manchester" in t.name for t in results)


@pytest.mark.asyncio
async def test_search_teams_no_results(mock_provider: MockProvider) -> None:
    results = await mock_provider.search_teams("zzznoteam")
    assert results == []


@pytest.mark.asyncio
async def test_get_teams_for_league(mock_provider: MockProvider) -> None:
    teams = await mock_provider.get_teams("mock-39")
    assert len(teams) == 3  # PL teams in mock data


@pytest.mark.asyncio
async def test_get_fixtures_date_range(mock_provider: MockProvider) -> None:
    now = datetime.now(UTC)
    fixtures = await mock_provider.get_fixtures(
        "mock-50",
        from_date=now - timedelta(days=7),
        to_date=now + timedelta(days=14),
    )
    assert isinstance(fixtures, list)


@pytest.mark.asyncio
async def test_get_events_for_finished_fixture(mock_provider: MockProvider) -> None:
    events = await mock_provider.get_events("mock-fix-1001")
    assert len(events) == 3
    assert all(e.type == "goal" for e in events)


@pytest.mark.asyncio
async def test_get_standings(mock_provider: MockProvider) -> None:
    standings = await mock_provider.get_standings("mock-39", "2024")
    assert len(standings) == 3
    assert standings[0].rank == 1
