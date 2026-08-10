FROM ghcr.io/astral-sh/uv:0.12.0 AS uv
FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64 AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /build
COPY triana-labs/pyproject.toml triana-labs/uv.lock ./triana-labs/
COPY triana-labs/src ./triana-labs/src
COPY triana-preview/pyproject.toml triana-preview/uv.lock ./triana-preview/
COPY triana-preview/src ./triana-preview/src
RUN cd triana-preview && UV_PROJECT_ENVIRONMENT=/opt/triana-preview uv sync --locked --no-dev

FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64
RUN useradd --create-home --uid 10001 preview
COPY --from=build /opt/triana-preview /opt/triana-preview
ENV PATH="/opt/triana-preview/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
USER preview
ENTRYPOINT ["triana-preview"]
