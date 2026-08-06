"""Production PostgreSQL/S3 composition for legacy and self-serve surfaces."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, BinaryIO, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dbos import DBOS, DBOSConfig
from sqlalchemy import Engine, create_engine, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker
from triana_labs.report import compile_hrai_normalized_trace_v2

from triana_backend.api import create_app
from triana_backend.api.contracts import (
    Availability,
    BackendReadPort,
    ImportCommandPort,
    ImportRegistration,
    IntegrityConflict,
    JsonObject,
    ResourceNotFound,
    ResourceUnavailable,
    RunCommandPort,
    RunStart,
)
from triana_backend.application.imports import ImportService, RegisterS3Import
from triana_backend.application.self_serve import SelfServeService
from triana_backend.artifacts.s3 import S3ArtifactStore
from triana_backend.auth import OidcJwtAuthenticator
from triana_backend.config import BackendSettings
from triana_backend.domain.models import (
    ArtifactAvailability,
    ArtifactKind,
    ArtifactRef,
    BoundaryError,
    EvidenceClass,
    ImportRequest,
    canonical_json,
    deterministic_id,
)
from triana_backend.domain.parser import HRAI_NORMALIZED_TRACE_V2
from triana_backend.persistence.models import (
    Agent,
    AgentVersion,
    AnalysisFact,
    Artifact,
    Import,
    Report,
    Run,
    RunArtifact,
    Workspace,
)
from triana_backend.persistence.repositories import SqlAlchemyImportRepository
from triana_backend.persistence.self_serve import SqlAlchemySelfServeRepository
from triana_backend.services.report_projection import (
    PersistedLabsFact,
    ReportProjectionInput,
    canonical_report_bytes,
    project_labs_report,
)
from triana_backend.workflows import DBOSForegroundExecutor, configure_workflow_services
from triana_backend.workflows.contracts import ImportRunRequest, WorkflowServices
from triana_backend.workflows.identity import workflow_id_for


class PostgresS3Reads(BackendReadPort):
    def __init__(
        self, *, sessions: sessionmaker[Session], artifacts: S3ArtifactStore
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts

    def ready(self) -> bool:
        try:
            with self._sessions() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_report(self, report_id: str) -> JsonObject:
        with self._sessions() as session:
            report = session.get(Report, report_id)
            if report is None:
                raise ResourceNotFound("report", report_id)
            artifact = session.get(Artifact, report.artifact_id)
            if artifact is None:
                raise ResourceUnavailable(
                    "report", report_id, Availability.DEGRADED_ARTIFACT_MISSING
                )
            run_id = report.run_id
            expected_hash = report.report_hash
            ref = _artifact_ref(artifact)
        try:
            availability = self._artifacts.head(ref)
        except (BotoCoreError, ClientError) as error:
            raise ResourceUnavailable(
                "report",
                report_id,
                Availability.UNAVAILABLE,
                "ARTIFACT_STORE_UNAVAILABLE",
            ) from error
        if availability is not ArtifactAvailability.AVAILABLE:
            raise ResourceUnavailable(
                "report",
                report_id,
                Availability.DEGRADED_ARTIFACT_MISSING,
                "ARTIFACT_MISSING"
                if availability is ArtifactAvailability.MISSING
                else "ARTIFACT_INTEGRITY_FAILED",
            )
        body = _read_json_object(
            self._artifacts.open_verified(ref),
            "report",
            report_id,
            expected_sha256=ref.content_sha256,
        )
        body_run = body.get("run")
        body_run_id = (
            body_run.get("run_id") if isinstance(body_run, dict) else body.get("run_id")
        )
        if (
            body.get("report_id") != report_id
            or body_run_id != run_id
            or ref.content_sha256 != expected_hash
        ):
            raise IntegrityConflict("report", report_id)
        return body

    def get_import(self, import_id: str) -> JsonObject:
        with self._sessions() as session:
            row = session.get(Import, import_id)
            if row is None:
                raise ResourceNotFound("import", import_id)
            return {
                "schema_version": 1,
                "import_id": row.id,
                "artifact_id": row.source_artifact_id,
                "evidence_class": row.evidence_class,
                "source_sha256": row.source_sha256,
                "physical_record_count": row.physical_record_count,
                "usable_conversation_count": row.usable_conversation_count,
                "source_status_counts": dict(row.source_status_counts),
                "rejected_record_count": row.rejected_record_count,
                "rejection_summary": dict(row.rejection_summary),
                "status": row.status,
            }

    def get_import_record(self, import_id: str, record_id: str) -> JsonObject:
        with self._sessions() as session:
            imported = session.get(Import, import_id)
            if imported is None:
                raise ResourceNotFound("import", import_id)
            artifact = session.get(Artifact, imported.source_artifact_id)
            if artifact is None:
                raise ResourceUnavailable(
                    "import", import_id, Availability.DEGRADED_ARTIFACT_MISSING
                )
            ref = _artifact_ref(artifact)
            evidence_class = imported.evidence_class
            source_sha256 = imported.source_sha256
        try:
            source = self._artifacts.open_verified(ref)
        except (BoundaryError, BotoCoreError, ClientError) as error:
            code = (
                error.code
                if isinstance(error, BoundaryError)
                else "ARTIFACT_STORE_UNAVAILABLE"
            )
            raise ResourceUnavailable(
                "import", import_id, Availability.DEGRADED_ARTIFACT_MISSING, code
            ) from error
        record = _find_jsonl_record(source, record_id)
        if record is None:
            raise ResourceNotFound("record", record_id)
        return {
            "schema_version": 1,
            "availability": Availability.AVAILABLE.value,
            "import_id": import_id,
            "source_artifact_sha256": source_sha256,
            "record_id": record_id,
            "evidence_class": evidence_class,
            "record": record,
        }

    def get_conversation(self, conversation_id: str) -> JsonObject:
        with self._sessions() as session:
            reports = tuple(
                session.scalars(
                    select(Report)
                    .where(Report.status.in_(("COMPLETED", "COMPLETED_WITH_GAPS")))
                    .order_by(Report.id)
                ).all()
            )
        unavailable = 0
        for report in reports:
            try:
                body = self.get_report(report.id)
            except (ResourceUnavailable, IntegrityConflict):
                unavailable += 1
                continue
            conversations = body.get("conversations", [])
            if not isinstance(conversations, list):
                unavailable += 1
                continue
            for conversation in conversations:
                if (
                    isinstance(conversation, dict)
                    and conversation.get("conversation_id") == conversation_id
                ):
                    return {
                        "schema_version": 1,
                        "availability": Availability.AVAILABLE.value,
                        "report_id": report.id,
                        "report_hash": hashlib.sha256(
                            canonical_report_bytes(body)
                        ).hexdigest(),
                        "conversation": conversation,
                    }
        if reports and unavailable == len(reports):
            raise ResourceUnavailable(
                "conversation",
                conversation_id,
                Availability.DEGRADED_ARTIFACT_MISSING,
            )
        raise ResourceNotFound("conversation", conversation_id)

    def get_run(self, run_id: str) -> JsonObject:
        with self._sessions() as session:
            run = session.get(Run, run_id)
            if run is None:
                raise ResourceNotFound("run", run_id)
            report_id = session.scalar(select(Report.id).where(Report.run_id == run.id))
            return {
                "schema_version": 1,
                "run_id": run.id,
                "workflow_id": run.workflow_id,
                "import_id": run.import_id,
                "attempt_number": run.attempt_number,
                "status": run.status,
                "report_id": report_id,
            }

    def list_agents(self) -> Sequence[JsonObject]:
        with self._sessions() as session:
            rows = session.execute(
                select(Agent, Workspace)
                .join(Workspace, Workspace.id == Agent.workspace_id)
                .order_by(Workspace.slug, Agent.agent_key, Agent.id)
            ).all()
            return tuple(
                {
                    "agent_id": agent.id,
                    "agent_key": agent.agent_key,
                    "workspace_slug": workspace.slug,
                }
                for agent, workspace in rows
            )

    def list_agent_versions(self, agent_id: str) -> Sequence[JsonObject]:
        with self._sessions() as session:
            if session.get(Agent, agent_id) is None:
                raise ResourceNotFound("agent", agent_id)
            rows = session.scalars(
                select(AgentVersion)
                .where(AgentVersion.agent_id == agent_id)
                .order_by(AgentVersion.version_key, AgentVersion.id)
            ).all()
            return tuple(
                {
                    "agent_version_id": row.id,
                    "version_key": row.version_key,
                    "source_commit": row.source_commit,
                    "config_identity": row.config_identity,
                }
                for row in rows
            )


class PostgresS3Imports(ImportCommandPort):
    def __init__(
        self, *, sessions: sessionmaker[Session], artifacts: S3ArtifactStore
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts

    def register_import(self, request: ImportRegistration) -> JsonObject:
        try:
            evidence_class = EvidenceClass(request.evidence_class)
        except ValueError as error:
            raise IntegrityConflict("evidence_class", request.evidence_class) from error
        try:
            with self._sessions() as session:
                result = ImportService(
                    artifacts=self._artifacts,
                    registry=SqlAlchemyImportRepository(session),
                ).register_s3(
                    RegisterS3Import(
                        bucket=request.source_bucket,
                        key=request.source_key,
                        expected_sha256=request.source_sha256,
                        request=ImportRequest(
                            workspace_slug=request.workspace_slug,
                            agent_key=request.agent_key,
                            version_key=request.version_key,
                            evidence_class=evidence_class,
                            parser_version=HRAI_NORMALIZED_TRACE_V2,
                            idempotency_key=request.idempotency_key,
                        ),
                    )
                )
        except BoundaryError as error:
            raise IntegrityConflict(
                "import", request.idempotency_key, error.code
            ) from error
        return {
            "schema_version": 1,
            "artifact_id": result.artifact_id,
            "import_id": result.import_id,
            "created": result.created,
            "physical_record_count": result.parsed.physical_record_count,
            "usable_conversation_count": result.parsed.usable_conversation_count,
            "source_status_counts": dict(result.parsed.source_status_counts),
        }


class PostgresWorkflowServices(WorkflowServices):
    """Replay-safe DBOS effects backed by deterministic IDs and immutable S3."""

    def __init__(
        self, *, sessions: sessionmaker[Session], artifacts: S3ArtifactStore
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts

    def mark_running(
        self, workflow_id: str, request: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        parsed = _workflow_request(request)
        if workflow_id_for(parsed) != workflow_id:
            raise IntegrityConflict("workflow", workflow_id)
        run_id = _run_id(parsed)
        with self._sessions() as session, session.begin():
            run = session.get(Run, run_id)
            if run is None or run.workflow_id != workflow_id:
                raise IntegrityConflict("workflow", workflow_id)
            if run.status not in {"COMPLETED", "COMPLETED_WITH_GAPS"}:
                run.status = "RUNNING"
                run.started_at = run.started_at or datetime.now(UTC)
        return {"run_id": run_id}

    def execute_labs_analysis(self, run_id: str) -> Mapping[str, Any]:
        with self._sessions() as session:
            run = session.get(Run, run_id)
            if run is None:
                raise ResourceNotFound("run", run_id)
            imported = session.get(Import, run.import_id)
            if imported is None:
                raise ResourceNotFound("import", run.import_id)
            source_row = session.get(Artifact, imported.source_artifact_id)
            if source_row is None:
                raise ResourceUnavailable(
                    "import", imported.id, Availability.DEGRADED_ARTIFACT_MISSING
                )
            source_ref = _artifact_ref(source_row)
            evidence_class = imported.evidence_class
            expected_sha256 = imported.source_sha256
        source = self._artifacts.open_verified(source_ref)
        try:
            source_bytes = source.read()
        finally:
            source.close()
        compiled = compile_hrai_normalized_trace_v2(
            source_bytes,
            evidence_class=evidence_class,
            expected_sha256=expected_sha256,
        )
        payload = canonical_json(cast(dict[str, Any], compiled.to_mapping()))
        ref = self._artifacts.publish_bytes(
            payload=payload,
            kind=ArtifactKind.LABS_ANALYSIS_FACTS,
            media_type="application/json",
        )
        with self._sessions() as session, session.begin():
            _persist_artifact(session, ref)
            _link_artifact(session, run_id, ref.id, "LABS_ANALYSIS_FACTS")
        return {"analysis_result_id": ref.id}

    def persist_labs_result(
        self, run_id: str, analysis_result_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        artifact_id = _only_ref(analysis_result_ref, "analysis_result_id")
        with self._sessions() as session:
            row = session.get(Artifact, artifact_id)
            run = session.get(Run, run_id)
            if row is None or run is None:
                raise ResourceNotFound("analysis_result", artifact_id)
            imported = session.get(Import, run.import_id)
            if imported is None:
                raise ResourceNotFound("import", run.import_id)
            ref = _artifact_ref(row)
            source_sha256 = imported.source_sha256
        analysis = _read_json_object(
            self._artifacts.open_verified(ref), "analysis_result", artifact_id
        )
        if analysis.get("source_sha256") != source_sha256:
            raise IntegrityConflict("analysis_result", artifact_id)
        facts = analysis.get("facts")
        rejected = analysis.get("rejected_evidence")
        result_hash = analysis.get("result_hash")
        if (
            not isinstance(facts, list)
            or not isinstance(rejected, list)
            or not isinstance(result_hash, str)
        ):
            raise IntegrityConflict("analysis_result", artifact_id)
        rejection_count = len(rejected)
        rows = [
            *facts,
            _supplemental_fact("rejected_evidence", rejected, result_hash),
            _supplemental_fact("rejected_record_count", rejection_count, result_hash),
            _supplemental_fact(
                "rejection_summary",
                {"SOURCE_EXECUTION_INCOMPLETE": rejection_count},
                result_hash,
            ),
        ]
        with self._sessions() as session, session.begin():
            for value in rows:
                if not isinstance(value, dict):
                    raise IntegrityConflict("analysis_result", artifact_id)
                fact_id = str(value["fact_id"])
                fact_row = AnalysisFact(
                    id=deterministic_id("af", {"run_id": run_id, "fact_id": fact_id}),
                    run_id=run_id,
                    fact_id=fact_id,
                    fact_kind=str(value["fact_kind"]),
                    schema_version=int(value["schema_version"]),
                    value_json=value["value"],
                    authority=str(value["authority"]),
                    lineage_json={
                        "source_sha256": source_sha256,
                        "compiler_version": analysis["compiler_version"],
                        "compiler_result_hash": result_hash,
                        "analysis_artifact_id": artifact_id,
                    },
                )
                statement = (
                    insert(cast(Any, AnalysisFact.__table__))
                    .values(
                        id=fact_row.id,
                        run_id=fact_row.run_id,
                        fact_id=fact_row.fact_id,
                        fact_kind=fact_row.fact_kind,
                        schema_version=fact_row.schema_version,
                        value_json=fact_row.value_json,
                        authority=fact_row.authority,
                        lineage_json=fact_row.lineage_json,
                    )
                    .on_conflict_do_nothing(index_elements=["run_id", "fact_id"])
                )
                session.execute(statement)
        return {"fact_set_id": artifact_id}

    def project_stored_report(
        self, run_id: str, persisted_fact_set_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        artifact_id = _only_ref(persisted_fact_set_ref, "fact_set_id")
        with self._sessions() as session:
            run = session.get(Run, run_id)
            analysis_row = session.get(Artifact, artifact_id)
            if run is None or analysis_row is None:
                raise ResourceNotFound("run", run_id)
            imported = session.get(Import, run.import_id)
            if imported is None:
                raise ResourceNotFound("import", run.import_id)
            fact_rows = session.scalars(
                select(AnalysisFact).where(AnalysisFact.run_id == run_id)
            ).all()
            created_at = (run.started_at or run.created_at).astimezone(UTC).isoformat()
            analysis_ref = _artifact_ref(analysis_row)
        analysis = _read_json_object(
            self._artifacts.open_verified(analysis_ref), "analysis_result", artifact_id
        )
        rejected = analysis.get("rejected_evidence")
        result_hash = analysis.get("result_hash")
        compiler_version = analysis.get("compiler_version")
        if (
            not isinstance(rejected, list)
            or not isinstance(result_hash, str)
            or not isinstance(compiler_version, str)
        ):
            raise IntegrityConflict("analysis_result", artifact_id)
        report_id = deterministic_id("rpt", {"run_id": run_id, "schema_version": 1})
        report = project_labs_report(
            ReportProjectionInput(
                report_id=report_id,
                run_id=run_id,
                evidence_class=imported.evidence_class,
                source_sha256=imported.source_sha256,
                created_at=created_at,
                compiler_version=compiler_version,
                compiler_result_hash=result_hash,
                analysis_artifact_sha256=analysis_ref.content_sha256,
                conversations=(),
                gaps=({"reason_code": "SEMANTIC_ANALYSIS_NOT_RUN"},),
                facts=tuple(
                    PersistedLabsFact(
                        fact_id=row.fact_id,
                        fact_kind=row.fact_kind,
                        value=row.value_json,
                        authority=row.authority,
                        schema_version=row.schema_version,
                    )
                    for row in fact_rows
                    if row.fact_kind != "rejected_evidence"
                ),
                rejected_evidence=tuple(cast(list[dict[str, Any]], rejected)),
            )
        )
        payload = canonical_report_bytes(report)
        ref = self._artifacts.publish_bytes(
            payload=payload,
            kind=ArtifactKind.LABS_REPORT,
            media_type="application/json",
        )
        with self._sessions() as session, session.begin():
            _persist_artifact(session, ref)
            _link_artifact(session, run_id, ref.id, "CANONICAL_REPORT")
            report_row = Report(
                id=report_id,
                run_id=run_id,
                artifact_id=ref.id,
                projection_schema_version=1,
                report_hash=ref.content_sha256,
                status="COMPLETED_WITH_GAPS",
            )
            statement = (
                insert(cast(Any, Report.__table__))
                .values(
                    id=report_row.id,
                    run_id=report_row.run_id,
                    artifact_id=report_row.artifact_id,
                    projection_schema_version=report_row.projection_schema_version,
                    report_hash=report_row.report_hash,
                    status=report_row.status,
                )
                .on_conflict_do_nothing(
                    index_elements=["run_id", "projection_schema_version"]
                )
            )
            session.execute(statement)
            stored = session.get(Report, report_id)
            if stored is not None and (
                stored.artifact_id != ref.id or stored.report_hash != ref.content_sha256
            ):
                raise IntegrityConflict("report", report_id)
        return {"report_id": report_id}

    def complete_run(
        self, run_id: str, report_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        report_id = _only_ref(report_ref, "report_id")
        with self._sessions() as session, session.begin():
            run = session.get(Run, run_id)
            report = session.get(Report, report_id)
            if run is None or report is None or report.run_id != run_id:
                raise IntegrityConflict("run", run_id)
            run.status = "COMPLETED_WITH_GAPS"
            run.finished_at = run.finished_at or datetime.now(UTC)
            return {
                "workflow_id": run.workflow_id,
                "run_id": run.id,
                "report_id": report.id,
                "attempt_number": run.attempt_number,
                "status": run.status,
            }


class PostgresDBOSRuns(RunCommandPort):
    def __init__(
        self,
        *,
        sessions: sessionmaker[Session],
        executor: DBOSForegroundExecutor,
        labs_version: str,
        config_identity: str,
    ) -> None:
        self._sessions = sessions
        self._executor = executor
        self._labs_version = labs_version
        self._config_identity = config_identity

    def start_or_get_run(self, request: RunStart) -> JsonObject:
        base_identity = _run_request_identity(
            import_id=request.import_id,
            labs_version=self._labs_version,
            config_identity=self._config_identity,
        )
        workflow_config = (
            _rerun_config_identity(self._config_identity, request.idempotency_key)
            if request.rerun
            else self._config_identity
        )
        with self._sessions() as session, session.begin():
            imported = session.get(Import, request.import_id)
            if imported is None:
                raise ResourceNotFound("import", request.import_id)
            # Serialize attempt allocation on the stable request identity.
            session.execute(
                select(func.pg_advisory_xact_lock(func.hashtext(base_identity)))
            )
            existing = session.scalars(
                select(Run)
                .where(Run.request_identity == base_identity)
                .order_by(Run.attempt_number)
            ).all()
            attempt = 1
            if request.rerun:
                matching = next(
                    (
                        row
                        for row in existing
                        if row.workflow_id
                        == workflow_id_for(
                            ImportRunRequest(
                                import_id=request.import_id,
                                request_identity=base_identity,
                                attempt_number=row.attempt_number,
                                labs_version=self._labs_version,
                                config_identity=workflow_config,
                            )
                        )
                    ),
                    None,
                )
                attempt = (
                    matching.attempt_number
                    if matching is not None
                    else max((row.attempt_number for row in existing), default=0) + 1
                )
            workflow_request = ImportRunRequest(
                import_id=request.import_id,
                request_identity=base_identity,
                attempt_number=attempt,
                labs_version=self._labs_version,
                config_identity=workflow_config,
            )
            workflow_id = workflow_id_for(workflow_request)
            run_id = _run_id(workflow_request)
            session.execute(
                insert(cast(Any, Run.__table__))
                .values(
                    id=run_id,
                    import_id=imported.id,
                    agent_version_id=imported.agent_version_id,
                    workflow_id=workflow_id,
                    request_identity=base_identity,
                    attempt_number=attempt,
                    labs_version=self._labs_version,
                    status="PENDING",
                )
                .on_conflict_do_nothing(index_elements=["workflow_id"])
            )
        receipt = self._executor.start_or_get(workflow_request)
        return {
            "schema_version": 1,
            "workflow_id": receipt.workflow_id,
            "run_id": receipt.run_id,
            "report_id": receipt.report_id,
            "attempt_number": receipt.attempt_number,
            "status": receipt.status,
        }


@dataclass(slots=True)
class BackendRuntime:
    app: Any
    engine: Engine

    def close(self) -> None:
        DBOS.destroy()
        self.engine.dispose()


def compose_backend(
    settings: BackendSettings, *, launch_dbos: bool = True
) -> BackendRuntime:
    engine = create_engine(_sqlalchemy_url(settings.database_url), pool_pre_ping=True)
    sessions = sessionmaker(engine, expire_on_commit=False)
    artifacts = S3ArtifactStore(
        client=boto3.client("s3", region_name=settings.aws_region),
        artifact_bucket=settings.artifact_bucket,
        kms_key_id=settings.kms_key_id,
    )
    if settings.oidc_issuer is None:
        if settings.dbos_system_database_url is None:
            raise ValueError("DBOS system database is required for the legacy runtime")
        services = PostgresWorkflowServices(sessions=sessions, artifacts=artifacts)
        configure_workflow_services(services)
        dbos_config: DBOSConfig = {
            "name": "triana-backend",
            "system_database_url": settings.dbos_system_database_url,
            "application_database_url": settings.database_url,
            "application_version": settings.labs_version,
        }
        DBOS(config=dbos_config)
        if launch_dbos:
            DBOS.launch()
    reads = PostgresS3Reads(sessions=sessions, artifacts=artifacts)
    self_serve = None
    authenticate = None
    if settings.oidc_issuer is not None:
        if settings.oidc_audience is None or settings.oidc_jwks_url is None:
            raise ValueError("OIDC settings must be configured together")
        self_serve = SelfServeService(
            repository=SqlAlchemySelfServeRepository(sessions), storage=artifacts
        )
        authenticate = OidcJwtAuthenticator(
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            jwks_url=settings.oidc_jwks_url,
        )
    return BackendRuntime(
        app=create_app(
            reads=reads,
            imports=PostgresS3Imports(sessions=sessions, artifacts=artifacts),
            runs=PostgresDBOSRuns(
                sessions=sessions,
                executor=DBOSForegroundExecutor(),
                labs_version=settings.labs_version,
                config_identity=settings.labs_config_identity,
            ),
            readiness=reads.ready,
            self_serve=self_serve,
            authenticate=authenticate,
        ),
        engine=engine,
    )


def _persist_artifact(session: Session, ref: ArtifactRef) -> None:
    session.execute(
        insert(cast(Any, Artifact.__table__))
        .values(
            id=ref.id,
            artifact_kind=ref.kind.value,
            content_sha256=ref.content_sha256,
            byte_count=ref.byte_count,
            media_type=ref.media_type,
            storage_backend="S3",
            storage_bucket=ref.storage_bucket,
            storage_key=ref.storage_key,
            kms_key_id=ref.kms_key_id,
            checksum_sha256_b64=ref.checksum_sha256_b64,
            availability="AVAILABLE",
        )
        .on_conflict_do_nothing(index_elements=["artifact_kind", "content_sha256"])
    )


def _link_artifact(session: Session, run_id: str, artifact_id: str, role: str) -> None:
    link = RunArtifact(
        run_id=run_id,
        artifact_id=artifact_id,
        artifact_role=role,
    )
    session.execute(
        insert(cast(Any, RunArtifact.__table__))
        .values(
            run_id=link.run_id,
            artifact_id=link.artifact_id,
            artifact_role=link.artifact_role,
        )
        .on_conflict_do_nothing()
    )


def _workflow_request(request: Mapping[str, Any]) -> ImportRunRequest:
    return ImportRunRequest(
        import_id=str(request["import_id"]),
        request_identity=str(request["request_identity"]),
        attempt_number=int(request["attempt_number"]),
        labs_version=str(request["labs_version"]),
        config_identity=str(request["config_identity"]),
        provider_identity=(
            None
            if request.get("provider_identity") is None
            else str(request["provider_identity"])
        ),
    )


def _run_id(request: ImportRunRequest) -> str:
    return deterministic_id(
        "run",
        {
            "request_identity": request.request_identity,
            "attempt_number": request.attempt_number,
        },
    )


def _only_ref(value: Mapping[str, Any], key: str) -> str:
    if set(value) != {key} or not isinstance(value[key], str) or not value[key]:
        raise IntegrityConflict("workflow_reference", key)
    return str(value[key])


def _supplemental_fact(kind: str, value: Any, result_hash: str) -> dict[str, Any]:
    return {
        "fact_id": deterministic_id(
            "fact", {"compiler_result_hash": result_hash, "fact_kind": kind}
        ),
        "fact_kind": kind,
        "value": value,
        "authority": "DETERMINISTIC",
        "schema_version": 1,
    }


def _sqlalchemy_url(value: str) -> str:
    if value.startswith("postgresql+psycopg://"):
        return value
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    raise ValueError("TRIANA_DATABASE_URL must use PostgreSQL")


def _artifact_ref(row: Artifact) -> ArtifactRef:
    try:
        kind = ArtifactKind(row.artifact_kind)
    except ValueError as error:
        raise IntegrityConflict("artifact", row.id) from error
    return ArtifactRef(
        id=row.id,
        kind=kind,
        content_sha256=row.content_sha256,
        byte_count=row.byte_count,
        media_type=row.media_type,
        storage_bucket=row.storage_bucket,
        storage_key=row.storage_key,
        kms_key_id=row.kms_key_id,
        checksum_sha256_b64=row.checksum_sha256_b64,
    )


def _read_json_object(
    stream: BinaryIO,
    kind: str,
    identity: str,
    *,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    try:
        raw = stream.read()
    finally:
        stream.close()
    if expected_sha256 is not None:
        actual_sha256 = hashlib.sha256(raw).hexdigest()
        if actual_sha256 != expected_sha256:
            raise IntegrityConflict(kind, identity)
    value: Any = json.loads(raw)
    if not isinstance(value, dict):
        raise IntegrityConflict(kind, identity)
    return cast(dict[str, Any], value)


def _find_jsonl_record(stream: BinaryIO, record_id: str) -> dict[str, Any] | None:
    try:
        for raw_line in stream:
            value: Any = json.loads(raw_line)
            if isinstance(value, dict) and value.get("case_id") == record_id:
                return cast(dict[str, Any], value)
    finally:
        stream.close()
    return None


def _run_request_identity(
    *, import_id: str, labs_version: str, config_identity: str
) -> str:
    return deterministic_id(
        "req",
        {
            "import_id": import_id,
            "labs_version": labs_version,
            "config_identity": config_identity,
            "provider_identity": None,
        },
    )


def _rerun_config_identity(config_identity: str, idempotency_key: str) -> str:
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    return f"{config_identity}:explicit-rerun:{digest}"
