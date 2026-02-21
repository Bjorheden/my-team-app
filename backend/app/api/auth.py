"""Authentication endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import AuthTokenOut, DevLoginIn, RequestLinkIn, UserOut, VerifyTokenIn
from app.schemas.common import OKResponse

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("auth")

# In-memory token store for MVP magic-link stub (replace with Redis in production)
_pending_tokens: dict[str, str] = {}  # token -> user_id


@router.post("/request-link", response_model=OKResponse)
async def request_link(
    body: RequestLinkIn,
    db: AsyncSession = Depends(get_db),
) -> OKResponse:
    """Send a magic link to the provided email (stubbed for MVP)."""
    # Ensure user exists
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=str(uuid.uuid4()), email=body.email, created_at=datetime.now(UTC))
        db.add(user)
        await db.flush()

    token = str(uuid.uuid4())
    _pending_tokens[token] = user.id
    log.info("Magic link requested (STUB)", email=body.email, token=token)
    return OKResponse(ok=True)


@router.post("/verify", response_model=AuthTokenOut)
async def verify_token(
    body: VerifyTokenIn,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthTokenOut:
    """Exchange a magic-link token for a JWT access token."""
    user_id = _pending_tokens.pop(body.token, None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token not found or expired"},
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = create_access_token(user.id, settings)
    return AuthTokenOut(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


# ── Dev-only endpoint ─────────────────────────────────────────────────────────


@router.post(
    "/dev-login",
    response_model=AuthTokenOut,
    include_in_schema=True,
    description="**Development only.** Disabled in non-development environments.",
)
async def dev_login(
    body: DevLoginIn,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthTokenOut:
    if not settings.is_development:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=body.user_id, email=None, created_at=datetime.now(UTC))
        db.add(user)
        await db.flush()

    access_token = create_access_token(user.id, settings)
    return AuthTokenOut(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )
