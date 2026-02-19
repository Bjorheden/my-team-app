"""SQLAlchemy 2.0 declarative models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    from datetime import UTC

    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


# ── UUID PK helper ─────────────────────────────────────────────────────────────

def uuid_pk() -> str:
    return str(uuid.uuid4())


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    follows: Mapped[list[Follow]] = relationship("Follow", back_populates="user", cascade="all, delete-orphan")
    notification_preferences: Mapped[list[NotificationPreference]] = relationship(
        "NotificationPreference", back_populates="user", cascade="all, delete-orphan"
    )
    push_tokens: Mapped[list[PushToken]] = relationship(
        "PushToken", back_populates="user", cascade="all, delete-orphan"
    )


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    provider_league_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100))
    season: Mapped[str] = mapped_column(String(20))
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    teams: Mapped[list[Team]] = relationship("Team", back_populates="league")
    fixtures: Mapped[list[Fixture]] = relationship("Fixture", back_populates="league")
    standings: Mapped[list[Standing]] = relationship("Standing", back_populates="league")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    provider_team_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    league_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("leagues.id"), nullable=True, index=True
    )
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    league: Mapped[League | None] = relationship("League", back_populates="teams")
    follows: Mapped[list[Follow]] = relationship("Follow", back_populates="team", cascade="all, delete-orphan")


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("user_id", "team_id"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship("User", back_populates="follows")
    team: Mapped[Team] = relationship("Team", back_populates="follows")


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    provider_fixture_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    league_id: Mapped[str] = mapped_column(String(36), ForeignKey("leagues.id"), index=True)
    season: Mapped[str] = mapped_column(String(20))
    home_team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(50), default="NS")  # NS / 1H / HT / 2H / FT / ...
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    league: Mapped[League] = relationship("League", back_populates="fixtures")
    home_team: Mapped[Team] = relationship("Team", foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship("Team", foreign_keys=[away_team_id])
    events: Mapped[list[Event]] = relationship("Event", back_populates="fixture", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    fixture_id: Mapped[str] = mapped_column(String(36), ForeignKey("fixtures.id"), index=True)
    type: Mapped[str] = mapped_column(String(50))  # goal / card / substitution / ...
    minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("teams.id"), nullable=True)
    player_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob for extra data
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    fixture: Mapped[Fixture] = relationship("Fixture", back_populates="events")


class Standing(Base):
    __tablename__ = "standings"
    __table_args__ = (UniqueConstraint("league_id", "season", "team_id"),)

    league_id: Mapped[str] = mapped_column(String(36), ForeignKey("leagues.id"), primary_key=True)
    season: Mapped[str] = mapped_column(String(20), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id"), primary_key=True)
    rank: Mapped[int] = mapped_column(Integer)
    played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    goal_diff: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    league: Mapped[League] = relationship("League", back_populates="standings")
    team: Mapped[Team] = relationship("Team")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", "team_id"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    team_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("teams.id"), primary_key=True, nullable=True)
    match_start: Mapped[bool] = mapped_column(Boolean, default=True)
    goals: Mapped[bool] = mapped_column(Boolean, default=True)
    final_score: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship("User", back_populates="notification_preferences")


class PushToken(Base):
    __tablename__ = "push_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_pk)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    platform: Mapped[str] = mapped_column(String(20))  # ios / android / web
    token: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship("User", back_populates="push_tokens")
