"""Authenticated durable projection of the canonical Trace-to-Eval engine."""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from triana_labs.trace_to_eval import append_human_ruling, run_trace_to_eval
from triana_labs.trace_to_eval.adapters import prepare_evidence_manifest

from triana_backend.api.contracts import IntegrityConflict, ResourceNotFound
from triana_backend.artifacts.s3 import S3ArtifactStore
from triana_backend.domain.models import (
    ArtifactKind,
    ArtifactRef,
    canonical_json,
    deterministic_id,
)
from triana_backend.persistence.models import (
    Agent,
    AgentVersion,
    Artifact,
    Import,
    ImportedConversation,
    ImportRejection,
    Report,
    Run,
    RunArtifact,
)

JsonObject = dict[str, Any]
_ENGINE_VERSION = "trace-to-eval-v0"
_REPORT_ROLE = "TRACE_TO_EVAL_REPORT"
_QUEUE_ROLE = "TRACE_TO_EVAL_REVIEW_QUEUE"
_CONVERSATIONS_ROLE = "TRACE_TO_EVAL_CONVERSATIONS"
_RULING_PREFIX = "TRACE_RULING:"


class PersistentSelfServeTraceToEvalService:
    """Run without provider egress and persist immutable artifacts in RDS/S3."""

    def __init__(
        self, *, sessions: sessionmaker[Session], artifacts: S3ArtifactStore
    ) -> None:
        self._sessions = sessions
        self._artifacts = artifacts

    def start_analysis_for_import(
        self, owner_subject: str, agent_id: str, import_id: str
    ) -> JsonObject:
        context = self._owned_import(owner_subject, agent_id, import_id)
        request_identity = hashlib.sha256(
            canonical_json(
                {
                    "workspace_id": context["workspace_id"],
                    "agent_id": agent_id,
                    "import_id": import_id,
                    "source_sha256": context["source_sha256"],
                    "engine_version": _ENGINE_VERSION,
                }
            )
        ).hexdigest()
        run_id = deterministic_id(
            "run", {"request_identity": request_identity, "attempt_number": 1}
        )
        with self._sessions() as session, session.begin():
            created_run_id = session.scalar(
                insert(cast(Any, Run.__table__))
                .values(
                    id=run_id,
                    import_id=import_id,
                    agent_version_id=context["agent_version_id"],
                    workflow_id=f"trace-to-eval:{run_id}",
                    request_identity=request_identity,
                    attempt_number=1,
                    labs_version=_ENGINE_VERSION,
                    status="RUNNING",
                    started_at=datetime.now(UTC),
                )
                .on_conflict_do_nothing()
                .returning(Run.id)
            )
        existing = self._run_projection(owner_subject, run_id)
        if created_run_id is None or existing.get("report_id") is not None:
            return existing
        if int(context["accepted_count"]) == 0:
            with self._sessions() as session, session.begin():
                row = session.get(Run, run_id)
                if row is not None:
                    row.status = "FAILED"
                    row.finished_at = datetime.now(UTC)
            return self._run_projection(owner_subject, run_id)

        try:
            self._execute(context, run_id)
        except (BotoCoreError, ClientError, OSError, SQLAlchemyError, ValueError):
            with self._sessions() as session, session.begin():
                row = session.get(Run, run_id)
                if row is not None and row.status == "RUNNING":
                    row.status = "FAILED"
                    row.finished_at = datetime.now(UTC)
            return self._run_projection(owner_subject, run_id)
        return self._run_projection(owner_subject, run_id)

    def list_agent_analysis_runs(
        self, owner_subject: str, agent_id: str
    ) -> Sequence[JsonObject]:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            owned_agent = session.scalar(
                select(Agent.id).where(
                    Agent.id == agent_id, Agent.workspace_id == workspace_id
                )
            )
            if owned_agent is None:
                raise ResourceNotFound("agent", agent_id)
            run_ids = session.scalars(
                select(Run.id)
                .join(AgentVersion, AgentVersion.id == Run.agent_version_id)
                .where(
                    AgentVersion.agent_id == agent_id,
                    Run.labs_version == _ENGINE_VERSION,
                )
                .order_by(Run.created_at.desc(), Run.id)
            ).all()
        return [self._run_projection(owner_subject, run_id) for run_id in run_ids]

    def get_owned_report(self, owner_subject: str, report_id: str) -> JsonObject:
        binding, report = self._owned_report(owner_subject, report_id)
        queue = self._read_role(binding["run_id"], _QUEUE_ROLE)
        review = self.get_owned_review_state(owner_subject, report_id)
        return {
            **report,
            "workspace_id": binding["workspace_id"],
            "agent_id": binding["agent_id"],
            "import_id": binding["import_id"],
            "run_id": binding["run_id"],
            "judgment": {
                "state": review["judgment_state"],
                "required_review_item_count": len(
                    cast(list[Any], queue.get("items", []))
                ),
                "verdict": "NOT_ESTABLISHED",
            },
        }

    def get_owned_review_state(self, owner_subject: str, report_id: str) -> JsonObject:
        binding, _ = self._owned_report(owner_subject, report_id)
        queue = self._read_role(binding["run_id"], _QUEUE_ROLE)
        rulings = self._rulings(binding["run_id"])
        current: dict[str, JsonObject] = {}
        for ruling in rulings:
            current[str(ruling["item_id"])] = ruling
        items = cast(list[JsonObject], queue.get("items", []))
        state = (
            "NOT_AVAILABLE"
            if not items
            else "JUDGMENT_COMPLETE"
            if all(str(item["item_id"]) in current for item in items)
            else "JUDGMENT_REQUIRED"
        )
        return {
            "artifact_kind": "trace_to_eval_review_state_v0",
            "schema_version": 0,
            "report_id": report_id,
            "judgment_state": state,
            "review_queue": queue,
            "current_rulings": [current[key] for key in sorted(current)],
        }

    def append_owned_ruling(
        self, owner_subject: str, report_id: str, ruling: Mapping[str, Any]
    ) -> JsonObject:
        binding, report = self._owned_report(owner_subject, report_id)
        queue = self._read_role(binding["run_id"], _QUEUE_ROLE)
        with self._sessions() as session, session.begin():
            locked = session.scalar(
                select(Run).where(Run.id == binding["run_id"]).with_for_update()
            )
            if locked is None:
                raise ResourceNotFound("report", report_id)
            previous = self._rulings_from_session(session, str(binding["run_id"]))
            with tempfile.TemporaryDirectory(prefix="triana-self-serve-review-") as raw:
                output = Path(raw)
                (output / "trace_to_eval_report.json").write_bytes(_canonical(report))
                (output / "review_queue.json").write_bytes(_canonical(queue))
                if previous:
                    (output / "human_rulings.jsonl").write_bytes(
                        b"".join(_canonical(item) for item in previous)
                    )
                accepted = append_human_ruling(output, ruling)
            ref = self._artifacts.publish_workspace_bytes(
                workspace_id=str(binding["workspace_id"]),
                payload=_canonical(accepted),
                kind=ArtifactKind.TRACE_TO_EVAL_RULING,
                media_type="application/json",
            )
            _persist_artifact(session, str(binding["workspace_id"]), ref)
            _link_artifact(
                session,
                str(binding["run_id"]),
                ref.id,
                f"{_RULING_PREFIX}{len(previous) + 1:06d}",
            )
            return accepted

    def get_owned_conversation(
        self, owner_subject: str, report_id: str, trace_id: str
    ) -> JsonObject:
        binding, _ = self._owned_report(owner_subject, report_id)
        artifact = self._read_role(binding["run_id"], _CONVERSATIONS_ROLE)
        conversation = next(
            (
                item
                for item in cast(list[Any], artifact.get("conversations", []))
                if isinstance(item, dict) and item.get("trace_id") == trace_id
            ),
            None,
        )
        if conversation is None:
            raise ResourceNotFound("conversation", trace_id)
        return {
            **cast(JsonObject, conversation),
            "report_id": report_id,
            "run_id": binding["run_id"],
            "workspace_id": binding["workspace_id"],
            "agent_id": binding["agent_id"],
            "import_id": binding["import_id"],
            "evidence_state": "OBSERVED",
        }

    def _execute(self, context: JsonObject, run_id: str) -> None:
        source_ref = cast(ArtifactRef, context["source_ref"])
        source = self._artifacts.open_verified(source_ref)
        try:
            source.read()
        finally:
            source.close()
        with self._sessions() as session:
            conversations = session.scalars(
                select(ImportedConversation)
                .where(ImportedConversation.import_id == context["import_id"])
                .order_by(ImportedConversation.line_number)
            ).all()
            rejections = session.scalars(
                select(ImportRejection)
                .where(ImportRejection.import_id == context["import_id"])
                .order_by(ImportRejection.line_number)
            ).all()
        payload = b"".join(
            _canonical(
                {
                    "contract_kind": "preview_trace",
                    "schema_version": 1,
                    "privacy_class": "CUSTOMER_AUTHORIZED_TRACE_DATA",
                    "trace_id": row.trace_id,
                    "source_trace_id": row.source_trace_id,
                    "events": row.events_json,
                }
            )
            for row in conversations
        )
        with tempfile.TemporaryDirectory(prefix="triana-self-serve-analysis-") as raw:
            root = Path(raw)
            source_path = root / "accepted-preview-traces.jsonl"
            source_path.write_bytes(payload)
            manifest_path = prepare_evidence_manifest(
                source_path,
                root / "prepared",
                source_kind="preview-trace-jsonl",
                workspace_id=str(context["workspace_id"]),
                agent_id=str(context["agent_id"]),
                semantic_model_id=None,
            )
            manifest = cast(JsonObject, json.loads(manifest_path.read_bytes()))
            manifest["privacy"] = {
                "authorization": "CUSTOMER_OWNER_ATTESTED",
                "execution_location": "PRIVATE_BACKEND",
                "provider_egress": {"authorized": False, "model_id": None},
                "redaction": {"state": "NOT_REQUIRED_NO_EGRESS"},
            }
            source_meta = cast(JsonObject, manifest["source"])
            source_meta["upstream_sha256"] = "sha256:" + str(context["source_sha256"])
            source_meta["physical_record_count"] = int(context["physical_count"])
            source_meta["normalized_record_count"] = len(conversations)
            manifest["adapter_rejections"] = [
                {
                    "line_number": row.line_number,
                    "code": row.code,
                    "json_pointer": row.json_pointer,
                }
                for row in rejections
            ]
            manifest_path.write_bytes(_canonical(manifest))
            output = root / "output"
            report = run_trace_to_eval(manifest_path, output, semantic_model=None)
            artifacts = (
                (
                    "trace_to_eval_report.json",
                    ArtifactKind.TRACE_TO_EVAL_REPORT,
                    _REPORT_ROLE,
                ),
                (
                    "review_queue.json",
                    ArtifactKind.TRACE_TO_EVAL_REVIEW_QUEUE,
                    _QUEUE_ROLE,
                ),
                (
                    "conversations.json",
                    ArtifactKind.TRACE_TO_EVAL_CONVERSATIONS,
                    _CONVERSATIONS_ROLE,
                ),
            )
            refs = [
                (
                    self._artifacts.publish_workspace_bytes(
                        workspace_id=str(context["workspace_id"]),
                        payload=(output / filename).read_bytes(),
                        kind=kind,
                        media_type="application/json",
                    ),
                    role,
                )
                for filename, kind, role in artifacts
            ]
        report_ref = refs[0][0]
        with self._sessions() as session, session.begin():
            for ref, role in refs:
                _persist_artifact(session, str(context["workspace_id"]), ref)
                _link_artifact(session, run_id, ref.id, role)
            report_id = str(report["report_id"])
            session.execute(
                insert(cast(Any, Report.__table__))
                .values(
                    id=deterministic_id("rpt", {"report_id": report_id}),
                    run_id=run_id,
                    artifact_id=report_ref.id,
                    projection_schema_version=0,
                    report_hash=report_id.removeprefix("sha256:"),
                    status="COMPLETED_WITH_GAPS" if report["gaps"] else "COMPLETED",
                )
                .on_conflict_do_nothing()
            )
            row = session.get(Run, run_id)
            if row is None:
                raise IntegrityConflict("run", run_id)
            row.status = "COMPLETED_WITH_GAPS" if report["gaps"] else "COMPLETED"
            row.finished_at = datetime.now(UTC)

    def _owned_import(
        self, owner_subject: str, agent_id: str, import_id: str
    ) -> JsonObject:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            row = session.execute(
                select(Import, AgentVersion, Agent, Artifact)
                .join(AgentVersion, AgentVersion.id == Import.agent_version_id)
                .join(Agent, Agent.id == AgentVersion.agent_id)
                .join(Artifact, Artifact.id == Import.source_artifact_id)
                .where(
                    Import.id == import_id,
                    Import.workspace_id == workspace_id,
                    Agent.id == agent_id,
                    Agent.workspace_id == workspace_id,
                )
            ).one_or_none()
            if row is None:
                raise ResourceNotFound("import", import_id)
            imported, version, agent, source = row
            return {
                "workspace_id": workspace_id,
                "agent_id": agent.id,
                "agent_version_id": version.id,
                "import_id": imported.id,
                "source_sha256": imported.source_sha256,
                "physical_count": imported.physical_record_count,
                "accepted_count": imported.usable_conversation_count,
                "source_ref": _artifact_ref(source),
            }

    def _run_projection(self, owner_subject: str, run_id: str) -> JsonObject:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            row = session.execute(
                select(Run, Import, AgentVersion, Agent, Report)
                .join(Import, Import.id == Run.import_id)
                .join(AgentVersion, AgentVersion.id == Run.agent_version_id)
                .join(Agent, Agent.id == AgentVersion.agent_id)
                .outerjoin(Report, Report.run_id == Run.id)
                .where(Run.id == run_id, Import.workspace_id == workspace_id)
            ).one_or_none()
            if row is None:
                raise ResourceNotFound("analysis_run", run_id)
            run, imported, _version, agent, report = row
            report_id = None if report is None else "sha256:" + report.report_hash
        judgment_state = "NOT_AVAILABLE"
        if report_id is not None:
            judgment_state = str(
                self.get_owned_review_state(owner_subject, report_id)["judgment_state"]
            )
        return {
            "workspace_id": workspace_id,
            "agent_id": agent.id,
            "import_id": imported.id,
            "run_id": run.id,
            "report_id": report_id,
            "state": run.status,
            "judgment_state": judgment_state,
            "created_at": run.created_at.isoformat(),
            **(
                {"failure_code": "ANALYSIS_EXECUTION_FAILED"}
                if run.status == "FAILED"
                else {}
            ),
        }

    def _owned_report(
        self, owner_subject: str, report_id: str
    ) -> tuple[JsonObject, JsonObject]:
        if not report_id.startswith("sha256:"):
            raise ResourceNotFound("report", report_id)
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            row = session.execute(
                select(Report, Run, Import, AgentVersion, Agent, Artifact)
                .join(Run, Run.id == Report.run_id)
                .join(Import, Import.id == Run.import_id)
                .join(AgentVersion, AgentVersion.id == Run.agent_version_id)
                .join(Agent, Agent.id == AgentVersion.agent_id)
                .join(Artifact, Artifact.id == Report.artifact_id)
                .where(
                    Report.report_hash == report_id.removeprefix("sha256:"),
                    Import.workspace_id == workspace_id,
                    Agent.workspace_id == workspace_id,
                )
            ).one_or_none()
            if row is None:
                raise ResourceNotFound("report", report_id)
            _stored, run, imported, _version, agent, artifact = row
            report = self._read_ref(_artifact_ref(artifact))
        if report.get("report_id") != report_id:
            raise IntegrityConflict("report", report_id)
        return (
            {
                "workspace_id": workspace_id,
                "agent_id": agent.id,
                "import_id": imported.id,
                "run_id": run.id,
            },
            report,
        )

    def _read_role(self, run_id: str, role: str) -> JsonObject:
        with self._sessions() as session:
            artifact = session.scalar(
                select(Artifact)
                .join(RunArtifact, RunArtifact.artifact_id == Artifact.id)
                .where(
                    RunArtifact.run_id == run_id,
                    RunArtifact.artifact_role == role,
                )
            )
            if artifact is None:
                raise IntegrityConflict("run_artifact", run_id)
            return self._read_ref(_artifact_ref(artifact))

    def _rulings(self, run_id: str) -> list[JsonObject]:
        with self._sessions() as session:
            return self._rulings_from_session(session, run_id)

    def _rulings_from_session(self, session: Session, run_id: str) -> list[JsonObject]:
        rows = session.execute(
            select(RunArtifact, Artifact)
            .join(Artifact, Artifact.id == RunArtifact.artifact_id)
            .where(
                RunArtifact.run_id == run_id,
                RunArtifact.artifact_role.like(f"{_RULING_PREFIX}%"),
            )
            .order_by(RunArtifact.artifact_role)
        ).all()
        return [self._read_ref(_artifact_ref(artifact)) for _link, artifact in rows]

    def _read_ref(self, ref: ArtifactRef) -> JsonObject:
        stream = self._artifacts.open_verified(ref)
        try:
            value = json.loads(stream.read())
        finally:
            stream.close()
        if not isinstance(value, dict):
            raise IntegrityConflict("artifact", ref.id)
        return cast(JsonObject, value)


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _workspace_id(subject: str) -> str:
    subject_hash = hashlib.sha256(subject.encode("utf-8")).hexdigest()
    user_id = deterministic_id("usr", {"subject_hash": subject_hash})
    return deterministic_id("wsp", {"owner_user_id": user_id})


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


def _persist_artifact(session: Session, workspace_id: str, ref: ArtifactRef) -> None:
    session.execute(
        insert(cast(Any, Artifact.__table__))
        .values(
            id=ref.id,
            workspace_id=workspace_id,
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
        .on_conflict_do_nothing()
    )


def _link_artifact(session: Session, run_id: str, artifact_id: str, role: str) -> None:
    session.execute(
        insert(cast(Any, RunArtifact.__table__))
        .values(run_id=run_id, artifact_id=artifact_id, artifact_role=role)
        .on_conflict_do_nothing()
    )


__all__ = ["PersistentSelfServeTraceToEvalService"]
