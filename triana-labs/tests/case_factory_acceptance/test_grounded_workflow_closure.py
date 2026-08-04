"""Black-box LABS-04/06 grounded-workflow closure acceptance."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


def _load(path: Path, name: str, conftest: Any = None) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    prior = sys.modules.get("conftest")
    if conftest is not None:
        sys.modules["conftest"] = conftest
    try:
        spec.loader.exec_module(module)
    finally:
        if prior is not None:
            sys.modules["conftest"] = prior
        elif conftest is not None:
            sys.modules.pop("conftest", None)
    return module


HERE = Path(__file__).parent
HARNESS = _load(HERE / "conftest.py", "labs046_case_harness")
RESTRICTED = _load(
    HERE / "test_restricted_runtime_outcomes.py", "labs046_restricted_harness", HARNESS
)
ENVIRON, ScriptedClock = HARNESS.ENVIRON, HARNESS.ScriptedClock
artifact_hash, build_upstream = HARNESS.artifact_hash, HARNESS.build_upstream
canonical, config_value, trace, write_config = (
    HARNESS.canonical,
    HARNESS.config_value,
    HARNESS.trace,
    HARNESS.write_config,
)
ScriptedRestrictedTransport = RESTRICTED.ScriptedRestrictedTransport
_field, _response, _submission = (
    RESTRICTED._field,
    RESTRICTED._response,
    RESTRICTED._submission,
)

MODE = "LABS046_WORKFLOW_CLOSURE_V1"
INVENTORY_VERSION = "LABS046_WORLD_INVENTORY_V1"
MARKDOWN = "LABS04_TIERED_CASES.md"


def _inventory(tmp_path: Path) -> Path:
    value = {
        "artifact_kind": "labs046_world_inventory",
        "schema_version": 1,
        "protocol_version": INVENTORY_VERSION,
        "data_class": "SYNTHETIC",
        "captured_at": "2026-08-03T00:00:00Z",
        "source_lineage": {
            "source_kind": "SYNTHETIC_FIXTURE",
            "source_id": "fixture-v1",
        },
        "inventory": {
            "candidate_id": [f"cand-{index:02d}" for index in range(1, 13)],
            "position_id": ["pos-01"],
        },
    }
    path = tmp_path / "world-inventory.json"
    path.write_bytes(canonical(value, lf=True))
    return path


def _closure_config(tmp_path: Path) -> Path:
    value = config_value()
    value["protocol_version"] = MODE
    value["generation"] = {
        "candidate_count": 12,
        "evidence_byte_limit": 90_000,
        "seed": 2026080104,
    }
    value["budget"] = {
        "max_usd": "8.700000",
        "reservation_usd_per_agent_call": "0.500000",
    }
    return write_config(tmp_path, value)


def _observe_all(value: Any, claim_key: str) -> None:
    if isinstance(value, dict):
        if set(value) == {"text", "basis", "claim_keys"}:
            value.update(basis="OBSERVED", claim_keys=[claim_key])
            return
        for key, item in value.items():
            if key != "grounding_claims":
                _observe_all(item, claim_key)
    elif isinstance(value, list):
        for item in value:
            _observe_all(item, claim_key)


def _closure_submission(request: Any, mutate: Any = None) -> dict[str, Any]:
    submission = _submission(request)
    catalog = _field(request, "evidence_catalog")
    handles = [trace["events"][0]["evidence_handle"] for trace in catalog["traces"][:2]]
    for index, case in enumerate(submission["cases"]):
        claim_key = f"claim_{index + 1}"
        ordinal = int(case["case_key"].removeprefix("case_"))
        selected = handles[:1] if ordinal <= 6 else handles
        related = (
            submission["personas"][index],
            submission["intents"][index],
            submission["turn_policies"][index],
            case,
        )
        for record in related:
            _observe_all(record, claim_key)
            for claim in record["grounding_claims"]:
                claim["evidence_handles"] = selected
        case.update(
            goal={
                "text": f"Complete workflow {ordinal}",
                "basis": "OBSERVED",
                "claim_keys": [claim_key],
            },
            done_when={
                "text": f"Workflow {ordinal} is confirmed complete",
                "basis": "OBSERVED",
                "claim_keys": [claim_key],
            },
            required_world_keys={
                "candidate_id": [f"cand-{ordinal:02d}"],
                "position_id": ["pos-01"],
            },
        )
    if mutate is not None:
        mutate(submission)
    return submission


def _submitted(mutate: Any = None) -> Any:
    def action(request: Any, tools: Any) -> Any:
        submission = _closure_submission(request, mutate)
        tools.submit_case_batch(submission)
        return _response("SUBMITTED", submission=submission)

    return action


def _run(
    tmp_path: Path, *, mutate: Any = None, traces: list[dict[str, Any]] | None = None
) -> tuple[Any, Any, Path]:
    observer, intelligence = build_upstream(tmp_path, traces)
    output = tmp_path / "closure-output"
    transport = ScriptedRestrictedTransport([_submitted(mutate)] * 8)
    result = importlib.import_module(
        "triana_labs.case_factory.generate"
    ).generate_restricted(
        observer,
        intelligence,
        _closure_config(tmp_path),
        output,
        cache_path=tmp_path / "cache",
        transport=transport,
        clock=ScriptedClock(list(range(0, 100_000_000, 1_000_000))),
        environ=ENVIRON,
        requested_case_count=12,
        world_inventory=_inventory(tmp_path),
    )
    return result, transport, output


def test_closure_derives_six_exact_origins_trace_union_and_manifest_hashed_tiers(
    tmp_path: Path,
) -> None:
    result, _, output = _run(tmp_path)
    assert result.outcome == "COMPLETED"
    cases = [
        json.loads(line)
        for line in (output / "case_candidates.jsonl").read_bytes().splitlines()
    ]
    assert len(cases) == 12
    assert [case["case_origin"] for case in cases].count(
        "OBSERVED_PRODUCTION_CASE"
    ) == 6
    assert [case["case_origin"] for case in cases].count("GROUNDED_EXPANDED_CASE") == 6
    assert all(
        case["goal"]["basis"] == case["done_when"]["basis"] == "OBSERVED"
        for case in cases
    )
    assert all(
        case["source_trace_ids"] == sorted(set(case["source_trace_ids"]))
        for case in cases
    )
    trace_counts = [len(case["source_trace_ids"]) for case in cases]
    assert trace_counts.count(1) == trace_counts.count(2) == 6
    markdown = (output / MARKDOWN).read_bytes()
    for heading in (
        b"# LABS-04 tiered cases",
        b"## Observed production cases",
        b"## Grounded expanded cases",
        b"## Invalid or unavailable evidence",
    ):
        assert heading in markdown
    assert b"non-authoritative" in markdown.lower()
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["artifacts"][MARKDOWN] == artifact_hash(markdown)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["cases"][0]["goal"].update(
            basis="GENERATED_VARIATION", claim_keys=[]
        ),
        lambda value: value["cases"][0]["required_world_keys"]["candidate_id"].append(
            "cand-01"
        ),
        lambda value: value["cases"][0]["required_world_keys"].update(
            candidate_id=["cand-unknown"]
        ),
        lambda value: value["cases"][0].update(
            source_trace_ids=["trace-spoof"], case_origin="OBSERVED_PRODUCTION_CASE"
        ),
    ],
)
def test_closure_rejects_generated_duplicate_unknown_or_model_authored_provenance(
    tmp_path: Path, mutate: Any
) -> None:
    result, _, output = _run(tmp_path, mutate=mutate)
    assert result.outcome == "REJECTED"
    assert result.valid_case_count == 0
    assert (output / "case_candidates.jsonl").read_bytes() == b""
    assert (
        json.loads((output / "case_factory_eval.json").read_bytes())["machine_status"]
        == "FAILED"
    )


def test_closure_evidence_uses_byte_ceiling_not_twenty_five_trace_cutoff(
    tmp_path: Path,
) -> None:
    traces = [
        trace(f"trace-{index:02d}", f"Request {index}", f"Reply {index}")
        for index in range(30)
    ]
    result, transport, output = _run(tmp_path, traces=traces)
    assert result.outcome == "COMPLETED"
    catalog = _field(transport.requests[0], "evidence_catalog")
    evidence = json.loads((output / "evidence_index.json").read_bytes())
    assert len(catalog["traces"]) > 25
    assert evidence["total_eligible_trace_count"] == 30
    assert evidence["selected_trace_count"] == len(catalog["traces"])
    assert evidence["excluded_trace_count"] == 30 - len(catalog["traces"])
    assert evidence["projected_byte_count"] <= 90_000
