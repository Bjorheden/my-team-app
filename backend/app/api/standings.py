"""Standings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user_id
from app.db.models import League, Standing
from app.db.session import get_db
from app.schemas.standings import StandingOut
from app.services.cache import cache_get, cache_set

router = APIRouter(tags=["standings"])


@router.get("/leagues/{league_id}/standings", response_model=list[StandingOut])
async def league_standings(
    league_id: str,
    season: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> list[StandingOut]:
    # Use the league's current season if not specified
    if not season:
        league_result = await db.execute(select(League).where(League.id == league_id))
        league = league_result.scalar_one_or_none()
        if not league:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="League not found")
        season = league.season

    cache_key = f"standings:{league_id}:{season}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return [StandingOut.model_validate(s) for s in cached]

    result = await db.execute(
        select(Standing)
        .options(selectinload(Standing.team))
        .where(Standing.league_id == league_id, Standing.season == season)
        .order_by(Standing.rank)
    )
    standings = result.scalars().all()
    out = [StandingOut.model_validate(s) for s in standings]
    await cache_set(cache_key, [s.model_dump(mode="json") for s in out])
    return out
