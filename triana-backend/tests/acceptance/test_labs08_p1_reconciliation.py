"""Independent offline contracts for the LABS-08 P1 reconciliation.

These tests use injected objects and tracked source only.  They do not contact
AWS, PostgreSQL, DBOS, a provider, or the network.
"""

# ruff: noqa: E402,S101,S603

from __future__ import annotations

import base64
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from triana_backend.api.contracts import IntegrityConflict
from triana_backend.artifacts.s3 import S3ArtifactStore
from triana_backend.composition import PostgresS3Reads
from triana_backend.domain.models import ArtifactIntegrityError, ArtifactKind
from triana_backend.persistence.models import Artifact, Report
from triana_backend.services.report_projection import (
    PersistedLabsFact,
    ReportProjectionInput,
    canonical_report_bytes,
    project_labs_report,
)

ROOT = Path(__file__).resolve().parents[3]
SOURCE_SHA256 = "76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b"
COMPILER_RESULT_HASH = (
    "13c4f659a65a78feeee248414c309d3df2c18c52f8cfa1e03b40c3b2db299aab"
)
KMS_KEY_ARN = (
    "arn:aws:kms:ap-south-1:123456789012:key/11111111-2222-3333-4444-555555555555"
)
OTHER_KMS_KEY_ARN = (
    "arn:aws:kms:ap-south-1:123456789012:key/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
)


def _facts() -> tuple[PersistedLabsFact, ...]:
    return (
        PersistedLabsFact("physical", "physical_record_count", 200, "DETERMINISTIC", 1),
        PersistedLabsFact(
            "statuses",
            "source_status_counts",
            {"COMPLETED": 186, "HARNESS_ERROR": 14},
            "DETERMINISTIC",
            1,
        ),
        PersistedLabsFact(
            "usable", "usable_conversation_count", 186, "DETERMINISTIC", 1
        ),
        PersistedLabsFact("rejected", "rejected_record_count", 14, "DETERMINISTIC", 1),
        PersistedLabsFact(
            "reasons",
            "rejection_summary",
            {"SOURCE_EXECUTION_INCOMPLETE": 14},
            "DETERMINISTIC",
            1,
        ),
    )


def _projected_report() -> dict[str, Any]:
    return project_labs_report(
        ReportProjectionInput(
            report_id="rpt_truthful_hash",
            run_id="run_truthful_hash",
            evidence_class="SYNTHETIC_EXISTING_TRACE_CORPUS",
            source_sha256=SOURCE_SHA256,
            facts=_facts(),
            conversations=(),
            gaps=({"reason_code": "SEMANTIC_ANALYSIS_NOT_RUN"},),
            created_at="2026-08-05T00:00:00+00:00",
            compiler_version="labs08-hrai-accounting-v1",
            compiler_result_hash=COMPILER_RESULT_HASH,
            rejected_evidence=tuple(
                {
                    "line_number": line,
                    "record_id": f"rejected-{line}",
                    "reason_code": "SOURCE_EXECUTION_INCOMPLETE",
                    "source_status": "HARNESS_ERROR",
                }
                for line in range(187, 201)
            ),
        )
    )


class _Session:
    def __init__(self, rows: dict[tuple[type[Any], str], Any]) -> None:
        self._rows = rows

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, model: type[Any], identity: str) -> Any:
        return self._rows.get((model, identity))


class _Sessions:
    def __init__(self, rows: dict[tuple[type[Any], str], Any]) -> None:
        self._rows = rows

    def __call__(self) -> _Session:
        return _Session(self._rows)


class _AvailableArtifacts:
    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    def head(self, ref: Any) -> Any:
        from triana_backend.domain.models import ArtifactAvailability

        return ArtifactAvailability.AVAILABLE

    def open_verified(self, ref: Any) -> io.BytesIO:
        del ref
        return io.BytesIO(canonical_report_bytes(self._body))


def _stored_report(
    body: dict[str, Any], *, stored_body: dict[str, Any] | None = None
) -> tuple[PostgresS3Reads, str]:
    body_bytes = canonical_report_bytes(body)
    digest = hashlib.sha256(body_bytes).hexdigest()
    artifact = Artifact(
        id="art_truthful_hash",
        artifact_kind="LABS_REPORT",
        content_sha256=digest,
        byte_count=len(body_bytes),
        media_type="application/json",
        storage_backend="S3",
        storage_bucket="private",
        storage_key=f"objects/sha256/labs_report/{digest[:2]}/{digest}",
        kms_key_id=KMS_KEY_ARN,
        checksum_sha256_b64=base64.b64encode(bytes.fromhex(digest)).decode(),
        availability="AVAILABLE",
    )
    row = Report(
        id=str(body["report_id"]),
        run_id=str(body["run"]["run_id"]),
        artifact_id=artifact.id,
        projection_schema_version=1,
        report_hash=digest,
        status="COMPLETED_WITH_GAPS",
    )
    reads = PostgresS3Reads(
        sessions=_Sessions({(Report, row.id): row, (Artifact, artifact.id): artifact}),
        artifacts=_AvailableArtifacts(stored_body or body),
    )
    return reads, row.id


def test_report_hash_semantics_and_serving_are_truthful() -> None:
    """The compiler hash is named honestly and the body hash stays external."""

    report = _projected_report()
    lineage = report["lineage"]
    projection_hash = hashlib.sha256(canonical_report_bytes(report)).hexdigest()

    assert lineage["compiler_result_hash"] == COMPILER_RESULT_HASH
    assert "report_hash" not in lineage
    assert COMPILER_RESULT_HASH != projection_hash
    assert len(projection_hash) == 64

    reads, report_id = _stored_report(report)
    assert reads.get_report(report_id) == report

    changed = json.loads(json.dumps(report))
    changed["title"] = "tampered but identity-preserving title"
    tampered_reads, report_id = _stored_report(report, stored_body=changed)
    with pytest.raises(IntegrityConflict):
        tampered_reads.get_report(report_id)


class _Body:
    def __init__(self, value: bytes) -> None:
        self._stream = io.BytesIO(value)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def close(self) -> None:
        self._stream.close()


class _PreexistingS3:
    def __init__(self, *, body: bytes, kms_identity: str) -> None:
        digest = hashlib.sha256(body).hexdigest()
        self._body = body
        self._head = {
            "ChecksumSHA256": base64.b64encode(bytes.fromhex(digest)).decode(),
            "ContentLength": len(body),
            "Metadata": {"sha256": digest, "artifact-kind": "LABS_REPORT"},
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": kms_identity,
        }

    def put_object(self, **kwargs: Any) -> None:
        del kwargs
        from botocore.exceptions import ClientError

        raise ClientError(
            {
                "Error": {"Code": "PreconditionFailed"},
                "ResponseMetadata": {"HTTPStatusCode": 412},
            },
            "PutObject",
        )

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        return dict(self._head)

    def get_object(self, **kwargs: Any) -> dict[str, _Body]:
        del kwargs
        return {"Body": _Body(self._body)}


def test_preexisting_cas_object_requires_exact_configured_kms_key_arn() -> None:
    """Aliases cannot be treated as equivalent without an authenticated resolution."""

    body = b'{"artifact_kind":"labs_report"}'
    for actual_identity in (
        OTHER_KMS_KEY_ARN,
        "arn:aws:kms:ap-south-1:123456789012:alias/triana-artifacts",
        "alias/triana-artifacts",
    ):
        mismatched = S3ArtifactStore(
            client=_PreexistingS3(body=body, kms_identity=actual_identity),
            artifact_bucket="private",
            kms_key_id=KMS_KEY_ARN,
        )
        with pytest.raises(ArtifactIntegrityError, match="KMS|key"):
            mismatched.publish_bytes(
                payload=body,
                kind=ArtifactKind.LABS_REPORT,
                media_type="application/json",
            )

    exact = S3ArtifactStore(
        client=_PreexistingS3(body=body, kms_identity=KMS_KEY_ARN),
        artifact_bucket="private",
        kms_key_id=KMS_KEY_ARN,
    )
    result = exact.publish_bytes(
        payload=body,
        kind=ArtifactKind.LABS_REPORT,
        media_type="application/json",
    )
    assert result.kms_key_id == KMS_KEY_ARN


def test_ci_executes_migration_bootstrap_and_bounded_content_secret_scan(
    tmp_path: Path,
) -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert (
        "uv run pytest -q "
        "tests/acceptance/test_labs08_p0_reconciliation.py::"
        "test_first_alembic_bootstrap_creates_schema_before_version_table"
    ) in workflow
    assert "./ops/verify-no-secrets.sh" in workflow

    scanner = ROOT / "ops" / "verify-no-secrets.sh"
    assert scanner.is_file()
    safe = tmp_path / "safe.txt"
    safe.write_text("AZURE_OPENAI_API_KEY=\n", encoding="utf-8")
    exposed = tmp_path / "exposed.txt"
    marker = "AKIA" + "1234567890ABCDEF"
    exposed.write_text(f"AWS_ACCESS_KEY_ID={marker}\n", encoding="utf-8")

    safe_result = subprocess.run(
        [str(scanner), str(safe)], capture_output=True, text=True, check=False
    )
    assert safe_result.returncode == 0, safe_result.stdout + safe_result.stderr

    exposed_result = subprocess.run(
        [str(scanner), str(exposed)], capture_output=True, text=True, check=False
    )
    assert exposed_result.returncode != 0
    output = exposed_result.stdout + exposed_result.stderr
    assert marker not in output
    assert "secret" in output.lower()
