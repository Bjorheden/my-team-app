"""Catalog endpoints: team search, leagues, league teams."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import League, Team
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.teams import LeagueOut, TeamOut, TeamWithLeagueOut
from app.services.factory import get_provider
from app.services.provider import FootballProvider

router = APIRouter(tags=["catalog"])


@router.get("/teams/search", response_model=PaginatedResponse[TeamWithLeagueOut])
async def search_teams(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    provider: FootballProvider = Depends(get_provider),
) -> PaginatedResponse[TeamWithLeagueOut]:
    """Search teams by name. Checks local DB first, falls back to provider."""
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.league))
        .where(Team.name.ilike(f"%{q}%"))
        .limit(limit)
    )
    teams = result.scalars().all()

    if not teams:
        # Fall back to provider search (does not persist)
        provider_teams = await provider.search_teams(q, limit)
        return PaginatedResponse(
            items=[
                TeamWithLeagueOut(
                    id=f"provider-{pt.provider_id}",
                    provider_team_id=pt.provider_id,
                    name=pt.name,
                    short_name=pt.short_name,
                    country=pt.country,
                    logo_url=pt.logo_url,
                    league_id=None,
                    league=None,
                )
                for pt in provider_teams
            ],
            total=len(provider_teams),
            page=1,
            page_size=limit,
            has_next=False,
        )

    items = [TeamWithLeagueOut.model_validate(t) for t in teams]
    return PaginatedResponse(items=items, total=len(items), page=1, page_size=limit, has_next=False)


@router.get("/leagues", response_model=list[LeagueOut])
async def list_leagues(
    country: str | None = Query(default=None),
    season: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[LeagueOut]:
    """List leagues, optionally filtered by country and/or season."""
    q = select(League)
    if country:
        q = q.where(League.country.ilike(f"%{country}%"))
    if season:
        q = q.where(League.season == season)
    result = await db.execute(q)
    return [LeagueOut.model_validate(lg) for lg in result.scalars().all()]


@router.get("/leagues/{league_id}/teams", response_model=list[TeamOut])
async def list_league_teams(
    league_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TeamOut]:
    """List all teams in a league."""
    result = await db.execute(select(Team).where(Team.league_id == league_id))
    return [TeamOut.model_validate(t) for t in result.scalars().all()]
