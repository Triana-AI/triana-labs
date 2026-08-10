"""Import-safe module-level ASGI entrypoint and command-line server."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Resolve these at startup so importing the checked-in Uvicorn target does
    # not read environment, credentials, RDS, S3, or DBOS state.
    if os.environ.get("TRIANA_TRACE_TO_EVAL_LOCAL") == "1":
        from triana_labs.trace_to_eval.semantic import FoundryStructuredSemanticModel

        from triana_backend.api.app import create_local_trace_to_eval_app
        from triana_backend.services.trace_to_eval import LocalTraceToEvalService

        local = create_local_trace_to_eval_app(
            LocalTraceToEvalService(
                Path(
                    os.environ.get("TRIANA_TRACE_TO_EVAL_ROOT", ".triana-trace-to-eval")
                ),
                semantic_model=FoundryStructuredSemanticModel.from_environment(),
            )
        )
        app.mount("/", local)
        yield
        return

    from triana_backend.composition import compose_backend
    from triana_backend.config import BackendSettings

    runtime = compose_backend(BackendSettings.from_environment())
    app.mount("/", runtime.app)
    try:
        yield
    finally:
        runtime.close()


app = FastAPI(title="Triana Backend Runtime", lifespan=_lifespan)


def main() -> None:
    if os.environ.get("TRIANA_TRACE_TO_EVAL_LOCAL") == "1":
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=int(os.environ.get("TRIANA_PORT", "8000")),
        )
        return

    from triana_backend.config import BackendSettings

    settings = BackendSettings.from_environment()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
