"""Closed feature catalog and deterministic workspace entitlement states."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from typing import Any, Protocol

from triana_backend.application.self_serve import SelfServeRefusal

FEATURE_CATALOG: tuple[tuple[str, str], ...] = (
    ("TRACE_INGESTION", "AVAILABLE"),
    ("CONVERSATION_VIEWER", "AVAILABLE"),
    ("ANALYSIS", "LOCKED"),
    ("SIMULATION", "LOCKED"),
    ("TEAM_COLLABORATION", "LOCKED"),
    ("API_ACCESS", "LOCKED"),
)


class FeatureEntitlementRepository(Protocol):
    def list_feature_state(self, owner_subject: str) -> tuple[Set[str], Set[str]]: ...

    def create_feature_access_request(
        self, owner_subject: str, feature_key: str
    ) -> None: ...


class FeatureEntitlementService:
    def __init__(self, repository: FeatureEntitlementRepository) -> None:
        self._repository = repository

    def list_features(self, owner_subject: str) -> Sequence[Mapping[str, Any]]:
        entitled, requested = self._repository.list_feature_state(owner_subject)
        return [
            {
                "feature_key": feature_key,
                "state": (
                    "AVAILABLE"
                    if default_state == "AVAILABLE" or feature_key in entitled
                    else "REQUESTED"
                    if feature_key in requested
                    else "LOCKED"
                ),
            }
            for feature_key, default_state in FEATURE_CATALOG
        ]

    def request_feature_access(
        self, owner_subject: str, feature_key: str
    ) -> Mapping[str, Any]:
        defaults = dict(FEATURE_CATALOG)
        if feature_key not in defaults:
            raise SelfServeRefusal(404, "FEATURE_NOT_FOUND", "Feature not found.")
        entitled, _ = self._repository.list_feature_state(owner_subject)
        if defaults[feature_key] == "AVAILABLE" or feature_key in entitled:
            raise SelfServeRefusal(
                409,
                "FEATURE_ALREADY_AVAILABLE",
                "Feature is already available.",
            )
        self._repository.create_feature_access_request(owner_subject, feature_key)
        return {"feature_key": feature_key, "state": "REQUESTED"}
