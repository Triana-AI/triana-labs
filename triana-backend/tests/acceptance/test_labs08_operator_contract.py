"""Offline contract checks for the LABS-08 operator boundary.

These tests exercise the installed CLI as an external process against a tiny
HTTP recorder. They require neither AWS nor RDS and do not import production
modules. They freeze transport semantics; they do not claim the live vertical
slice is GREEN.
"""

from __future__ import annotations

import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import pytest

BACKEND = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(__file__).with_name("labs08_hrai_contract.json")
DIGEST = "76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b"


def _contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


class _Recorder(BaseHTTPRequestHandler):
    requests: list[dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
        length = int(self.headers.get("Content-Length", "0"))
        self.requests.append(
            {
                "path": self.path,
                "idempotency_key": self.headers.get("Idempotency-Key"),
                "body": json.loads(self.rfile.read(length)),
            }
        )
        response = json.dumps({"resource_id": "recorded"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def recorder() -> tuple[str, list[dict[str, Any]]]:
    _Recorder.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", _Recorder.requests
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _run_cli(origin: str, arguments: list[str]) -> None:
    completed = subprocess.run(
        ["uv", "run", "triana", *arguments],
        cwd=BACKEND,
        env={**os.environ, "TRIANA_BACKEND_API_ORIGIN": origin},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_contract_is_portable_and_freezes_canonical_artifact_identity() -> None:
    contract = _contract()
    source = contract["source"]

    assert source["sha256"] == DIGEST
    assert source["physical_record_count"] == 200
    assert source["status_counts"] == {"COMPLETED": 186, "HARNESS_ERROR": 14}
    assert source["usable_conversation_count"] == 186
    assert source["evidence_class"] == "SYNTHETIC_EXISTING_TRACE_CORPUS"
    assert "repository" not in source
    assert not any("/Users/" in str(value) for value in source.values())
    assert contract["environment"]["source_file"] == (
        "TRIANA_ACCEPTANCE_HRAI_SOURCE_FILE"
    )
    assert (
        contract["artifact_storage"]["canonical_key_template"].format(
            sha256_prefix=DIGEST[:2], sha256=DIGEST
        )
        == f"objects/sha256/76/{DIGEST}"
    )
    assert all(path.startswith("/api/v1/") for path in contract["api"].values())


def test_import_cli_uses_versioned_api_and_idempotency_header(
    recorder: tuple[str, list[dict[str, Any]]],
) -> None:
    origin, requests = recorder
    _run_cli(
        origin,
        [
            "backend",
            "import-s3",
            "--bucket",
            "operator-staging",
            "--key",
            "staging/request/source.jsonl",
            "--sha256",
            DIGEST,
            "--workspace",
            "local",
            "--agent",
            "hrai",
            "--version",
            "run-200",
            "--evidence-class",
            "SYNTHETIC_EXISTING_TRACE_CORPUS",
            "--idempotency-key",
            "labs08-hrai-import-v1",
        ],
    )

    assert requests == [
        {
            "path": _contract()["api"]["import_path"],
            "idempotency_key": "labs08-hrai-import-v1",
            "body": {
                "workspace_slug": "local",
                "agent_key": "hrai",
                "version_key": "run-200",
                "source": {
                    "bucket": "operator-staging",
                    "key": "staging/request/source.jsonl",
                    "sha256": DIGEST,
                },
                "evidence_class": "SYNTHETIC_EXISTING_TRACE_CORPUS",
            },
        }
    ]


@pytest.mark.parametrize(
    ("rerun_flag", "idempotency_key", "rerun"),
    [
        ([], "labs08-hrai-run-v1", False),
        (["--rerun"], "labs08-hrai-rerun-v1", True),
    ],
)
def test_run_cli_preserves_explicit_rerun_semantics(
    recorder: tuple[str, list[dict[str, Any]]],
    rerun_flag: list[str],
    idempotency_key: str,
    rerun: bool,
) -> None:
    origin, requests = recorder
    _run_cli(
        origin,
        [
            "backend",
            "run",
            "--import-id",
            "imp_frozen",
            *rerun_flag,
            "--idempotency-key",
            idempotency_key,
        ],
    )

    assert requests == [
        {
            "path": _contract()["api"]["run_path"],
            "idempotency_key": idempotency_key,
            "body": {"import_id": "imp_frozen", "rerun": rerun},
        }
    ]
