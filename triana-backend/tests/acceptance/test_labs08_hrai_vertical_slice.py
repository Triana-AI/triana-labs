"""Independent black-box acceptance for LABS-08 Exit B.

No production module is imported. The test uses the operator CLI, S3, RDS,
and HTTP surfaces as separate deployed consumers would.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

BACKEND = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(__file__).with_name("labs08_hrai_contract.json")
PACKAGE = BACKEND / "src" / "triana_backend" / "__init__.py"


def _load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _required_environment(contract: dict[str, Any]) -> dict[str, str]:
    environment = contract["environment"]
    defaults = contract["defaults"]
    values = {
        "api_origin": os.environ.get(environment["api_origin"], defaults["api_origin"]),
        "artifact_bucket": os.environ.get(environment["artifact_bucket"], ""),
        "database_url": os.environ.get(environment["database_url"], ""),
        "source_file": os.environ.get(environment["source_file"], ""),
        "source_s3_uri": os.environ.get(environment["source_s3_uri"], ""),
        "workspace_slug": os.environ.get(
            environment["workspace_slug"], defaults["workspace_slug"]
        ),
    }
    missing = [
        environment[key]
        for key in ("artifact_bucket", "database_url", "source_file", "source_s3_uri")
        if not values[key]
    ]
    if missing:
        raise AssertionError(
            "LABS08_ACCEPTANCE_PRECONDITION: set " + ", ".join(sorted(missing))
        )
    source_file = Path(values["source_file"])
    if not source_file.is_file():
        raise AssertionError(
            "LABS08_ACCEPTANCE_PRECONDITION: "
            f"{environment['source_file']} must name the authorized run_200 JSONL file"
        )
    return values


def _source_facts(
    source_path: Path,
) -> tuple[bytes, list[dict[str, Any]], dict[str, int]]:
    source_bytes = source_path.read_bytes()
    records = [json.loads(raw_line) for raw_line in source_bytes.splitlines()]
    status_counts: dict[str, int] = {}
    for record in records:
        status = record["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    return source_bytes, records, status_counts


def _run_operator(
    contract: dict[str, Any], action: str, tokens: dict[str, str]
) -> dict[str, Any]:
    command = contract["operator_command"]
    arguments = [token.format(**tokens) for token in command[f"{action}_arguments"]]
    completed = subprocess.run(
        [command["executable"], *arguments],
        cwd=BACKEND,
        env={
            **os.environ,
            "TRIANA_BACKEND_API_ORIGIN": tokens["api_origin"],
            "PYTHONPATH": str(BACKEND / "src"),
        },
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def _get_json(origin: str, path: str) -> dict[str, Any]:
    with urlopen(f"{origin.rstrip('/')}{path}", timeout=30) as response:  # noqa: S310
        assert response.status == 200
        return json.load(response)


def _get_error_json(origin: str, path: str) -> tuple[int, dict[str, Any]]:
    try:
        _get_json(origin, path)
    except HTTPError as error:
        return error.code, json.load(error)
    raise AssertionError(f"expected typed HTTP failure for {path}")


def _table(contract: dict[str, Any], key: str) -> str:
    database = contract["database"]
    schema = database["schema"]
    table = database["tables"][key]
    assert schema.replace("_", "").isalnum() and table.replace("_", "").isalnum()
    return f'"{schema}"."{table}"'


def test_hrai_run_200_flows_from_s3_and_rds_to_api_without_value_invention() -> None:
    # Canonical RED must be absent production, not absent AWS/RDS configuration.
    assert PACKAGE.is_file(), "triana_backend production package is not implemented"

    contract = _load_contract()
    source = contract["source"]
    values = _required_environment(contract)
    source_path = Path(values["source_file"])
    source_bytes, records, status_counts = _source_facts(source_path)

    assert hashlib.sha256(source_bytes).hexdigest() == source["sha256"]
    assert len(records) == source["physical_record_count"]
    assert status_counts == source["status_counts"]
    assert status_counts["COMPLETED"] == source["usable_conversation_count"]

    import boto3
    import psycopg

    parsed = urlparse(values["source_s3_uri"])
    assert parsed.scheme == "s3" and parsed.netloc and parsed.path.lstrip("/")
    source_bucket = parsed.netloc
    source_key = parsed.path.lstrip("/")
    s3 = boto3.client("s3")
    head = s3.head_object(Bucket=source_bucket, Key=source_key, ChecksumMode="ENABLED")
    assert head["ServerSideEncryption"] == "aws:kms"
    assert head["ContentLength"] == len(source_bytes)
    assert head["Metadata"]["sha256"] == source["sha256"]
    assert head["ChecksumSHA256"] == base64.b64encode(
        bytes.fromhex(source["sha256"])
    ).decode("ascii")
    stored_source = s3.get_object(Bucket=source_bucket, Key=source_key)["Body"].read()
    assert stored_source == source_bytes

    tokens = {
        "api_origin": values["api_origin"],
        "source_bucket": source_bucket,
        "source_key": source_key,
        "source_sha256": source["sha256"],
        "workspace_slug": values["workspace_slug"],
        "import_id": "",
    }
    first_import = _run_operator(contract, "import", tokens)
    repeated_import = _run_operator(contract, "import", tokens)
    import_identity = {"artifact_id", "import_id"}
    assert import_identity <= first_import.keys()
    assert {key: repeated_import[key] for key in import_identity} == {
        key: first_import[key] for key in import_identity
    }

    tokens["import_id"] = first_import["import_id"]
    first_run = _run_operator(contract, "run", tokens)
    repeated_run = _run_operator(contract, "run", tokens)
    rerun = _run_operator(contract, "rerun", tokens)
    run_identity = {"run_id", "workflow_id", "report_id", "attempt_number"}
    assert run_identity <= first_run.keys()
    assert {key: repeated_run[key] for key in run_identity} == {
        key: first_run[key] for key in run_identity
    }
    assert rerun["run_id"] != first_run["run_id"]
    assert rerun["workflow_id"] != first_run["workflow_id"]
    assert rerun["report_id"] != first_run["report_id"]
    assert rerun["attempt_number"] == first_run["attempt_number"] + 1

    with psycopg.connect(values["database_url"]) as connection:
        with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'artifacts')} WHERE id=%s",
                (first_import["artifact_id"],),
            )
            source_artifact = cursor.fetchone()
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'imports')} WHERE id=%s",
                (first_import["import_id"],),
            )
            import_row = cursor.fetchone()
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'runs')} WHERE id=%s",
                (first_run["run_id"],),
            )
            run_row = cursor.fetchone()
            cursor.execute(
                f"SELECT fact_kind, value_json, authority FROM "
                f"{_table(contract, 'analysis_facts')} WHERE run_id=%s",
                (first_run["run_id"],),
            )
            facts = {row["fact_kind"]: row for row in cursor.fetchall()}
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'reports')} WHERE id=%s",
                (first_run["report_id"],),
            )
            report_row = cursor.fetchone()
            assert report_row is not None
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'artifacts')} WHERE id=%s",
                (report_row["artifact_id"],),
            )
            report_artifact = cursor.fetchone()
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'reports')} WHERE id=%s",
                (rerun["report_id"],),
            )
            rerun_report_row = cursor.fetchone()
            assert rerun_report_row is not None
            cursor.execute(
                f"SELECT * FROM {_table(contract, 'artifacts')} WHERE id=%s",
                (rerun_report_row["artifact_id"],),
            )
            rerun_report_artifact = cursor.fetchone()
            cursor.execute(
                f"SELECT artifact_id, artifact_role FROM "
                f"{_table(contract, 'run_artifacts')} WHERE run_id=%s",
                (first_run["run_id"],),
            )
            run_artifacts = cursor.fetchall()

    assert source_artifact is not None
    assert source_artifact["content_sha256"] == source["sha256"]
    assert source_artifact["byte_count"] == len(source_bytes)
    assert source_artifact["storage_backend"] == "S3"
    assert source_artifact["storage_bucket"] == values["artifact_bucket"]
    canonical_key = contract["artifact_storage"]["canonical_key_template"].format(
        artifact_kind="source_trace_jsonl",
        sha256_prefix=source["sha256"][:2],
        sha256=source["sha256"],
    )
    assert source_artifact["storage_key"] == canonical_key
    canonical_head = s3.head_object(
        Bucket=values["artifact_bucket"],
        Key=canonical_key,
        ChecksumMode="ENABLED",
    )
    assert canonical_head["ServerSideEncryption"] == "aws:kms"
    assert canonical_head["ChecksumSHA256"] == head["ChecksumSHA256"]
    canonical_source = s3.get_object(
        Bucket=values["artifact_bucket"], Key=canonical_key
    )["Body"].read()
    assert canonical_source == source_bytes
    assert import_row is not None
    assert import_row["source_artifact_id"] == source_artifact["id"]
    assert import_row["evidence_class"] == source["evidence_class"]
    assert import_row["source_sha256"] == source["sha256"]
    assert import_row["rejected_record_count"] == 14
    assert import_row["rejection_summary"] == {"SOURCE_EXECUTION_INCOMPLETE": 14}
    assert run_row is not None
    assert run_row["import_id"] == import_row["id"]
    assert run_row["workflow_id"] == first_run["workflow_id"]
    assert run_row["attempt_number"] == first_run["attempt_number"]
    assert run_row["status"] in {"COMPLETED", "COMPLETED_WITH_GAPS"}
    assert facts["physical_record_count"]["value_json"] == 200
    assert facts["source_status_counts"]["value_json"] == source["status_counts"]
    assert facts["usable_conversation_count"]["value_json"] == 186
    assert facts["rejected_record_count"]["value_json"] == 14
    assert facts["rejection_summary"]["value_json"] == {
        "SOURCE_EXECUTION_INCOMPLETE": 14
    }
    assert all(fact["authority"] == "DETERMINISTIC" for fact in facts.values())
    assert report_row["run_id"] == run_row["id"]
    assert report_artifact is not None
    assert report_artifact["storage_backend"] == "S3"
    assert rerun_report_artifact is not None
    assert rerun_report_artifact["id"] != report_artifact["id"]
    assert {(item["artifact_id"], item["artifact_role"]) for item in run_artifacts} >= {
        (report_artifact["id"], "CANONICAL_REPORT")
    }

    report_path = contract["api"]["report_path"].format(
        report_id=first_run["report_id"]
    )
    report = _get_json(values["api_origin"], report_path)
    assert report["artifact_kind"] == "labs_report"
    assert report["schema_version"] == 1
    assert report["report_id"] == first_run["report_id"]
    understanding = report["setup"]["understanding"]
    assert understanding["physical_record_count"] == source["physical_record_count"]
    assert (
        understanding["usable_conversation_count"]
        == source["usable_conversation_count"]
    )
    assert understanding["source_status_counts"] == source["status_counts"]
    assert report["evidence_class"] == source["evidence_class"]
    assert report["lineage"]["source_sha256"] == source["sha256"]
    assert report["results"]["accounting"]["actual_cost_usd"] is None

    report_object = s3.get_object(
        Bucket=report_artifact["storage_bucket"], Key=report_artifact["storage_key"]
    )
    assert report_object["ServerSideEncryption"] == "aws:kms"
    report_bytes = report_object["Body"].read()
    assert hashlib.sha256(report_bytes).hexdigest() == report_artifact["content_sha256"]
    assert hashlib.sha256(report_bytes).hexdigest() == report_row["report_hash"]
    assert json.loads(report_bytes) == report

    source_record = records[0]
    record_id = source_record["case_id"]
    record_path = contract["api"]["source_record_path"].format(
        import_id=first_import["import_id"], record_id=record_id
    )
    record_response = _get_json(values["api_origin"], record_path)
    assert record_response["schema_version"] == 1
    assert record_response["availability"] == "AVAILABLE"
    assert record_response["import_id"] == first_import["import_id"]
    assert record_response["source_artifact_sha256"] == source["sha256"]
    assert record_response["record_id"] == record_id
    assert record_response["evidence_class"] == source["evidence_class"]
    assert record_response["record"] == source_record

    if report["conversations"]:
        expected_conversation = report["conversations"][0]
        conversation_path = contract["api"]["conversation_path"].format(
            conversation_id=expected_conversation["conversation_id"]
        )
        conversation_response = _get_json(values["api_origin"], conversation_path)
        assert conversation_response["schema_version"] == 1
        assert conversation_response["availability"] == "AVAILABLE"
        assert conversation_response["report_id"] == report["report_id"]
        assert conversation_response["report_hash"] == report_row["report_hash"]
        assert conversation_response["conversation"] == expected_conversation

    # Acceptance resources are disposable. Restore exact bytes even when an
    # assertion fails so this localized degradation check is recoverable.
    report_bucket = report_artifact["storage_bucket"]
    report_key = report_artifact["storage_key"]
    report_head = s3.head_object(Bucket=report_bucket, Key=report_key)
    put_options: dict[str, Any] = {
        "Bucket": report_bucket,
        "Key": report_key,
        "Body": report_bytes,
        "ServerSideEncryption": "aws:kms",
        "Metadata": report_head["Metadata"],
    }
    if report_head.get("SSEKMSKeyId"):
        put_options["SSEKMSKeyId"] = report_head["SSEKMSKeyId"]
    if report_head.get("ContentType"):
        put_options["ContentType"] = report_head["ContentType"]
    if report_head.get("ChecksumSHA256"):
        put_options["ChecksumSHA256"] = report_head["ChecksumSHA256"]
    s3.delete_object(Bucket=report_bucket, Key=report_key)
    try:
        status, missing = _get_error_json(values["api_origin"], report_path)
        assert status == 503
        assert missing["code"] == "ARTIFACT_MISSING"
        assert missing["availability"] == "DEGRADED_ARTIFACT_MISSING"
        assert missing["report_id"] == first_run["report_id"]

        rerun_report_path = contract["api"]["report_path"].format(
            report_id=rerun["report_id"]
        )
        assert (
            _get_json(values["api_origin"], rerun_report_path)["report_id"]
            == rerun["report_id"]
        )
        assert _get_json(values["api_origin"], record_path)["record"] == source_record
    finally:
        s3.put_object(**put_options)
