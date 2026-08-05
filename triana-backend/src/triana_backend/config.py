"""Strict environment configuration for the private RDS/S3 deployment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class BackendSettings:
    database_url: str
    dbos_system_database_url: str
    artifact_bucket: str
    kms_key_id: str
    aws_region: str | None
    labs_version: str
    labs_config_identity: str
    host: str
    port: int

    @classmethod
    def from_environment(cls) -> BackendSettings:
        settings = cls(
            database_url=_required("TRIANA_DATABASE_URL"),
            dbos_system_database_url=_required("DBOS_SYSTEM_DATABASE_URL"),
            artifact_bucket=_required("TRIANA_ARTIFACT_BUCKET"),
            kms_key_id=_required("TRIANA_KMS_KEY_ID"),
            aws_region=os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION"),
            labs_version=os.environ.get("TRIANA_LABS_VERSION", "labs08-unavailable"),
            labs_config_identity=os.environ.get(
                "TRIANA_LABS_CONFIG_IDENTITY", "compiler-not-integrated"
            ),
            host=os.environ.get("TRIANA_BACKEND_HOST", "127.0.0.1"),
            port=_port(os.environ.get("TRIANA_BACKEND_PORT", "8000")),
        )
        _require_postgresql(settings.database_url, "TRIANA_DATABASE_URL")
        _require_postgresql(
            settings.dbos_system_database_url, "DBOS_SYSTEM_DATABASE_URL"
        )
        if settings.host != "127.0.0.1":
            raise ValueError("TRIANA_BACKEND_HOST must be 127.0.0.1 for LABS-08")
        return settings


def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def _require_postgresql(value: str, name: str) -> None:
    scheme = urlsplit(value).scheme.lower()
    if scheme not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise ValueError(f"{name} must use PostgreSQL; local persistence is forbidden")


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise ValueError("TRIANA_BACKEND_PORT must be an integer") from error
    if not 1 <= port <= 65535:
        raise ValueError("TRIANA_BACKEND_PORT must be between 1 and 65535")
    return port
