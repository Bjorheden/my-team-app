"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class RequestLinkIn(BaseModel):
    email: EmailStr


class VerifyTokenIn(BaseModel):
    token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None


class AuthTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DevLoginIn(BaseModel):
    """Dev-only: create/fetch a user by arbitrary ID (no email required)."""

    user_id: str
