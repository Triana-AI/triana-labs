"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI, HTTPException

from triana_backend.application.self_serve import SelfServeRefusal

from .contracts import (
    AnalysisNotReady,
    Authenticator,
    BackendReadPort,
    ImportCommandPort,
    IntegrityConflict,
    ResourceNotFound,
    ResourceUnavailable,
    RunCommandPort,
    SelfServePort,
)
from .errors import (
    analysis_not_ready_handler,
    integrity_conflict_handler,
    not_found_handler,
    self_serve_refusal_handler,
    unavailable_handler,
)
from .routes import create_v1_router


def create_app(
    *,
    reads: BackendReadPort,
    imports: ImportCommandPort,
    runs: RunCommandPort,
    readiness: Callable[[], bool],
    self_serve: SelfServePort | None = None,
    authenticate: Authenticator | None = None,
) -> FastAPI:
    app = FastAPI(title="Triana Backend", version="0.1.0")
    app.add_exception_handler(ResourceUnavailable, unavailable_handler)  # type: ignore[arg-type]
    app.add_exception_handler(AnalysisNotReady, analysis_not_ready_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ResourceNotFound, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        IntegrityConflict,
        integrity_conflict_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(SelfServeRefusal, self_serve_refusal_handler)  # type: ignore[arg-type]
    app.include_router(
        create_v1_router(
            reads=reads,
            imports=imports,
            runs=runs,
            self_serve=self_serve,
            authenticate=authenticate,
        )
    )

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready")
    @app.get("/healthz")
    def ready() -> dict[str, str]:
        if not readiness():
            raise HTTPException(
                status_code=503, detail="backend dependencies unavailable"
            )
        return {"status": "ready"}

    return app
