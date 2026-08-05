"""Offline RED contracts for the LABS-08 integration reconciliation.

These tests freeze cross-lane behavior only.  They use injected ports and
tracked fixtures; they never connect to PostgreSQL, AWS, DBOS, or the network.
"""

# ruff: noqa: E402,S101,S603,S607

from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib
import io
import json
import os
import subprocess
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI


class _OfflineClientError(Exception):
    """Small botocore-compatible error used only by the injected fake S3."""

    def __init__(self, response: dict[str, Any], operation_name: str) -> None:
        super().__init__(operation_name)
        self.response = response


if importlib.util.find_spec("boto3") is None:
    boto3_stub = types.ModuleType("boto3")
    boto3_stub.client = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    botocore_stub = types.ModuleType("botocore")
    exceptions_stub = types.ModuleType("botocore.exceptions")
    exceptions_stub.BotoCoreError = Exception  # type: ignore[attr-defined]
    exceptions_stub.ClientError = _OfflineClientError  # type: ignore[attr-defined]
    sys.modules["boto3"] = boto3_stub
    sys.modules["botocore"] = botocore_stub
    sys.modules["botocore.exceptions"] = exceptions_stub

from triana_backend.api.contracts import IntegrityConflict
from triana_backend.artifacts.s3 import S3ArtifactStore
from triana_backend.composition import PostgresS3Reads
from triana_backend.config import BackendSettings
from triana_backend.domain.models import ArtifactAvailability, ArtifactKind
from triana_backend.persistence.models import Artifact, Report
from triana_backend.services.report_projection import (
    PersistedLabsFact,
    ReportProjectionInput,
    project_labs_report,
)

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "triana-backend"
LABS_SRC = ROOT / "triana-labs" / "src"
CANONICAL_REPORT = Path(__file__).with_name("labs08_canonical_accounting_report.json")
SOURCE_SHA256 = "76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b"


def _canonical_report() -> dict[str, Any]:
    return json.loads(CANONICAL_REPORT.read_text(encoding="utf-8"))


def test_module_level_asgi_app_uses_injected_composition_without_external_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uvicorn's checked-in target must resolve without opening infrastructure."""

    import triana_backend.composition as composition
    import triana_backend.config as config

    sentinel_settings = object()
    calls: list[object] = []
    closes: list[bool] = []

    monkeypatch.setattr(
        config.BackendSettings,
        "from_environment",
        classmethod(lambda cls: sentinel_settings),
    )
    monkeypatch.setattr(
        composition,
        "compose_backend",
        lambda settings: calls.append(settings)
        or SimpleNamespace(app=FastAPI(), close=lambda: closes.append(True)),
    )
    sys.modules.pop("triana_backend.main", None)
    module = importlib.import_module("triana_backend.main")

    assert isinstance(module.app, FastAPI)
    assert calls == []

    async def exercise_lifespan() -> None:
        async with module.app.router.lifespan_context(module.app):
            assert calls == [sentinel_settings]
            assert closes == []

    asyncio.run(exercise_lifespan())
    assert closes == [True]


def test_runtime_environment_names_agree_and_app_does_not_receive_backend_secrets() -> (
    None
):
    example_names = {
        line.partition("=")[0]
        for line in (ROOT / "ops" / ".env.example")
        .read_text(encoding="utf-8")
        .splitlines()
        if line and not line.startswith("#")
    }
    required_backend_names = {
        "TRIANA_DATABASE_URL",
        "DBOS_SYSTEM_DATABASE_URL",
        "TRIANA_ARTIFACT_BUCKET",
        "TRIANA_KMS_KEY_ID",
    }
    assert required_backend_names <= example_names

    compose = (ROOT / "compose.production.yaml").read_text(encoding="utf-8")
    app_section = compose.split("\n  app:\n", maxsplit=1)[1]
    assert "env_file:" not in app_section
    assert "TRIANA_DATABASE_URL" not in app_section
    assert "AZURE_OPENAI_API_KEY" not in app_section
    assert "OPENROUTER_API_KEY" not in app_section


def test_first_alembic_bootstrap_creates_schema_before_version_table() -> None:
    environment = {
        **os.environ,
        "PYTHONPATH": str(BACKEND / "src"),
        "TRIANA_DATABASE_URL": "postgresql://test:test@127.0.0.1/triana",
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    sql = completed.stdout
    assert sql.index("CREATE SCHEMA IF NOT EXISTS app") < sql.index(
        "CREATE TABLE app.alembic_version"
    )


def _synthetic_hrai_source() -> bytes:
    records = []
    for index in range(200):
        completed = index < 186
        records.append(
            {
                "case_id": f"case-{index:03d}",
                "schema_version": "normalized-trace-v2",
                "status": "COMPLETED" if completed else "HARNESS_ERROR",
                "turns": [{"role": "user", "content": "retained"}] if completed else [],
            }
        )
    return b"".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        for record in records
    )


def test_labs_compiler_owns_exact_200_186_14_accounting_and_rejections() -> None:
    sys.path.insert(0, str(LABS_SRC))
    try:
        from triana_labs.report import compile_hrai_normalized_trace_v2

        compiled = compile_hrai_normalized_trace_v2(
            _synthetic_hrai_source(),
            evidence_class="SYNTHETIC_EXISTING_TRACE_CORPUS",
        )
    finally:
        sys.path.remove(str(LABS_SRC))

    facts = {fact.fact_kind: fact.value for fact in compiled.facts}
    assert facts == {
        "physical_record_count": 200,
        "source_status_counts": {"COMPLETED": 186, "HARNESS_ERROR": 14},
        "usable_conversation_count": 186,
    }
    assert len(compiled.rejected_evidence) == 14
    assert {item.reason_code for item in compiled.rejected_evidence} == {
        "SOURCE_EXECUTION_INCOMPLETE"
    }
    assert {item.source_status for item in compiled.rejected_evidence} == {
        "HARNESS_ERROR"
    }


def test_backend_projection_preserves_accounting_contract_consumed_by_real_ui() -> None:
    expected = _canonical_report()
    facts = (
        PersistedLabsFact(
            "fact-physical", "physical_record_count", 200, "DETERMINISTIC", 1
        ),
        PersistedLabsFact(
            "fact-status",
            "source_status_counts",
            {"COMPLETED": 186, "HARNESS_ERROR": 14},
            "DETERMINISTIC",
            1,
        ),
        PersistedLabsFact(
            "fact-usable", "usable_conversation_count", 186, "DETERMINISTIC", 1
        ),
        PersistedLabsFact(
            "fact-rejected", "rejected_record_count", 14, "DETERMINISTIC", 1
        ),
        PersistedLabsFact(
            "fact-reasons",
            "rejection_summary",
            {"SOURCE_EXECUTION_INCOMPLETE": 14},
            "DETERMINISTIC",
            1,
        ),
    )
    projected = project_labs_report(
        ReportProjectionInput(
            report_id=expected["report_id"],
            run_id=expected["run"]["run_id"],
            evidence_class=expected["evidence_class"],
            source_sha256=SOURCE_SHA256,
            created_at=expected["created_at"],
            compiler_version="labs08-hrai-accounting-v1",
            compiler_result_hash=(
                "13c4f659a65a78feeee248414c309d3df2c18c52f8cfa1e03b40c3b2db299aab"
            ),
            facts=facts,
            conversations=(),
            gaps=({"reason_code": "SEMANTIC_ANALYSIS_NOT_RUN"},),
        )
    )

    assert projected["mode"] == "RETAINED_TRACE_ACCOUNTING"
    assert projected["setup"]["understanding"] == expected["setup"]["understanding"]
    assert projected["behavior"]["groups"] == []
    assert projected["cases"] == []
    assert projected["conversations"] == []
    assert projected["reviews"] == []


class _Rows:
    def __init__(self, rows: list[Report]) -> None:
        self._rows = rows

    def all(self) -> list[Report]:
        return self._rows


class _Session:
    def __init__(
        self, rows: dict[tuple[type[Any], str], Any], reports: list[Report]
    ) -> None:
        self._rows = rows
        self._reports = reports

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, model: type[Any], identity: str) -> Any:
        return self._rows.get((model, identity))

    def scalars(self, statement: object) -> _Rows:
        del statement
        return _Rows(self._reports)


class _Sessions:
    def __init__(
        self, rows: dict[tuple[type[Any], str], Any], reports: list[Report]
    ) -> None:
        self._rows = rows
        self._reports = reports

    def __call__(self) -> _Session:
        return _Session(self._rows, self._reports)


class _Artifacts:
    def __init__(self, bodies: dict[str, dict[str, Any] | None]) -> None:
        self._bodies = bodies

    def head(self, ref: Any) -> ArtifactAvailability:
        return (
            ArtifactAvailability.AVAILABLE
            if self._bodies.get(ref.id) is not None
            else ArtifactAvailability.MISSING
        )

    def open_verified(self, ref: Any) -> io.BytesIO:
        body = self._bodies.get(ref.id)
        if body is None:
            raise AssertionError("missing body must be rejected by head")
        return io.BytesIO(json.dumps(body).encode())


def _report(report_id: str, artifact_id: str, *, report_hash: str) -> Report:
    return Report(
        id=report_id,
        run_id=f"run-{report_id}",
        artifact_id=artifact_id,
        projection_schema_version=1,
        report_hash=report_hash,
        status="COMPLETED",
    )


def _artifact(artifact_id: str, body: dict[str, Any]) -> Artifact:
    body_bytes = json.dumps(body).encode()
    digest = hashlib.sha256(body_bytes).hexdigest()
    return Artifact(
        id=artifact_id,
        artifact_kind="LABS_REPORT",
        content_sha256=digest,
        byte_count=len(body_bytes),
        media_type="application/json",
        storage_backend="S3",
        storage_bucket="private",
        storage_key=f"reports/{artifact_id}",
        kms_key_id="arn:aws:kms:ap-south-1:123456789012:key/key-id",
        checksum_sha256_b64=base64.b64encode(bytes.fromhex(digest)).decode(),
        availability="AVAILABLE",
    )


def test_report_body_identity_mismatch_refuses_instead_of_serving_wrong_report() -> (
    None
):
    wrong_body = {
        "artifact_kind": "labs_report",
        "schema_version": 1,
        "report_id": "report-other",
        "run_id": "run-report-other",
    }
    artifact = _artifact("artifact-wrong", wrong_body)
    report = _report(
        "report-requested",
        artifact.id,
        report_hash=artifact.content_sha256,
    )
    reads = PostgresS3Reads(
        sessions=_Sessions(
            {(Report, report.id): report, (Artifact, artifact.id): artifact}, [report]
        ),
        artifacts=_Artifacts({artifact.id: wrong_body}),
    )

    with pytest.raises(IntegrityConflict):
        reads.get_report(report.id)


def test_missing_unrelated_report_does_not_hide_healthy_conversation() -> None:
    missing_body = {
        "artifact_kind": "labs_report",
        "schema_version": 1,
        "report_id": "report-a-missing",
        "run_id": "run-report-a-missing",
        "conversations": [],
    }
    missing_artifact = _artifact("artifact-missing", missing_body)
    missing = _report(
        "report-a-missing",
        missing_artifact.id,
        report_hash=missing_artifact.content_sha256,
    )
    healthy_body = {
        "artifact_kind": "labs_report",
        "schema_version": 1,
        "report_id": "report-b-healthy",
        "run_id": "run-report-b-healthy",
        "conversations": [{"conversation_id": "conversation-healthy"}],
    }
    healthy_artifact = _artifact("artifact-healthy", healthy_body)
    healthy = _report(
        "report-b-healthy",
        healthy_artifact.id,
        report_hash=healthy_artifact.content_sha256,
    )
    rows = {
        (Report, missing.id): missing,
        (Artifact, missing.artifact_id): missing_artifact,
        (Report, healthy.id): healthy,
        (Artifact, healthy.artifact_id): healthy_artifact,
    }
    reads = PostgresS3Reads(
        sessions=_Sessions(rows, [missing, healthy]),
        artifacts=_Artifacts(
            {missing.artifact_id: None, healthy.artifact_id: healthy_body}
        ),
    )

    result = reads.get_conversation("conversation-healthy")
    assert result["report_id"] == healthy.id
    assert result["conversation"] == {"conversation_id": "conversation-healthy"}


def test_ci_uses_scopes_that_are_green_under_the_frozen_acceptance_style() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv run ruff check src migrations" in workflow
    assert "uv run ruff check src tests migrations" not in workflow
    assert "uv run ruff format --check src tests migrations" in workflow
    assert "uv run mypy src/triana_backend" in workflow


class _Body:
    def __init__(self, value: bytes) -> None:
        self._stream = io.BytesIO(value)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def close(self) -> None:
        self._stream.close()


class _S3:
    def __init__(self, kms_arn: str) -> None:
        self.kms_arn = kms_arn
        self.objects: dict[tuple[str, str], dict[str, Any]] = {}

    def seed(self, bucket: str, key: str, body: bytes, checksum: str) -> None:
        self.objects[(bucket, key)] = {
            "body": body,
            "ChecksumSHA256": checksum,
            "ContentLength": len(body),
            "Metadata": {"sha256": SOURCE_SHA256},
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": self.kms_arn,
        }

    def head_object(self, *, Bucket: str, Key: str, **kwargs: object) -> dict[str, Any]:
        del kwargs
        return dict(self.objects[(Bucket, Key)])

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, _Body]:
        return {"Body": _Body(self.objects[(Bucket, Key)]["body"])}

    def put_object(self, *, Bucket: str, Key: str, Body: Any, **kwargs: Any) -> None:
        if (Bucket, Key) in self.objects:
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {"Code": "PreconditionFailed"},
                    "ResponseMetadata": {"HTTPStatusCode": 412},
                },
                "PutObject",
            )
        body = Body.read()
        self.objects[(Bucket, Key)] = {
            "body": body,
            "ChecksumSHA256": kwargs["ChecksumSHA256"],
            "ContentLength": len(body),
            "Metadata": kwargs["Metadata"],
            "ServerSideEncryption": kwargs["ServerSideEncryption"],
            "SSEKMSKeyId": self.kms_arn,
        }


def test_s3_cas_domain_separates_artifact_kind_for_identical_bytes() -> None:
    import base64

    body = b"same exact bytes"
    import hashlib

    digest = hashlib.sha256(body).hexdigest()
    checksum = base64.b64encode(bytes.fromhex(digest)).decode()
    kms_arn = "arn:aws:kms:ap-south-1:123456789012:key/key-id"
    client = _S3(kms_arn)
    client.objects[("staging", "source")] = {
        "body": body,
        "ChecksumSHA256": checksum,
        "ContentLength": len(body),
        "Metadata": {"sha256": digest},
        "ServerSideEncryption": "aws:kms",
        "SSEKMSKeyId": kms_arn,
    }
    store = S3ArtifactStore(
        client=client, artifact_bucket="artifacts", kms_key_id=kms_arn
    )

    source = store.publish_staging(
        bucket="staging",
        key="source",
        expected_sha256=digest,
        kind=ArtifactKind.SOURCE_TRACE_JSONL,
        media_type="application/x-ndjson",
    )
    report = store.publish_staging(
        bucket="staging",
        key="source",
        expected_sha256=digest,
        kind=ArtifactKind.LABS_REPORT,
        media_type="application/json",
    )

    assert source.storage_key != report.storage_key
    assert "/source_trace_jsonl/" in source.storage_key
    assert "/labs_report/" in report.storage_key


def test_kms_alias_is_rejected_as_ambiguous_runtime_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {
        "TRIANA_DATABASE_URL": "postgresql://test:test@db/triana",
        "DBOS_SYSTEM_DATABASE_URL": "postgresql://test:test@db/triana",
        "TRIANA_ARTIFACT_BUCKET": "private-artifacts",
        "TRIANA_KMS_KEY_ID": "alias/triana-artifacts",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="KMS.*ARN"):
        BackendSettings.from_environment()


def test_compiler_persistence_and_report_publication_path_is_wired() -> None:
    """The live gate remains authoritative; this guards against an absent path."""

    source = (BACKEND / "src" / "triana_backend" / "composition.py").read_text(
        encoding="utf-8"
    )
    required_effects = (
        "compile_hrai_normalized_trace_v2",
        "AnalysisFact(",
        "RunArtifact(",
        "Report(",
        "ArtifactKind.LABS_REPORT",
        "project_labs_report",
    )
    assert all(effect in source for effect in required_effects)
