"""Strict environment configuration for legacy and self-serve deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class BackendSettings:
    database_url: str
    dbos_system_database_url: str | None
    artifact_bucket: str
    kms_key_id: str
    aws_region: str | None
    labs_version: str
    labs_config_identity: str
    host: str
    port: int
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    public_app_origin: str | None = None
    self_serve_required: bool = False

    @classmethod
    def from_environment(cls) -> BackendSettings:
        settings = cls(
            database_url=_required("TRIANA_DATABASE_URL"),
            dbos_system_database_url=os.environ.get("DBOS_SYSTEM_DATABASE_URL"),
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
            oidc_issuer=os.environ.get("TRIANA_OIDC_ISSUER"),
            oidc_audience=os.environ.get("TRIANA_OIDC_AUDIENCE"),
            oidc_jwks_url=os.environ.get("TRIANA_OIDC_JWKS_URL"),
            public_app_origin=os.environ.get("TRIANA_PUBLIC_APP_ORIGIN"),
            self_serve_required=_flag(
                os.environ.get("TRIANA_SELF_SERVE_REQUIRED", "0")
            ),
        )
        _require_postgresql(settings.database_url, "TRIANA_DATABASE_URL")
        if settings.oidc_issuer is None:
            if settings.self_serve_required:
                raise ValueError(
                    "self-serve deployment requires all TRIANA_OIDC_* settings"
                )
            if settings.dbos_system_database_url is None:
                raise ValueError("DBOS_SYSTEM_DATABASE_URL is required")
            _require_postgresql(
                settings.dbos_system_database_url, "DBOS_SYSTEM_DATABASE_URL"
            )
        if not settings.kms_key_id.startswith("arn:aws:kms:"):
            raise ValueError("TRIANA_KMS_KEY_ID must be a full KMS key ARN")
        if settings.oidc_issuer is None and settings.host != "127.0.0.1":
            raise ValueError("TRIANA_BACKEND_HOST must be 127.0.0.1 for LABS-08")
        oidc_values = (
            settings.oidc_issuer,
            settings.oidc_audience,
            settings.oidc_jwks_url,
        )
        if any(oidc_values) and not all(oidc_values):
            raise ValueError("all TRIANA_OIDC_* settings are required together")
        if settings.self_serve_required:
            if not all(oidc_values):
                raise ValueError(
                    "self-serve deployment requires all TRIANA_OIDC_* settings"
                )
            if settings.public_app_origin is None:
                raise ValueError("TRIANA_PUBLIC_APP_ORIGIN is required for self-serve")
            if urlsplit(settings.public_app_origin).scheme.lower() != "https":
                raise ValueError("TRIANA_PUBLIC_APP_ORIGIN must use HTTPS")
            for value, name in (
                (settings.oidc_issuer, "TRIANA_OIDC_ISSUER"),
                (settings.oidc_jwks_url, "TRIANA_OIDC_JWKS_URL"),
            ):
                if value is None or urlsplit(value).scheme.lower() != "https":
                    raise ValueError(f"{name} must use HTTPS")
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


def _flag(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise ValueError("TRIANA_SELF_SERVE_REQUIRED must be a boolean flag")
