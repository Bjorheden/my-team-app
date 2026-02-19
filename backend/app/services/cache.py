"""Redis cache helper."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

_pool: aioredis.ConnectionPool | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = aioredis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def cache_get(key: str) -> Any | None:
    async with aioredis.Redis(connection_pool=get_redis_pool()) as r:
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)


async def cache_set(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    settings = get_settings()
    ttl = ttl_seconds or settings.redis_cache_ttl_seconds
    async with aioredis.Redis(connection_pool=get_redis_pool()) as r:
        await r.set(key, json.dumps(value), ex=ttl)


async def cache_delete(key: str) -> None:
    async with aioredis.Redis(connection_pool=get_redis_pool()) as r:
        await r.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern."""
    async with aioredis.Redis(connection_pool=get_redis_pool()) as r:
        keys = [k async for k in r.scan_iter(pattern)]
        if keys:
            await r.delete(*keys)


async def redis_ping() -> bool:
    """Return True if Redis is reachable."""
    try:
        async with aioredis.Redis(connection_pool=get_redis_pool()) as r:
            return await r.ping()
    except Exception:
        return False
