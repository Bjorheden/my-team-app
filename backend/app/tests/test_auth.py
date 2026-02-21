"""Tests for authentication endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_link_returns_ok(client: AsyncClient) -> None:
    response = await client.post("/v1/auth/request-link", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.asyncio
async def test_verify_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.post("/v1/auth/verify", json={"token": "not-a-real-token"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dev_login_creates_user(client: AsyncClient) -> None:
    response = await client.post("/v1/auth/dev-login", json={"user_id": "test-user-123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == "test-user-123"


@pytest.mark.asyncio
async def test_dev_login_idempotent(client: AsyncClient) -> None:
    """Calling dev-login twice with same user_id returns same user."""
    payload = {"user_id": "idempotent-user"}
    r1 = await client.post("/v1/auth/dev-login", json=payload)
    r2 = await client.post("/v1/auth/dev-login", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]


@pytest.mark.asyncio
async def test_magic_link_full_flow(client: AsyncClient) -> None:
    """request-link + verify with real token works end-to-end."""
    # 1. request link
    r1 = await client.post("/v1/auth/request-link", json={"email": "magic@example.com"})
    assert r1.status_code == 200

    # 2. Grab the token from the in-memory store (only possible in tests)
    from app.api.auth import _pending_tokens

    token = next(iter(_pending_tokens))

    # 3. verify
    r2 = await client.post("/v1/auth/verify", json={"token": token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
