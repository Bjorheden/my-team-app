"""Admin / internal endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import League, Team
from app.db.session import get_db
from app.schemas.common import OKResponse
from app.schemas.fixtures import SyncIn
from app.services.factory import get_provider
from app.services.provider import FootballProvider
from app.services.sync import SyncService

router = APIRouter(prefix="/admin", tags=["admin"])
log = get_logger("admin")


@router.post("/sync", response_model=OKResponse)
async def trigger_sync(
    body: SyncIn,
    db: AsyncSession = Depends(get_db),
    provider: FootballProvider = Depends(get_provider),
) -> OKResponse:
    """Manually trigger a data sync. Intended for admin/internal use."""
    svc = SyncService(provider, db)

    if body.scope == "standings":
        leagues = (await db.execute(select(League))).scalars().all()
        for league in leagues:
            league_prov_id = league.provider_league_id
            await svc.sync_standings(league_prov_id, league.season)
        await db.commit()
        log.info("Admin sync: standings complete", leagues=len(leagues))

    elif body.scope == "fixtures":
        teams = (await db.execute(select(Team))).scalars().all()
        for team in teams:
            await svc.sync_fixtures(team.provider_team_id, body.hours_forward)
        await db.commit()
        log.info("Admin sync: fixtures complete", teams=len(teams))

    elif body.scope == "events":
        from datetime import UTC, datetime, timedelta

        from app.db.models import Fixture

        now = datetime.now(UTC)
        result = await db.execute(
            select(Fixture).where(
                Fixture.status.not_in(["FT", "AET", "PEN"]),
                Fixture.start_time <= now + timedelta(hours=body.hours_forward),
            )
        )
        fixtures = result.scalars().all()
        for fixture in fixtures:
            await svc.sync_events(fixture.provider_fixture_id)
        await db.commit()
        log.info("Admin sync: events complete", fixtures=len(fixtures))

    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scope: {body.scope}. Use: fixtures, standings, events",
        )

    return OKResponse()
