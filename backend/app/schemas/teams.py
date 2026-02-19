"""Team and League schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_league_id: str
    name: str
    country: str
    season: str
    logo_url: str | None


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_team_id: str
    name: str
    short_name: str | None
    country: str | None
    logo_url: str | None
    league_id: str | None


class TeamWithLeagueOut(TeamOut):
    league: LeagueOut | None


class FollowIn(BaseModel):
    team_id: str


class FollowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: str
    user_id: str
    team: TeamOut | None = None
