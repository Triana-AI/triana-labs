"""`/api/v1` routes with no persistence or evidence arithmetic."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
)

from .contracts import (
    Authenticator,
    BackendReadPort,
    ImportCommandPort,
    ImportRegistration,
    RunCommandPort,
    RunStart,
    SelfServePort,
)
from .models import AgentCreateModel, ImportRegistrationModel, RunStartModel

_MAX_MULTIPART_UPLOAD_BYTES = 16 * 1024 * 1024


async def _read_bounded_upload(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    byte_count = 0
    while chunk := await file.read(1024 * 1024):
        byte_count += len(chunk)
        if byte_count > _MAX_MULTIPART_UPLOAD_BYTES:
            from triana_backend.application.self_serve import SelfServeRefusal

            raise SelfServeRefusal(
                413, "UPLOAD_TOO_LARGE", "Upload exceeds the size limit."
            )
        chunks.append(chunk)
    return b"".join(chunks)


def create_v1_router(
    *,
    reads: BackendReadPort,
    imports: ImportCommandPort,
    runs: RunCommandPort,
    self_serve: SelfServePort | None = None,
    authenticate: Authenticator | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    if self_serve is not None:
        if authenticate is None:
            raise ValueError("authenticate is required when self_serve is configured")

        def authenticated_subject(
            authorization: Annotated[str | None, Header()] = None,
        ) -> str:
            scheme, _, token = (authorization or "").partition(" ")
            subject = authenticate(token if scheme.lower() == "bearer" else None)
            if subject is None:
                raise HTTPException(status_code=401, detail="invalid authentication")
            return subject

        @router.get("/me")
        def get_me(subject: str = Depends(authenticated_subject)) -> dict[str, Any]:
            return dict(self_serve.get_or_create_me(subject))

        @router.post("/agents", status_code=201)
        def create_agent(
            payload: Annotated[AgentCreateModel, Body()],
            subject: str = Depends(authenticated_subject),
        ) -> dict[str, Any]:
            return dict(self_serve.create_agent(subject, payload.display_name.strip()))

        @router.get("/agents")
        def list_self_serve_agents(
            subject: str = Depends(authenticated_subject),
        ) -> dict[str, Any]:
            return {
                "schema_version": 1,
                "agents": [dict(row) for row in self_serve.list_agents(subject)],
            }

        @router.get("/agents/{agent_id}")
        def get_self_serve_agent(
            agent_id: str, subject: str = Depends(authenticated_subject)
        ) -> dict[str, Any]:
            return dict(self_serve.get_agent(subject, agent_id))

        @router.post("/agents/{agent_id}/imports", status_code=201)
        async def create_self_serve_import(
            agent_id: str,
            idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
            owner_attested: Annotated[bool, Form()],
            file: Annotated[UploadFile, File()],
            subject: str = Depends(authenticated_subject),
        ) -> dict[str, Any]:
            return dict(
                self_serve.create_import(
                    subject,
                    agent_id,
                    filename=file.filename or "",
                    content_type=file.content_type or "",
                    payload=await _read_bounded_upload(file),
                    owner_attested=owner_attested,
                    idempotency_key=idempotency_key,
                )
            )

        @router.get("/agents/{agent_id}/imports")
        def list_self_serve_imports(
            agent_id: str, subject: str = Depends(authenticated_subject)
        ) -> dict[str, Any]:
            return {
                "schema_version": 1,
                "imports": [
                    dict(row)
                    for row in self_serve.list_agent_imports(subject, agent_id)
                ],
            }

        @router.get("/imports/{import_id}")
        def get_self_serve_import(
            import_id: str, subject: str = Depends(authenticated_subject)
        ) -> dict[str, Any]:
            return dict(self_serve.get_import(subject, import_id))

        @router.get("/imports/{import_id}/conversations")
        def list_self_serve_conversations(
            import_id: str, subject: str = Depends(authenticated_subject)
        ) -> dict[str, Any]:
            return {
                "schema_version": 1,
                "conversations": [
                    dict(row)
                    for row in self_serve.list_import_conversations(subject, import_id)
                ],
            }

        @router.get("/imports/{import_id}/rejections")
        def list_self_serve_rejections(
            import_id: str, subject: str = Depends(authenticated_subject)
        ) -> dict[str, Any]:
            return {
                "schema_version": 1,
                "rejections": [
                    dict(row)
                    for row in self_serve.list_import_rejections(subject, import_id)
                ],
            }

        @router.get("/conversations/{conversation_id}")
        def get_self_serve_conversation(
            conversation_id: str,
            subject: str = Depends(authenticated_subject),
        ) -> dict[str, Any]:
            return dict(self_serve.get_conversation(subject, conversation_id))

        return router

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
