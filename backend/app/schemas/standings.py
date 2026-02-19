"""Standings schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.teams import TeamOut


class StandingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    league_id: str
    season: str
    team_id: str
    rank: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    updated_at: datetime

    team: TeamOut | None = None


class DashboardTeamEntry(BaseModel):
    """One followed team's summary for the dashboard."""

    team: TeamOut
    standing: StandingOut | None
    next_fixture: "FixtureBrief | None"
    last_fixture: "FixtureBrief | None"


class FixtureBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: datetime
    status: str
    home_team_id: str
    away_team_id: str
    home_score: int | None
    away_score: int | None
    home_team: TeamOut | None = None
    away_team: TeamOut | None = None


class NotificationPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    team_id: str | None
    match_start: bool
    goals: bool
    final_score: bool


class NotificationPreferenceIn(BaseModel):
    team_id: str | None = None
    match_start: bool = True
    goals: bool = True
    final_score: bool = True


class PushTokenIn(BaseModel):
    platform: str  # ios | android | web
    token: str


class PushTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str
    token: str
