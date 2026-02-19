"""Periodic sync tasks executed by the worker."""

from __future__ import annotations

import asyncio
import logging

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_worker_settings

log = structlog.get_logger("worker.tasks")


def _make_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def _get_provider() -> object:
    settings = get_worker_settings()
    if settings.provider_api_key and settings.provider_name == "api_football":
        from app.provider_adapters.api_football import ApiFootballProvider  # type: ignore[import]
        return ApiFootballProvider(
            api_key=settings.provider_api_key,
            base_url=settings.provider_base_url or "https://v3.football.api-sports.io",
        )
    from app.provider_adapters.mock import MockProvider  # type: ignore[import]
    return MockProvider()


# ── Individual sync tasks ─────────────────────────────────────────────────────

async def sync_fixtures_task() -> None:
    """Sync upcoming and recent fixtures for all tracked teams."""
    from datetime import UTC, datetime, timedelta

    settings = get_worker_settings()
    factory = _make_session_factory(settings.database_url)
    provider = _get_provider()

    async with factory() as session:
        from sqlalchemy.orm import DeclarativeBase

        # Import DB models from the shared layer
        # Worker re-uses backend models by having them importable via PYTHONPATH
        try:
            from app.db_models import Team, Fixture  # type: ignore[import]
        except ImportError:
            log.warning("DB models not importable – skipping fixture sync")
            return

        from app.sync_helper import SyncService  # type: ignore[import]
        svc = SyncService(provider, session)  # type: ignore[arg-type]

        teams_result = await session.execute(select(Team))
        teams = teams_result.scalars().all()
        for team in teams:
            await svc.sync_fixtures(team.provider_team_id, hours_forward=72)
        await session.commit()
    log.info("Fixture sync complete", team_count=len(teams))


async def sync_standings_task() -> None:
    """Sync standings for all tracked leagues."""
    settings = get_worker_settings()
    factory = _make_session_factory(settings.database_url)
    provider = _get_provider()

    async with factory() as session:
        try:
            from app.db_models import League  # type: ignore[import]
            from app.sync_helper import SyncService  # type: ignore[import]
        except ImportError:
            log.warning("DB models not importable – skipping standings sync")
            return

        svc = SyncService(provider, session)  # type: ignore[arg-type]
        leagues_result = await session.execute(select(League))
        leagues = leagues_result.scalars().all()
        for league in leagues:
            await svc.sync_standings(league.provider_league_id, league.season)
        await session.commit()
    log.info("Standings sync complete", league_count=len(leagues))


async def sync_live_events_task() -> None:
    """Sync events for fixtures that are currently in-progress."""
    from datetime import UTC, datetime, timedelta

    settings = get_worker_settings()
    factory = _make_session_factory(settings.database_url)
    provider = _get_provider()

    async with factory() as session:
        try:
            from app.db_models import Fixture  # type: ignore[import]
            from app.sync_helper import SyncService  # type: ignore[import]
        except ImportError:
            log.warning("DB models not importable – skipping event sync")
            return

        svc = SyncService(provider, session)  # type: ignore[arg-type]
        now = datetime.now(UTC)
        result = await session.execute(
            select(Fixture).where(
                Fixture.status.not_in(["FT", "AET", "PEN", "NS", "TBD", "CANC"]),
                Fixture.start_time <= now,
                Fixture.start_time >= now - timedelta(hours=4),
            )
        )
        fixtures = result.scalars().all()
        for fixture in fixtures:
            await svc.sync_events(fixture.provider_fixture_id)
        await session.commit()
    log.info("Live event sync complete", fixture_count=len(fixtures))
