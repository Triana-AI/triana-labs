"""`/api/v1` routes with no persistence or evidence arithmetic."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, Query

from .contracts import (
    BackendReadPort,
    ImportCommandPort,
    ImportRegistration,
    RunCommandPort,
    RunStart,
)
from .models import ImportRegistrationModel, RunStartModel


def create_v1_router(
    *,
    reads: BackendReadPort,
    imports: ImportCommandPort,
    runs: RunCommandPort,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post("/imports", status_code=200)
    def register_import(
        payload: Annotated[ImportRegistrationModel, Body()],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    ) -> dict[str, Any]:
        result = imports.register_import(
            ImportRegistration(
                workspace_slug=payload.workspace_slug,
                agent_key=payload.agent_key,
                version_key=payload.version_key,
                source_bucket=payload.source.bucket,
                source_key=payload.source.key,
                source_sha256=payload.source.sha256,
                evidence_class=payload.evidence_class,
                idempotency_key=idempotency_key,
            )
        )
        return dict(result)

    @router.get("/imports/{import_id}")
    def get_import(import_id: str) -> dict[str, Any]:
        return dict(reads.get_import(import_id))

    @router.get("/imports/{import_id}/records/{record_id}")
    def get_import_record(import_id: str, record_id: str) -> dict[str, Any]:
        return dict(reads.get_import_record(import_id, record_id))

    @router.post("/runs", status_code=200)
    def start_run(
        payload: Annotated[RunStartModel, Body()],
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    ) -> dict[str, Any]:
        result = runs.start_or_get_run(
            RunStart(
                import_id=payload.import_id,
                idempotency_key=idempotency_key,
                rerun=payload.rerun,
            )
        )
        return dict(result)

    @router.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        return dict(reads.get_run(run_id))

    @router.get("/agents")
    def list_agents() -> dict[str, Any]:
        return {
            "schema_version": 1,
            "agents": [dict(item) for item in reads.list_agents()],
        }

    @router.get("/agents/{agent_id}/versions")
    def list_agent_versions(
        agent_id: str,
        limit: Annotated[int, Query(ge=1, le=200)] = 100,
    ) -> dict[str, Any]:
        # The repository owns deterministic ordering; slicing cannot reorder it.
        versions = reads.list_agent_versions(agent_id)
        return {
            "schema_version": 1,
            "agent_id": agent_id,
            "versions": [dict(item) for item in versions[:limit]],
        }

    @router.get("/reports/{report_id}")
    def get_report(report_id: str) -> dict[str, Any]:
        # Return the immutable canonical artifact directly, without an envelope.
        return dict(reads.get_report(report_id))

    @router.get("/conversations/{conversation_id}")
    def get_conversation(conversation_id: str) -> dict[str, Any]:
        return dict(reads.get_conversation(conversation_id))

    return router
