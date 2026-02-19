"""Fixtures endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Event, Fixture, Team
from app.db.session import get_db
from app.schemas.fixtures import EventOut, FixtureDetailOut, FixtureOut
from app.schemas.common import PaginatedResponse
from app.core.security import get_current_user_id

router = APIRouter(tags=["fixtures"])


@router.get("/teams/{team_id}/fixtures", response_model=PaginatedResponse[FixtureOut])
async def team_fixtures(
    team_id: str,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> PaginatedResponse[FixtureOut]:
    now = datetime.now(UTC)
    from_dt = from_date or (now - timedelta(days=30))
    to_dt = to_date or (now + timedelta(days=30))

    q = (
        select(Fixture)
        .options(selectinload(Fixture.home_team), selectinload(Fixture.away_team))
        .where(
            ((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
            & (Fixture.start_time >= from_dt)
            & (Fixture.start_time <= to_dt)
        )
        .order_by(Fixture.start_time)
    )
    result = await db.execute(q)
    all_rows = result.scalars().all()
    total = len(all_rows)
    offset = (page - 1) * page_size
    items = all_rows[offset : offset + page_size]
    return PaginatedResponse(
        items=[FixtureOut.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/fixtures/{fixture_id}", response_model=FixtureDetailOut)
async def get_fixture(
    fixture_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> FixtureDetailOut:
    result = await db.execute(
        select(Fixture)
        .options(
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
            selectinload(Fixture.events),
        )
        .where(Fixture.id == fixture_id)
    )
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fixture not found")
    return FixtureDetailOut.model_validate(fixture)


@router.get("/fixtures/{fixture_id}/events", response_model=list[EventOut])
async def fixture_events(
    fixture_id: str,
    since_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> list[EventOut]:
    q = select(Event).where(Event.fixture_id == fixture_id).order_by(Event.created_at)
    if since_id:
        # Return only events after the given event id (created_at-based pagination)
        last_event = await db.get(Event, since_id)
        if last_event:
            q = q.where(Event.created_at > last_event.created_at)

    result = await db.execute(q)
    return [EventOut.model_validate(e) for e in result.scalars().all()]
