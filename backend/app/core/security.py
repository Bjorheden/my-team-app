"""JWT creation, verification, and FastAPI dependency for current user."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(subject: str, settings: Settings | None = None) -> str:
    cfg = settings or get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=cfg.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)


def decode_access_token(token: str, settings: Settings | None = None) -> str:
    """Return the subject (user id) or raise HTTPException 401."""
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise _credentials_error()
        return sub
    except JWTError as err:
        raise _credentials_error() from err


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_TOKEN", "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None:
        raise _credentials_error()
    return decode_access_token(credentials.credentials, settings)
