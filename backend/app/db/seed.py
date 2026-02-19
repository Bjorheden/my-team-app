"""
Seed script – loads deterministic sample data for local development.
Only inserts rows that don't already exist (idempotent).

Usage (inside Docker):
    python -m app.db.seed
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.logging import configure_logging, get_logger
from app.db.models import Fixture, League, Standing, Team
from app.db.session import AsyncSessionLocal

configure_logging()
log = get_logger("seed")

# ── Seed data ─────────────────────────────────────────────────────────────────

LEAGUES = [
    {
        "id": "league-pl",
        "provider_league_id": "mock-39",
        "name": "Premier League",
        "country": "England",
        "season": "2024",
        "logo_url": "https://media.api-sports.io/football/leagues/39.png",
    },
    {
        "id": "league-ll",
        "provider_league_id": "mock-140",
        "name": "La Liga",
        "country": "Spain",
        "season": "2024",
        "logo_url": "https://media.api-sports.io/football/leagues/140.png",
    },
]

TEAMS = [
    {
        "id": "team-mci",
        "provider_team_id": "mock-50",
        "name": "Manchester City",
        "short_name": "MCI",
        "league_id": "league-pl",
        "country": "England",
        "logo_url": "https://media.api-sports.io/football/teams/50.png",
    },
    {
        "id": "team-liv",
        "provider_team_id": "mock-40",
        "name": "Liverpool",
        "short_name": "LIV",
        "league_id": "league-pl",
        "country": "England",
        "logo_url": "https://media.api-sports.io/football/teams/40.png",
    },
    {
        "id": "team-ars",
        "provider_team_id": "mock-42",
        "name": "Arsenal",
        "short_name": "ARS",
        "league_id": "league-pl",
        "country": "England",
        "logo_url": "https://media.api-sports.io/football/teams/42.png",
    },
    {
        "id": "team-rma",
        "provider_team_id": "mock-541",
        "name": "Real Madrid",
        "short_name": "RMA",
        "league_id": "league-ll",
        "country": "Spain",
        "logo_url": "https://media.api-sports.io/football/teams/541.png",
    },
    {
        "id": "team-bar",
        "provider_team_id": "mock-529",
        "name": "FC Barcelona",
        "short_name": "BAR",
        "league_id": "league-ll",
        "country": "Spain",
        "logo_url": "https://media.api-sports.io/football/teams/529.png",
    },
    {
        "id": "team-atm",
        "provider_team_id": "mock-530",
        "name": "Atletico Madrid",
        "short_name": "ATM",
        "league_id": "league-ll",
        "country": "Spain",
        "logo_url": "https://media.api-sports.io/football/teams/530.png",
    },
]

_now = datetime.now(UTC)
_yesterday = _now - timedelta(days=1)
_tomorrow = _now + timedelta(days=1)
_next_week = _now + timedelta(days=7)

FIXTURES = [
    {
        "id": "fix-1",
        "provider_fixture_id": "mock-fix-1001",
        "league_id": "league-pl",
        "season": "2024",
        "home_team_id": "team-mci",
        "away_team_id": "team-liv",
        "start_time": _yesterday.replace(hour=15, minute=0, second=0, microsecond=0),
        "status": "FT",
        "home_score": 2,
        "away_score": 1,
        "updated_at": _now,
    },
    {
        "id": "fix-2",
        "provider_fixture_id": "mock-fix-1002",
        "league_id": "league-pl",
        "season": "2024",
        "home_team_id": "team-ars",
        "away_team_id": "team-mci",
        "start_time": _tomorrow.replace(hour=17, minute=30, second=0, microsecond=0),
        "status": "NS",
        "home_score": None,
        "away_score": None,
        "updated_at": _now,
    },
    {
        "id": "fix-3",
        "provider_fixture_id": "mock-fix-1003",
        "league_id": "league-ll",
        "season": "2024",
        "home_team_id": "team-rma",
        "away_team_id": "team-bar",
        "start_time": _next_week.replace(hour=21, minute=0, second=0, microsecond=0),
        "status": "NS",
        "home_score": None,
        "away_score": None,
        "updated_at": _now,
    },
]

STANDINGS_PL = [
    {"rank": 1, "team_id": "team-mci", "played": 28, "wins": 20, "draws": 4, "losses": 4, "goals_for": 65, "goals_against": 28, "goal_diff": 37, "points": 64},
    {"rank": 2, "team_id": "team-liv", "played": 28, "wins": 19, "draws": 5, "losses": 4, "goals_for": 60, "goals_against": 30, "goal_diff": 30, "points": 62},
    {"rank": 3, "team_id": "team-ars", "played": 28, "wins": 18, "draws": 4, "losses": 6, "goals_for": 55, "goals_against": 32, "goal_diff": 23, "points": 58},
]

STANDINGS_LL = [
    {"rank": 1, "team_id": "team-rma", "played": 27, "wins": 21, "draws": 3, "losses": 3, "goals_for": 70, "goals_against": 25, "goal_diff": 45, "points": 66},
    {"rank": 2, "team_id": "team-bar", "played": 27, "wins": 18, "draws": 4, "losses": 5, "goals_for": 58, "goals_against": 32, "goal_diff": 26, "points": 58},
    {"rank": 3, "team_id": "team-atm", "played": 27, "wins": 16, "draws": 5, "losses": 6, "goals_for": 48, "goals_against": 28, "goal_diff": 20, "points": 53},
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # ── Leagues ──────────────────────────────────────────────
        for league_data in LEAGUES:
            stmt = pg_insert(League).values(**league_data).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # ── Teams ────────────────────────────────────────────────
        for team_data in TEAMS:
            stmt = pg_insert(Team).values(**team_data).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # ── Fixtures ─────────────────────────────────────────────
        for fix_data in FIXTURES:
            stmt = pg_insert(Fixture).values(**fix_data).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # ── Standings ─────────────────────────────────────────────
        for row in STANDINGS_PL:
            stmt = pg_insert(Standing).values(league_id="league-pl", season="2024", **row).on_conflict_do_update(
                index_elements=["league_id", "season", "team_id"],
                set_={k: row[k] for k in row if k != "team_id"},
            )
            await session.execute(stmt)

        for row in STANDINGS_LL:
            stmt = pg_insert(Standing).values(league_id="league-ll", season="2024", **row).on_conflict_do_update(
                index_elements=["league_id", "season", "team_id"],
                set_={k: row[k] for k in row if k != "team_id"},
            )
            await session.execute(stmt)

        await session.commit()
        log.info("Seed complete", leagues=len(LEAGUES), teams=len(TEAMS), fixtures=len(FIXTURES))


if __name__ == "__main__":
    asyncio.run(seed())
