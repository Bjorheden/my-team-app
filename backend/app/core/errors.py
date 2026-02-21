"""Consistent error response shape and exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette import status


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def not_found(resource: str, resource_id: Any = None) -> ORJSONResponse:
    msg = f"{resource} not found" if resource_id is None else f"{resource} '{resource_id}' not found"
    return error_response("NOT_FOUND", msg, status_code=status.HTTP_404_NOT_FOUND)


def conflict(message: str) -> ORJSONResponse:
    return error_response("CONFLICT", message, status_code=status.HTTP_409_CONFLICT)


def forbidden(message: str = "Forbidden") -> ORJSONResponse:
    return error_response("FORBIDDEN", message, status_code=status.HTTP_403_FORBIDDEN)


# ── FastAPI exception handlers ────────────────────────────────────────────────


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    from app.core.logging import get_logger

    log = get_logger()
    log.exception("Unhandled exception", exc_info=exc)
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": {},
            }
        },
    )
