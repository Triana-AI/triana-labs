"""Production composition for the private PostgreSQL/S3 LABS-08 backend.

This module joins existing ports.  It deliberately does not compile Labs facts:
that compiler is a separate canonical product boundary and is not present yet.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, BinaryIO, NoReturn, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dbos import DBOS, DBOSConfig
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from triana_backend.api import create_app
from triana_backend.api.contracts import (
    AnalysisNotReady,
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
from triana_backend.artifacts.s3 import S3ArtifactStore
from triana_backend.config import BackendSettings
from triana_backend.domain.models import (
    ArtifactAvailability,
    ArtifactKind,
    ArtifactRef,
    BoundaryError,
    EvidenceClass,
    ImportRequest,
    deterministic_id,
)
from triana_backend.domain.parser import HRAI_NORMALIZED_TRACE_V2
from triana_backend.persistence.models import (
    Agent,
    AgentVersion,
    Artifact,
    Import,
    Report,
    Run,
    Workspace,
)
from triana_backend.persistence.repositories import SqlAlchemyImportRepository
from triana_backend.workflows import DBOSForegroundExecutor, configure_workflow_services
from triana_backend.workflows.contracts import ImportRunRequest, WorkflowServices
from triana_backend.workflows.identity import workflow_id_for


class CanonicalLabsCompilerUnavailable:
    """Stable refusal until a canonical Labs fact compiler is integrated."""

    @property
    def available(self) -> bool:
        return False

    def refuse(self) -> NoReturn:
        raise AnalysisNotReady()


class PostgresS3Reads(BackendReadPort):
    def __init__(
        self,
        *,
        sessions: sessionmaker[Session],
        artifacts: S3ArtifactStore,
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts

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
        return _read_json_object(
            self._artifacts.open_verified(ref), "report", report_id
        )

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
                "import",
                import_id,
                Availability.DEGRADED_ARTIFACT_MISSING,
                code,
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
        # Conversations are immutable members of canonical report artifacts.
        # The demo has a bounded report set, so a deterministic ID-ordered scan
        # is preferable to adding an unfrozen persistence table.
        with self._sessions() as session:
            rows = session.scalars(
                select(Report)
                .where(Report.status.in_(("COMPLETED", "COMPLETED_WITH_GAPS")))
                .order_by(Report.id)
            ).all()
        for report in rows:
            body = self.get_report(report.id)
            conversations = body.get("conversations", [])
            if not isinstance(conversations, list):
                raise IntegrityConflict("report", report.id)
            for conversation in conversations:
                if (
                    isinstance(conversation, dict)
                    and conversation.get("conversation_id") == conversation_id
                ):
                    return {
                        "schema_version": 1,
                        "availability": Availability.AVAILABLE.value,
                        "report_id": report.id,
                        "report_hash": report.report_hash,
                        "conversation": conversation,
                    }
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
        self,
        *,
        sessions: sessionmaker[Session],
        artifacts: S3ArtifactStore,
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
    """RDS workflow effects; analysis remains a typed unavailable boundary."""

    def __init__(
        self,
        *,
        sessions: sessionmaker[Session],
        compiler: CanonicalLabsCompilerUnavailable,
    ) -> None:
        self._sessions = sessions
        self._compiler = compiler

    def mark_running(
        self, workflow_id: str, request: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        parsed = ImportRunRequest(
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
        if workflow_id_for(parsed) != workflow_id:
            raise IntegrityConflict("workflow", workflow_id)
        run_id = deterministic_id(
            "run",
            {
                "request_identity": parsed.request_identity,
                "attempt_number": parsed.attempt_number,
            },
        )
        with self._sessions() as session, session.begin():
            imported = session.get(Import, parsed.import_id)
            if imported is None:
                raise ResourceNotFound("import", parsed.import_id)
            existing = session.scalar(select(Run).where(Run.workflow_id == workflow_id))
            if existing is None:
                session.add(
                    Run(
                        id=run_id,
                        import_id=imported.id,
                        agent_version_id=imported.agent_version_id,
                        workflow_id=workflow_id,
                        request_identity=parsed.request_identity,
                        attempt_number=parsed.attempt_number,
                        labs_version=parsed.labs_version,
                        status="RUNNING",
                        started_at=datetime.now(UTC),
                    )
                )
            elif existing.id != run_id:
                raise IntegrityConflict("workflow", workflow_id)
        return {"run_id": run_id}

    def execute_labs_analysis(self, run_id: str) -> Mapping[str, Any]:
        del run_id
        self._compiler.refuse()

    def persist_labs_result(
        self, run_id: str, analysis_result_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        del run_id, analysis_result_ref
        self._compiler.refuse()

    def project_stored_report(
        self, run_id: str, persisted_fact_set_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        del run_id, persisted_fact_set_ref
        self._compiler.refuse()

    def complete_run(
        self, run_id: str, report_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        del run_id, report_ref
        self._compiler.refuse()


class PostgresDBOSRuns(RunCommandPort):
    def __init__(
        self,
        *,
        sessions: sessionmaker[Session],
        executor: DBOSForegroundExecutor,
        compiler: CanonicalLabsCompilerUnavailable,
        labs_version: str,
        config_identity: str,
    ) -> None:
        self._sessions = sessions
        self._executor = executor
        self._compiler = compiler
        self._labs_version = labs_version
        self._config_identity = config_identity

    def start_or_get_run(self, request: RunStart) -> JsonObject:
        # Refuse before creating DBOS/RDS state. A missing compiler is not a
        # failed analysis attempt and must not leave a misleading RUNNING row.
        if not self._compiler.available:
            self._compiler.refuse()
        with self._sessions() as session:
            imported = session.get(Import, request.import_id)
            if imported is None:
                raise ResourceNotFound("import", request.import_id)
            base_identity = _run_request_identity(
                import_id=request.import_id,
                labs_version=self._labs_version,
                config_identity=self._config_identity,
            )
            attempt = 1
            workflow_config_identity = self._config_identity
            if request.rerun:
                workflow_config_identity = _rerun_config_identity(
                    self._config_identity, request.idempotency_key
                )
                existing = session.scalars(
                    select(Run)
                    .where(Run.request_identity == base_identity)
                    .order_by(Run.attempt_number)
                ).all()
                matching_attempt = next(
                    (
                        row.attempt_number
                        for row in existing
                        if row.workflow_id
                        == workflow_id_for(
                            ImportRunRequest(
                                import_id=request.import_id,
                                request_identity=base_identity,
                                attempt_number=row.attempt_number,
                                labs_version=self._labs_version,
                                config_identity=workflow_config_identity,
                            )
                        )
                    ),
                    None,
                )
                attempt = matching_attempt or (
                    max((row.attempt_number for row in existing), default=0) + 1
                )
        workflow_request = ImportRunRequest(
            import_id=request.import_id,
            request_identity=base_identity,
            attempt_number=attempt,
            labs_version=self._labs_version,
            config_identity=workflow_config_identity,
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
    s3 = boto3.client("s3", region_name=settings.aws_region)
    artifacts = S3ArtifactStore(
        client=s3,
        artifact_bucket=settings.artifact_bucket,
        kms_key_id=settings.kms_key_id,
    )
    compiler = CanonicalLabsCompilerUnavailable()
    workflow_services = PostgresWorkflowServices(sessions=sessions, compiler=compiler)
    configure_workflow_services(workflow_services)
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
    imports = PostgresS3Imports(sessions=sessions, artifacts=artifacts)
    runs = PostgresDBOSRuns(
        sessions=sessions,
        executor=DBOSForegroundExecutor(),
        compiler=compiler,
        labs_version=settings.labs_version,
        config_identity=settings.labs_config_identity,
    )
    return BackendRuntime(
        app=create_app(reads=reads, imports=imports, runs=runs), engine=engine
    )


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


def _read_json_object(stream: BinaryIO, kind: str, identity: str) -> JsonObject:
    try:
        value: Any = json.load(stream)
    finally:
        stream.close()
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
    key_digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    return f"{config_identity}:explicit-rerun:{key_digest}"
