"""`/api/v1` routes with no persistence or evidence arithmetic."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Annotated, Any, cast

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
    FeatureEntitlementPort,
    ImportCommandPort,
    ImportRegistration,
    RunCommandPort,
    RunStart,
    SelfServeAnalysisPort,
    SelfServePort,
    TraceToEvalPort,
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
    reads: BackendReadPort | None,
    imports: ImportCommandPort | None,
    runs: RunCommandPort | None,
    self_serve: SelfServePort | None = None,
    authenticate: Authenticator | None = None,
    feature_entitlements: FeatureEntitlementPort | None = None,
    trace_to_eval: TraceToEvalPort | SelfServeAnalysisPort | None = None,
    local_trace_to_eval_only: bool = False,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    if trace_to_eval is not None and self_serve is None:
        local_analysis = cast(TraceToEvalPort, trace_to_eval)

        @router.post("/trace-to-eval/runs", status_code=201)
        def start_trace_to_eval(
            payload: Annotated[dict[str, Any], Body()],
        ) -> dict[str, Any]:
            manifest_path = payload.get("manifest_path")
            source_path = payload.get("source_path")
            source_kind = payload.get("source_kind")
            manifest_valid = isinstance(manifest_path, str) and bool(
                manifest_path.strip()
            )
            source_valid = (
                isinstance(source_path, str)
                and bool(source_path.strip())
                and isinstance(source_kind, str)
                and bool(source_kind.strip())
            )
            if manifest_valid == source_valid:
                raise HTTPException(status_code=422, detail="select exactly one source")
            try:
                return dict(
                    local_analysis.run(
                        manifest_path if manifest_valid else None,
                        source_path=source_path if source_valid else None,
                        source_kind=source_kind if source_valid else None,
                    )
                )
            except ValueError as error:
                raise HTTPException(
                    status_code=422, detail="trace-to-eval run rejected"
                ) from error

        @router.get("/trace-to-eval/reports/{report_id}")
        def get_trace_to_eval_report(report_id: str) -> dict[str, Any]:
            try:
                return dict(local_analysis.get_report(report_id))
            except KeyError as error:
                raise HTTPException(
                    status_code=404, detail="report not found"
                ) from error
            except ValueError as error:
                raise HTTPException(
                    status_code=409, detail="report integrity failure"
                ) from error

        @router.post("/trace-to-eval/reports/{report_id}/rulings", status_code=201)
        def append_trace_to_eval_ruling(
            report_id: str,
            payload: Annotated[dict[str, Any], Body()],
        ) -> dict[str, Any]:
            try:
                return dict(local_analysis.append_ruling(report_id, payload))
            except KeyError as error:
                raise HTTPException(
                    status_code=404, detail="report not found"
                ) from error
            except ValueError as error:
                raise HTTPException(
                    status_code=422, detail="ruling rejected"
                ) from error

        @router.get("/trace-to-eval/reports/{report_id}/review")
        def get_trace_to_eval_review(report_id: str) -> dict[str, Any]:
            try:
                return dict(local_analysis.get_review_state(report_id))
            except KeyError as error:
                raise HTTPException(
                    status_code=404, detail="report not found"
                ) from error
            except ValueError as error:
                raise HTTPException(
                    status_code=409, detail="review integrity failure"
                ) from error

        @router.get("/trace-to-eval/reports/{report_id}/conversations/{trace_id}")
        def get_trace_to_eval_conversation(
            report_id: str, trace_id: str
        ) -> dict[str, Any]:
            try:
                return dict(local_analysis.get_conversation(report_id, trace_id))
            except KeyError as error:
                raise HTTPException(
                    status_code=404, detail="conversation not found"
                ) from error
            except ValueError as error:
                raise HTTPException(
                    status_code=409, detail="conversation integrity failure"
                ) from error

    if local_trace_to_eval_only:
        if trace_to_eval is None:
            raise ValueError("trace_to_eval is required for local-only routing")
        return router

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

        if feature_entitlements is not None:

            @router.get("/me/features")
            def list_features(
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                return {
                    "schema_version": 1,
                    "features": [
                        dict(feature)
                        for feature in feature_entitlements.list_features(subject)
                    ],
                }

            @router.post("/me/access-requests")
            def request_feature_access(
                payload: Annotated[dict[str, Any], Body()],
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                feature_key = payload.get("feature_key")
                if not isinstance(feature_key, str):
                    from triana_backend.application.self_serve import SelfServeRefusal

                    raise SelfServeRefusal(
                        422, "INVALID_FEATURE_KEY", "Feature key is required."
                    )
                return dict(
                    feature_entitlements.request_feature_access(subject, feature_key)
                )

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
            imported = dict(
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
            if trace_to_eval is None or feature_entitlements is None:
                return imported
            analysis_state = next(
                (
                    str(item.get("state"))
                    for item in feature_entitlements.list_features(subject)
                    if item.get("feature_key") == "ANALYSIS"
                ),
                "LOCKED",
            )
            analysis_run = (
                dict(
                    cast(
                        SelfServeAnalysisPort, trace_to_eval
                    ).start_analysis_for_import(
                        subject, agent_id, str(imported["import_id"])
                    )
                )
                if analysis_state == "AVAILABLE"
                else None
            )
            imported["analysis"] = {
                "feature_state": analysis_state,
                "run": analysis_run,
            }
            return imported

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

        if trace_to_eval is not None:
            owned_analysis = cast(SelfServeAnalysisPort, trace_to_eval)

            @router.get("/agents/{agent_id}/analysis-runs")
            def list_agent_analysis_runs(
                agent_id: str,
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                return {
                    "schema_version": 1,
                    "analysis_runs": [
                        dict(item)
                        for item in owned_analysis.list_agent_analysis_runs(
                            subject, agent_id
                        )
                    ],
                }

            @router.get("/trace-to-eval/reports/{report_id}")
            def get_owned_trace_to_eval_report(
                report_id: str,
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                return dict(owned_analysis.get_owned_report(subject, report_id))

            @router.get("/trace-to-eval/reports/{report_id}/review")
            def get_owned_trace_to_eval_review(
                report_id: str,
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                return dict(owned_analysis.get_owned_review_state(subject, report_id))

            @router.post("/trace-to-eval/reports/{report_id}/rulings", status_code=201)
            def append_owned_trace_to_eval_ruling(
                report_id: str,
                payload: Annotated[dict[str, Any], Body()],
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                server_ruling = {
                    **payload,
                    "report_id": report_id,
                    "reviewer_id": "owner:"
                    + hashlib.sha256(subject.encode("utf-8")).hexdigest()[:24],
                    "ruled_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }
                try:
                    return dict(
                        owned_analysis.append_owned_ruling(
                            subject, report_id, server_ruling
                        )
                    )
                except ValueError as error:
                    raise HTTPException(
                        status_code=422, detail="ruling rejected"
                    ) from error

            @router.get("/trace-to-eval/reports/{report_id}/conversations/{trace_id}")
            def get_owned_trace_to_eval_conversation(
                report_id: str,
                trace_id: str,
                subject: str = Depends(authenticated_subject),
            ) -> dict[str, Any]:
                return dict(
                    owned_analysis.get_owned_conversation(subject, report_id, trace_id)
                )

        return router

    if reads is None or imports is None or runs is None:
        raise ValueError("legacy ports are required")

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
