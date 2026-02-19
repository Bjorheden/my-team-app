"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from app.services.cache import redis_ping

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> ORJSONResponse:
    """Liveness probe – fast, no dependencies."""
    return ORJSONResponse({"status": "ok"})


@router.get("/readyz")
async def readyz() -> ORJSONResponse:
    """Readiness probe – checks Redis connectivity."""
    redis_ok = await redis_ping()
    if not redis_ok:
        return ORJSONResponse(
            status_code=503,
            content={"status": "degraded", "checks": {"redis": "fail"}},
        )
    return ORJSONResponse({"status": "ok", "checks": {"redis": "pass"}})
