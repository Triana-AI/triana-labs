"""Process entrypoint: initialize DBOS on RDS, then serve loopback FastAPI."""

from __future__ import annotations

import uvicorn

from triana_backend.composition import compose_backend
from triana_backend.config import BackendSettings


def main() -> None:
    settings = BackendSettings.from_environment()
    runtime = compose_backend(settings)
    try:
        uvicorn.run(runtime.app, host=settings.host, port=settings.port)
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
