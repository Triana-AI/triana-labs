"""Configurable OIDC JWT verification; claims are never trusted unverified."""

from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWKClient


class OidcJwtAuthenticator:
    def __init__(self, *, issuer: str, audience: str, jwks_url: str) -> None:
        if not issuer or not audience or not jwks_url.startswith("https://"):
            raise ValueError("OIDC issuer, audience, and HTTPS JWKS URL are required")
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._keys = PyJWKClient(jwks_url, cache_keys=True)

    def __call__(self, token: str | None) -> str | None:
        if not token:
            return None
        try:
            key = self._keys.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                key.key,
                algorithms=["RS256", "ES256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )
        except jwt.PyJWTError:
            return None
        subject = claims.get("sub")
        return subject if isinstance(subject, str) and subject else None
