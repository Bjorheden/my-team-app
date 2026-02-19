"""Sync service – pulls data from the provider and upserts into the DB."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Event, Fixture, League, Standing, Team
from app.services.provider import FootballProvider, ProviderFixture

log = get_logger("sync")


class SyncService:
    def __init__(self, provider: FootballProvider, session: AsyncSession) -> None:
        self.provider = provider
        self.session = session

    # ── Leagues ───────────────────────────────────────────────────────────────
    async def sync_leagues(self, country: str | None = None, season: str | None = None) -> int:
        provider_leagues = await self.provider.get_leagues(country=country, season=season)
        count = 0
        for pl in provider_leagues:
            existing = await self.session.execute(
                select(League).where(League.provider_league_id == pl.provider_id)
            )
            league = existing.scalar_one_or_none()
            if league is None:
                league = League(
                    id=str(uuid.uuid4()),
                    provider_league_id=pl.provider_id,
                    name=pl.name,
                    country=pl.country,
                    season=pl.season,
                    logo_url=pl.logo_url,
                )
                self.session.add(league)
                count += 1
            else:
                league.name = pl.name
                league.season = pl.season
        await self.session.flush()
        log.info("Synced leagues", count=count)
        return count

    # ── Teams ─────────────────────────────────────────────────────────────────
    async def sync_teams(self, league_provider_id: str) -> int:
        # Ensure league exists
        league_row = await self.session.execute(
            select(League).where(League.provider_league_id == league_provider_id)
        )
        league = league_row.scalar_one_or_none()

        provider_teams = await self.provider.get_teams(league_provider_id)
        count = 0
        for pt in provider_teams:
            existing = await self.session.execute(
                select(Team).where(Team.provider_team_id == pt.provider_id)
            )
            team = existing.scalar_one_or_none()
            if team is None:
                team = Team(
                    id=str(uuid.uuid4()),
                    provider_team_id=pt.provider_id,
                    name=pt.name,
                    short_name=pt.short_name,
                    league_id=league.id if league else None,
                    country=pt.country,
                    logo_url=pt.logo_url,
                )
                self.session.add(team)
                count += 1
            else:
                team.name = pt.name
                team.logo_url = pt.logo_url
        await self.session.flush()
        log.info("Synced teams", league=league_provider_id, count=count)
        return count

    # ── Fixtures ──────────────────────────────────────────────────────────────
    async def sync_fixtures(self, team_provider_id: str, hours_forward: int = 72) -> int:
        now = datetime.now(UTC)
        from_date = now - timedelta(hours=24)
        to_date = now + timedelta(hours=hours_forward)

        provider_fixtures = await self.provider.get_fixtures(team_provider_id, from_date, to_date)
        count = 0
        for pf in provider_fixtures:
            count += await self._upsert_fixture(pf)
        await self.session.flush()
        log.info("Synced fixtures", team=team_provider_id, count=count)
        return count

    async def _upsert_fixture(self, pf: ProviderFixture) -> int:
        # Resolve foreign keys
        league_row = await self.session.execute(
            select(League).where(League.provider_league_id == pf.league_provider_id)
        )
        league = league_row.scalar_one_or_none()
        home_row = await self.session.execute(
            select(Team).where(Team.provider_team_id == pf.home_team_provider_id)
        )
        away_row = await self.session.execute(
            select(Team).where(Team.provider_team_id == pf.away_team_provider_id)
        )
        home_team = home_row.scalar_one_or_none()
        away_team = away_row.scalar_one_or_none()

        if not (league and home_team and away_team):
            return 0

        existing = await self.session.execute(
            select(Fixture).where(Fixture.provider_fixture_id == pf.provider_id)
        )
        fixture = existing.scalar_one_or_none()
        if fixture is None:
            fixture = Fixture(
                id=str(uuid.uuid4()),
                provider_fixture_id=pf.provider_id,
                league_id=league.id,
                season=pf.season,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                start_time=pf.start_time,
                status=pf.status,
                home_score=pf.home_score,
                away_score=pf.away_score,
                updated_at=datetime.now(UTC),
            )
            self.session.add(fixture)
            return 1
        else:
            fixture.status = pf.status
            fixture.home_score = pf.home_score
            fixture.away_score = pf.away_score
            fixture.updated_at = datetime.now(UTC)
            return 0

    # ── Events ────────────────────────────────────────────────────────────────
    async def sync_events(self, fixture_provider_id: str) -> int:
        provider_events = await self.provider.get_events(fixture_provider_id)
        fixture_row = await self.session.execute(
            select(Fixture).where(Fixture.provider_fixture_id == fixture_provider_id)
        )
        fixture = fixture_row.scalar_one_or_none()
        if not fixture:
            return 0

        count = 0
        for pe in provider_events:
            team: Team | None = None
            if pe.team_provider_id:
                team_row = await self.session.execute(
                    select(Team).where(Team.provider_team_id == pe.team_provider_id)
                )
                team = team_row.scalar_one_or_none()

            new_event = Event(
                id=str(uuid.uuid4()),
                fixture_id=fixture.id,
                type=pe.type,
                minute=pe.minute,
                team_id=team.id if team else None,
                player_name=pe.player_name,
                payload=json.dumps(pe.payload) if pe.payload else None,
                created_at=datetime.now(UTC),
            )
            self.session.add(new_event)
            count += 1

        await self.session.flush()
        log.info("Synced events", fixture=fixture_provider_id, count=count)
        return count

    # ── Standings ─────────────────────────────────────────────────────────────
    async def sync_standings(self, league_provider_id: str, season: str) -> int:
        provider_standings = await self.provider.get_standings(league_provider_id, season)
        league_row = await self.session.execute(
            select(League).where(League.provider_league_id == league_provider_id)
        )
        league = league_row.scalar_one_or_none()
        if not league:
            return 0

        count = 0
        for ps in provider_standings:
            team_row = await self.session.execute(
                select(Team).where(Team.provider_team_id == ps.team_provider_id)
            )
            team = team_row.scalar_one_or_none()
            if not team:
                continue

            stmt = pg_insert(Standing).values(
                league_id=league.id,
                season=ps.season,
                team_id=team.id,
                rank=ps.rank,
                played=ps.played,
                wins=ps.wins,
                draws=ps.draws,
                losses=ps.losses,
                goals_for=ps.goals_for,
                goals_against=ps.goals_against,
                goal_diff=ps.goal_diff,
                points=ps.points,
                updated_at=datetime.now(UTC),
            ).on_conflict_do_update(
                index_elements=["league_id", "season", "team_id"],
                set_={
                    "rank": ps.rank,
                    "played": ps.played,
                    "wins": ps.wins,
                    "draws": ps.draws,
                    "losses": ps.losses,
                    "goals_for": ps.goals_for,
                    "goals_against": ps.goals_against,
                    "goal_diff": ps.goal_diff,
                    "points": ps.points,
                    "updated_at": datetime.now(UTC),
                },
            )
            await self.session.execute(stmt)
            count += 1

        await self.session.flush()
        log.info("Synced standings", league=league_provider_id, count=count)
        return count
