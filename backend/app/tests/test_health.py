"""Tests for health endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    response = await client.get("/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_returns_status(client: AsyncClient) -> None:
    response = await client.get("/v1/readyz")
    # May be 200 or 503 depending on Redis availability in CI;
    # either way the shape must be correct.
    data = response.json()
    assert "status" in data
