"""Safe HTTP error mapping.

Exception strings are deliberately excluded because they can contain SQL,
object-store locations, credentials, or raw trace content.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from triana_backend.application.self_serve import SelfServeRefusal

from .contracts import (
    AnalysisNotReady,
    IntegrityConflict,
    ResourceNotFound,
    ResourceUnavailable,
)


def _correlation_id(request: Request) -> str | None:
    value = request.headers.get("x-correlation-id")
    return value if value and len(value) <= 128 else None


async def unavailable_handler(
    request: Request, error: ResourceUnavailable
) -> JSONResponse:
    body: dict[str, Any] = {
        "code": error.code,
        "availability": error.availability.value,
        f"{error.resource_kind}_id": error.resource_id,
    }
    correlation_id = _correlation_id(request)
    if correlation_id is not None:
        body["correlation_id"] = correlation_id
    return JSONResponse(status_code=503, content=body)


async def not_found_handler(request: Request, error: ResourceNotFound) -> JSONResponse:
    body: dict[str, Any] = {
        "code": "RESOURCE_NOT_FOUND",
        "resource_kind": error.resource_kind,
        "resource_id": error.resource_id,
    }
    correlation_id = _correlation_id(request)
    if correlation_id is not None:
        body["correlation_id"] = correlation_id
    return JSONResponse(status_code=404, content=body)


async def integrity_conflict_handler(
    request: Request, error: IntegrityConflict
) -> JSONResponse:
    body: dict[str, Any] = {
        "code": error.code,
        "resource_kind": error.resource_kind,
        "resource_id": error.resource_id,
    }
    correlation_id = _correlation_id(request)
    if correlation_id is not None:
        body["correlation_id"] = correlation_id
    return JSONResponse(status_code=409, content=body)


async def analysis_not_ready_handler(
    request: Request, error: AnalysisNotReady
) -> JSONResponse:
    body: dict[str, Any] = {
        "code": error.code,
        "availability": error.availability.value,
    }
    correlation_id = _correlation_id(request)
    if correlation_id is not None:
        body["correlation_id"] = correlation_id
    return JSONResponse(status_code=503, content=body)


async def self_serve_refusal_handler(
    request: Request, error: SelfServeRefusal
) -> JSONResponse:
    body: dict[str, Any] = {"code": error.code, "detail": error.safe_message}
    correlation_id = _correlation_id(request)
    if correlation_id is not None:
        body["correlation_id"] = correlation_id
    return JSONResponse(status_code=error.status_code, content=body)
