# syntax=docker/dockerfile:1.7
FROM python:3.13.14-slim-bookworm AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN python -m pip install --no-cache-dir uv==0.8.14

WORKDIR /workspace/triana-backend
COPY triana-backend/pyproject.toml triana-backend/uv.lock ./
COPY triana-labs/pyproject.toml /workspace/triana-labs/pyproject.toml
COPY triana-labs/src /workspace/triana-labs/src
RUN uv sync --frozen --no-dev --no-install-project

COPY triana-backend/src ./src
COPY triana-backend/alembic.ini ./
COPY triana-backend/migrations ./migrations
RUN uv sync --frozen --no-dev
RUN .venv/bin/python -c "import dbos, fastapi, uvicorn; import triana_backend.main"

FROM python:3.13.14-slim-bookworm AS runtime

ENV PATH="/workspace/triana-backend/.venv/bin:$PATH" \
    PYTHONPATH="/workspace/triana-labs/src" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 triana \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/triana triana

WORKDIR /workspace/triana-backend
COPY --from=build --chown=triana:triana /workspace/triana-backend/.venv ./.venv
COPY --from=build --chown=triana:triana /workspace/triana-backend/src ./src
COPY --from=build --chown=triana:triana /workspace/triana-backend/alembic.ini ./alembic.ini
COPY --from=build --chown=triana:triana /workspace/triana-backend/migrations ./migrations
COPY --from=build --chown=triana:triana /workspace/triana-labs /workspace/triana-labs

USER 10001:10001
EXPOSE 8000

# `triana_backend.main:app` is the CP7 composition seam. The build check above
# keeps deployment blocked until that singleton and its locked dependencies land.
CMD ["uvicorn", "triana_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
