from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from conftest import SECRET, refresh_manifest, write_json


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("tau2_luna_local") is None,
    reason="production package absent; test_package_contract owns the RED signal",
)


def assert_invalid(run_dir: Path, expected_reason: str) -> None:
    from tau2_luna_local.verify import verify_bundle

    report = verify_bundle(run_dir, secret_values=(SECRET,))
    assert report["valid"] is False
    assert expected_reason in {reason["code"] for reason in report["reasons"]}


def test_valid_bundle_verifies_and_preserves_typed_telemetry(valid_bundle: Path) -> None:
    from tau2_luna_local.verify import verify_bundle

    report = verify_bundle(valid_bundle, secret_values=(SECRET,))
    assert report["valid"] is True
    completeness = json.loads((valid_bundle / "completeness.json").read_text())
    assert completeness["telemetry"]["response.reasoning"]["state"] == "CAPTURED"
    assert completeness["telemetry"]["provider_private_chain_of_thought"]["state"] == "NOT_RETURNED"
    results = json.loads((valid_bundle / "tau2-results.json").read_text())
    assert results["messages"][0]["tool_calls"][0] == {
        "id": "tool-1",
        "name": "lookup_order",
        "arguments": {"order_id": "O-1"},
    }
    assert results["messages"][1] == {
        "role": "tool",
        "tool_call_id": "tool-1",
        "name": "lookup_order",
        "content": {"status": "shipped"},
    }
    assert results["termination_reason"] == "agent_stop"
    assert results["reward"] == 1.0
    assert results["reward_breakdown"] == {"task": 1.0}
    assert results["evaluator_checks"] == [{"name": "order_status", "passed": True}]


@pytest.mark.parametrize(
    ("artifact", "reason"),
    [
        ("events.jsonl", "ARTIFACT_HASH_MISMATCH"),
        ("spans.jsonl", "ARTIFACT_HASH_MISMATCH"),
        ("tau2-results.json", "ARTIFACT_HASH_MISMATCH"),
    ],
)
def test_artifact_tamper_fails(valid_bundle: Path, artifact: str, reason: str) -> None:
    path = valid_bundle / artifact
    path.write_bytes(path.read_bytes() + b" ")
    assert_invalid(valid_bundle, reason)


def test_orphan_model_request_fails_even_with_refreshed_hash(valid_bundle: Path) -> None:
    lines = (valid_bundle / "events.jsonl").read_text().splitlines()
    (valid_bundle / "events.jsonl").write_text(lines[0] + "\n")
    refresh_manifest(valid_bundle)
    assert_invalid(valid_bundle, "MODEL_TERMINAL_MISSING")


def test_missing_tau2_result_fails(valid_bundle: Path) -> None:
    (valid_bundle / "tau2-results.json").unlink()
    assert_invalid(valid_bundle, "REQUIRED_ARTIFACT_MISSING")


def test_malformed_or_duplicate_sequence_fails(valid_bundle: Path) -> None:
    path = valid_bundle / "events.jsonl"
    path.write_text(path.read_text() + "{not-json}\n")
    refresh_manifest(valid_bundle)
    assert_invalid(valid_bundle, "EVENT_CHAIN_INVALID")


def test_unexpected_artifact_fails(valid_bundle: Path) -> None:
    (valid_bundle / "provider-dump.txt").write_text("unexpected")
    assert_invalid(valid_bundle, "UNEXPECTED_ARTIFACT")


def test_silent_required_field_omission_fails(valid_bundle: Path) -> None:
    completeness_path = valid_bundle / "completeness.json"
    completeness = json.loads(completeness_path.read_text())
    del completeness["telemetry"]["response.headers"]
    write_json(completeness_path, completeness)
    assert_invalid(valid_bundle, "TELEMETRY_FIELD_UNCLASSIFIED")


@pytest.mark.parametrize("field", ["response.usage", "response.cost", "response.headers"])
def test_missing_observables_are_typed_non_success_not_zero(valid_bundle: Path, field: str) -> None:
    completeness_path = valid_bundle / "completeness.json"
    completeness = json.loads(completeness_path.read_text())
    completeness["telemetry"][field] = {
        "state": "NOT_RETURNED",
        "source": "azure",
        "reason": "fake provider omitted field",
    }
    write_json(completeness_path, completeness)

    from tau2_luna_local.verify import verify_bundle

    report = verify_bundle(valid_bundle, secret_values=(SECRET,))
    assert report["valid"] is False
    assert report["telemetry"][field]["state"] == "NOT_RETURNED"
    assert report["telemetry"][field].get("value") != 0


def test_secret_reflection_anywhere_is_fatal(valid_bundle: Path) -> None:
    completeness_path = valid_bundle / "completeness.json"
    completeness = json.loads(completeness_path.read_text())
    completeness["leak"] = {"nested": ["safe", SECRET]}
    write_json(completeness_path, completeness)
    assert_invalid(valid_bundle, "SECRET_REFLECTION")
