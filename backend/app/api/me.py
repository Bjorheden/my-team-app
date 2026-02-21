"""Me endpoints: follows, dashboard, notification preferences, push tokens."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user_id
from app.db.models import Fixture, Follow, NotificationPreference, PushToken, Standing, Team, User
from app.db.session import get_db
from app.schemas.common import OKResponse
from app.schemas.standings import (
    DashboardTeamEntry,
    FixtureBrief,
    NotificationPreferenceIn,
    NotificationPreferenceOut,
    PushTokenIn,
    PushTokenOut,
    StandingOut,
)
from app.schemas.teams import FollowIn, FollowOut, TeamOut
from app.services.cache import cache_delete_pattern, cache_get, cache_set

router = APIRouter(prefix="/me", tags=["me"])


# ── Helper ────────────────────────────────────────────────────────────────────


async def _get_or_404(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ── Follows ───────────────────────────────────────────────────────────────────


@router.get("/follows", response_model=list[FollowOut])
async def list_follows(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[FollowOut]:
    result = await db.execute(select(Follow).options(selectinload(Follow.team)).where(Follow.user_id == user_id))
    return [FollowOut.model_validate(f) for f in result.scalars().all()]


@router.post("/follows", response_model=FollowOut, status_code=status.HTTP_201_CREATED)
async def follow_team(
    body: FollowIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> FollowOut:
    # Ensure team exists
    team_result = await db.execute(select(Team).where(Team.id == body.team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Idempotent: return existing follow
    existing = await db.execute(select(Follow).where(Follow.user_id == user_id, Follow.team_id == body.team_id))
    follow = existing.scalar_one_or_none()
    if follow:
        return FollowOut.model_validate(follow)

    follow = Follow(user_id=user_id, team_id=body.team_id, created_at=datetime.now(UTC))
    db.add(follow)
    await db.flush()
    await cache_delete_pattern(f"dashboard:{user_id}:*")
    return FollowOut(user_id=user_id, team_id=body.team_id, team=TeamOut.model_validate(team))


@router.delete("/follows/{team_id}", response_model=OKResponse)
async def unfollow_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> OKResponse:
    await db.execute(delete(Follow).where(Follow.user_id == user_id, Follow.team_id == team_id))
    await cache_delete_pattern(f"dashboard:{user_id}:*")
    return OKResponse()


# ── Dashboard ─────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=list[DashboardTeamEntry])
async def dashboard(
    days_back: int = Query(default=7, ge=0, le=30),
    days_forward: int = Query(default=7, ge=0, le=60),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[DashboardTeamEntry]:
    cache_key = f"dashboard:{user_id}:{days_back}:{days_forward}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return [DashboardTeamEntry.model_validate(entry) for entry in cached]

    follows_result = await db.execute(
        select(Follow).options(selectinload(Follow.team)).where(Follow.user_id == user_id)
    )
    follows = follows_result.scalars().all()
    now = datetime.now(UTC)
    from_time = now - timedelta(days=days_back)
    to_time = now + timedelta(days=days_forward)

    entries: list[DashboardTeamEntry] = []
    for follow in follows:
        team = follow.team
        team_out = TeamOut.model_validate(team)

        # Standing
        standing_row = await db.execute(
            select(Standing).where(Standing.team_id == team.id).order_by(Standing.season.desc())
        )
        standing = standing_row.scalar_one_or_none()
        standing_out = StandingOut.model_validate(standing) if standing else None

        # Fixtures window
        fixtures_result = await db.execute(
            select(Fixture)
            .options(selectinload(Fixture.home_team), selectinload(Fixture.away_team))
            .where(
                ((Fixture.home_team_id == team.id) | (Fixture.away_team_id == team.id))
                & (Fixture.start_time >= from_time)
                & (Fixture.start_time <= to_time)
            )
            .order_by(Fixture.start_time)
        )
        all_fixtures = fixtures_result.scalars().all()
        past = [f for f in all_fixtures if f.start_time < now]
        future = [f for f in all_fixtures if f.start_time >= now]

        last_fixture = FixtureBrief.model_validate(past[-1]) if past else None
        next_fixture = FixtureBrief.model_validate(future[0]) if future else None

        entries.append(
            DashboardTeamEntry(
                team=team_out,
                standing=standing_out,
                next_fixture=next_fixture,
                last_fixture=last_fixture,
            )
        )

    await cache_set(cache_key, [e.model_dump(mode="json") for e in entries])
    return entries


# ── Notification preferences ──────────────────────────────────────────────────


@router.get("/notification-preferences", response_model=list[NotificationPreferenceOut])
async def get_notification_prefs(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[NotificationPreferenceOut]:
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
    return [NotificationPreferenceOut.model_validate(p) for p in result.scalars().all()]


@router.put("/notification-preferences", response_model=NotificationPreferenceOut)
async def upsert_notification_prefs(
    body: NotificationPreferenceIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> NotificationPreferenceOut:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.team_id == body.team_id,
        )
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        pref = NotificationPreference(
            user_id=user_id,
            team_id=body.team_id,
            match_start=body.match_start,
            goals=body.goals,
            final_score=body.final_score,
        )
        db.add(pref)
    else:
        pref.match_start = body.match_start
        pref.goals = body.goals
        pref.final_score = body.final_score
    await db.flush()
    return NotificationPreferenceOut.model_validate(pref)


# ── Push tokens ───────────────────────────────────────────────────────────────


@router.post("/push-tokens", response_model=PushTokenOut, status_code=status.HTTP_201_CREATED)
async def register_push_token(
    body: PushTokenIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> PushTokenOut:
    # Idempotent by token value
    existing = await db.execute(select(PushToken).where(PushToken.token == body.token))
    push_token = existing.scalar_one_or_none()
    if push_token is None:
        push_token = PushToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            platform=body.platform,
            token=body.token,
            created_at=datetime.now(UTC),
        )
        db.add(push_token)
        await db.flush()
    return PushTokenOut.model_validate(push_token)
