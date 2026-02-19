"""Fixture and Event schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.teams import TeamOut


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    minute: int | None
    team_id: str | None
    player_name: str | None
    payload: str | None
    created_at: datetime


class FixtureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_fixture_id: str
    league_id: str
    season: str
    home_team_id: str
    away_team_id: str
    start_time: datetime
    status: str
    home_score: int | None
    away_score: int | None
    updated_at: datetime

    home_team: TeamOut | None = None
    away_team: TeamOut | None = None


class FixtureDetailOut(FixtureOut):
    events: list[EventOut] = []


class SyncIn(BaseModel):
    scope: str  # fixtures | standings | events
    hours_forward: int = 72
