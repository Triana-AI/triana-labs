# syntax=docker/dockerfile:1.7
FROM python:3.12.11-slim-bookworm AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN python -m pip install --no-cache-dir uv==0.8.14

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN uv sync --frozen --no-dev
RUN .venv/bin/python -c "import dbos, fastapi, uvicorn; import triana_backend.main"

FROM python:3.12.11-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 triana \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/triana triana

WORKDIR /app
COPY --from=build --chown=triana:triana /app/.venv /app/.venv
COPY --from=build --chown=triana:triana /app/src /app/src
COPY --from=build --chown=triana:triana /app/alembic.ini /app/alembic.ini
COPY --from=build --chown=triana:triana /app/migrations /app/migrations

USER 10001:10001
EXPOSE 8000

# `triana_backend.main:app` is the CP7 composition seam. The build check above
# keeps deployment blocked until that singleton and its locked dependencies land.
CMD ["uvicorn", "triana_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
