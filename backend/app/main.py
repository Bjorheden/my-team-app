"""MyTeams FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api import admin, auth, catalog, fixtures, health, me, standings
from app.core.config import get_settings
from app.core.errors import generic_exception_handler, validation_exception_handler
from app.core.logging import RequestIDMiddleware, configure_logging

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.core.logging import get_logger
    log = get_logger()
    log.info(
        "MyTeams API starting",
        env=settings.app_env,
        provider=settings.effective_provider,
    )
    yield
    log.info("MyTeams API shutting down")


app = FastAPI(
    title="MyTeams API",
    version="0.1.0",
    description="Personalized football hub — REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = settings.api_v1_prefix

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(catalog.router, prefix=API_PREFIX)
app.include_router(me.router, prefix=API_PREFIX)
app.include_router(fixtures.router, prefix=API_PREFIX)
app.include_router(standings.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
