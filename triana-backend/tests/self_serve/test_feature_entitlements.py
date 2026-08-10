"""HTTP acceptance contract for workspace feature entitlements."""

# ruff: noqa: S101 - assertions are the acceptance-test contract.

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from triana_backend.api.app import create_app
from triana_backend.application.self_serve import SelfServeRefusal

OWNER_ONE = "feature-owner-one-token"
OWNER_TWO = "feature-owner-two-token"

DEFAULT_FEATURES = (
    ("TRACE_INGESTION", "AVAILABLE"),
    ("CONVERSATION_VIEWER", "AVAILABLE"),
    ("ANALYSIS", "LOCKED"),
    ("SIMULATION", "LOCKED"),
    ("TEAM_COLLABORATION", "LOCKED"),
    ("API_ACCESS", "LOCKED"),
)


class _UnusedPort:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"unrelated port unexpectedly used: {name}")


class _FeatureEntitlementPort:
    """Purpose-built stateful double for the frozen HTTP boundary."""

    def __init__(self) -> None:
        self.requests: set[tuple[str, str]] = set()

    def list_features(self, owner_subject: str) -> list[dict[str, str]]:
        return [
            {
                "feature_key": feature_key,
                "state": (
                    "REQUESTED"
                    if (owner_subject, feature_key) in self.requests
                    else default_state
                ),
            }
            for feature_key, default_state in DEFAULT_FEATURES
        ]

    def request_feature_access(
        self, owner_subject: str, feature_key: str
    ) -> dict[str, str]:
        catalog = dict(DEFAULT_FEATURES)
        if feature_key not in catalog:
            raise SelfServeRefusal(404, "FEATURE_NOT_FOUND", "Feature not found.")
        if catalog[feature_key] == "AVAILABLE":
            raise SelfServeRefusal(
                409, "FEATURE_ALREADY_AVAILABLE", "Feature is already available."
            )
        self.requests.add((owner_subject, feature_key))
        return {"feature_key": feature_key, "state": "REQUESTED"}


def _authenticate(bearer_token: str | None) -> str | None:
    return {
        OWNER_ONE: "oidc|feature-owner-one",
        OWNER_TWO: "oidc|feature-owner-two",
    }.get(bearer_token or "")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> TestClient:
    unused = _UnusedPort()
    feature_entitlements = _FeatureEntitlementPort()
    app = create_app(
        reads=unused,
        imports=unused,
        runs=unused,
        readiness=lambda: True,
        self_serve=unused,
        authenticate=_authenticate,
        feature_entitlements=feature_entitlements,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_new_owner_receives_closed_default_feature_catalog(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/me/features", headers=_headers(OWNER_ONE))

    assert response.status_code == 200, response.text
    assert response.json() == {
        "schema_version": 1,
        "features": [
            {"feature_key": feature_key, "state": state}
            for feature_key, state in DEFAULT_FEATURES
        ],
    }


def test_analysis_request_is_idempotent_and_owner_scoped(
    client: TestClient,
) -> None:
    first = client.post(
        "/api/v1/me/access-requests",
        headers=_headers(OWNER_ONE),
        json={"feature_key": "ANALYSIS"},
    )
    second = client.post(
        "/api/v1/me/access-requests",
        headers=_headers(OWNER_ONE),
        json={"feature_key": "ANALYSIS"},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert (
        first.json()
        == second.json()
        == {
            "feature_key": "ANALYSIS",
            "state": "REQUESTED",
        }
    )
    owner_one = client.get("/api/v1/me/features", headers=_headers(OWNER_ONE))
    owner_two = client.get("/api/v1/me/features", headers=_headers(OWNER_TWO))
    assert _state(owner_one.json(), "ANALYSIS") == "REQUESTED"
    assert _state(owner_two.json(), "ANALYSIS") == "LOCKED"


@pytest.mark.parametrize(
    ("feature_key", "expected_status"),
    [("NOT_A_FEATURE", 404), ("TRACE_INGESTION", 409)],
)
def test_request_refuses_unknown_and_already_available_features(
    client: TestClient,
    feature_key: str,
    expected_status: int,
) -> None:
    response = client.post(
        "/api/v1/me/access-requests",
        headers=_headers(OWNER_ONE),
        json={"feature_key": feature_key},
    )

    assert response.status_code == expected_status, response.text


def _state(catalog: dict[str, Any], feature_key: str) -> str:
    return next(
        feature["state"]
        for feature in catalog["features"]
        if feature["feature_key"] == feature_key
    )
