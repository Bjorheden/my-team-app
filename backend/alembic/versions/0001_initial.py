"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-19 00:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "leagues",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_league_id", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("season", sa.String(20), nullable=False),
        sa.Column("logo_url", sa.Text, nullable=True),
    )
    op.create_index("ix_leagues_provider_league_id", "leagues", ["provider_league_id"])

    op.create_table(
        "teams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_team_id", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("league_id", sa.String(36), sa.ForeignKey("leagues.id"), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.Text, nullable=True),
    )
    op.create_index("ix_teams_provider_team_id", "teams", ["provider_team_id"])
    op.create_index("ix_teams_league_id", "teams", ["league_id"])

    op.create_table(
        "follows",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("team_id", sa.String(36), sa.ForeignKey("teams.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "team_id"),
    )

    op.create_table(
        "fixtures",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_fixture_id", sa.String(64), nullable=False, unique=True),
        sa.Column("league_id", sa.String(36), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("season", sa.String(20), nullable=False),
        sa.Column("home_team_id", sa.String(36), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("away_team_id", sa.String(36), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="NS"),
        sa.Column("home_score", sa.Integer, nullable=True),
        sa.Column("away_score", sa.Integer, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fixtures_provider_fixture_id", "fixtures", ["provider_fixture_id"])
    op.create_index("ix_fixtures_league_id", "fixtures", ["league_id"])
    op.create_index("ix_fixtures_home_team_id", "fixtures", ["home_team_id"])
    op.create_index("ix_fixtures_away_team_id", "fixtures", ["away_team_id"])
    op.create_index("ix_fixtures_start_time", "fixtures", ["start_time"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("fixture_id", sa.String(36), sa.ForeignKey("fixtures.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("minute", sa.Integer, nullable=True),
        sa.Column("team_id", sa.String(36), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("player_name", sa.String(255), nullable=True),
        sa.Column("payload", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_fixture_id", "events", ["fixture_id"])

    op.create_table(
        "standings",
        sa.Column("league_id", sa.String(36), sa.ForeignKey("leagues.id"), primary_key=True),
        sa.Column("season", sa.String(20), primary_key=True),
        sa.Column("team_id", sa.String(36), sa.ForeignKey("teams.id"), primary_key=True),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("played", sa.Integer, nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer, nullable=False, server_default="0"),
        sa.Column("draws", sa.Integer, nullable=False, server_default="0"),
        sa.Column("losses", sa.Integer, nullable=False, server_default="0"),
        sa.Column("goals_for", sa.Integer, nullable=False, server_default="0"),
        sa.Column("goals_against", sa.Integer, nullable=False, server_default="0"),
        sa.Column("goal_diff", sa.Integer, nullable=False, server_default="0"),
        sa.Column("points", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("league_id", "season", "team_id"),
    )

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("team_id", sa.String(36), sa.ForeignKey("teams.id"), primary_key=True),
        sa.Column("match_start", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("goals", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("final_score", sa.Boolean, nullable=False, server_default="true"),
        sa.UniqueConstraint("user_id", "team_id"),
    )

    op.create_table(
        "push_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("token", sa.Text, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_push_tokens_user_id", "push_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("push_tokens")
    op.drop_table("notification_preferences")
    op.drop_table("standings")
    op.drop_table("events")
    op.drop_table("fixtures")
    op.drop_table("follows")
    op.drop_table("teams")
    op.drop_table("leagues")
    op.drop_table("users")
