"""Import-safe module-level ASGI entrypoint and command-line server."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Resolve these at startup so importing the checked-in Uvicorn target does
    # not read environment, credentials, RDS, S3, or DBOS state.
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
    from triana_backend.config import BackendSettings

    settings = BackendSettings.from_environment()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
