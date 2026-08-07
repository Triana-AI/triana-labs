"""Black-box acceptance for proposal-only handling after an incomplete run set."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from triana_labs.trace_to_eval import run_trace_to_eval


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return encoded + (b"\n" if lf else b"")


def _manifest(tmp_path: Path, *, outcomes: bool) -> tuple[Path, dict[str, float]]:
    traces = []
    assignments = []
    rewards: dict[str, float] = {}
    for index in range(20):
        trace_id = f"trace-{index:02d}"
        traces.append(
            {
                "contract_kind": "preview_trace",
                "schema_version": 1,
                "privacy_class": "SYNTHETIC",
                "trace_id": trace_id,
                "source_trace_id": f"source-{index:02d}",
                "events": [
                    {
                        "sequence": 0,
                        "event_kind": "USER_MESSAGE",
                        "content": f"Handle synthetic request {index}.",
                    },
                    {
                        "sequence": 1,
                        "event_kind": "ASSISTANT_MESSAGE",
                        "content": "Synthetic response returned.",
                        "is_final": True,
                    },
                ],
            }
        )
        assignments.append({"group_id": f"group-{index:02d}", "trace_ids": [trace_id]})
        rewards[trace_id] = 1.0 if index % 2 == 0 else 0.0

    source = tmp_path / "traces.jsonl"
    source_bytes = b"".join(_canonical(trace, lf=True) for trace in traces)
    source.write_bytes(source_bytes)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "tau-archive",
            "adapter_version": "synthetic-v0",
            "path": str(source),
            "sha256": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
            "physical_record_count": len(traces),
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "synthetic-agent"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {"authorized": True, "model_id": "semantic-test-v0"},
        },
        "grouping": {
            "highest_dependency_key": "synthetic_case_id",
            "assignments": assignments,
        },
        "capabilities": {
            "paired_arms": False,
            "outcomes": outcomes,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": (
            [
                {
                    "trace_id": trace_id,
                    "group_id": f"group-{int(trace_id[-2:]):02d}",
                    "source": "TAU2_REWARD_INFO",
                    "reward": reward,
                    "outcome": "SUCCESS" if reward == 1.0 else "FAILURE",
                }
                for trace_id, reward in sorted(rewards.items())
            ]
            if outcomes
            else None
        ),
        "existing_evals": None,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    return manifest_path, rewards


def _handling_mode(trace_id: str) -> str:
    return (
        "TOOL_ACTION_OBSERVED",
        "HANDOFF_OR_ESCALATION",
        "INFORMATION_REQUESTED",
    )[int(trace_id[-2:]) % 3]


class _IncompleteSemanticModel:
    model_id = "semantic-test-v0"

    def __init__(self, *, completed_runs: int) -> None:
        self.completed_runs = completed_runs
        self.last_failure_code: str | None = None

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: dict[str, Any],
        schema: Any,
    ) -> dict[str, Any]:
        del system, schema
        run_index = int(stage.removeprefix("semantic-run-").split("/", 1)[0])
        if run_index > self.completed_runs:
            self.last_failure_code = "SEMANTIC_BUDGET_EXCEEDED"
            raise ValueError("SEMANTIC_BUDGET_EXCEEDED")
        if "/facets-" in stage:
            return {
                "facets": [
                    {
                        "trace_id": trace["trace_id"],
                        "demand_summary": "Handle a synthetic request.",
                        "goal_label": f"synthetic-goal-{int(trace['trace_id'][-2:]) % 3}",
                        "handling_mode": _handling_mode(trace["trace_id"]),
                        "claimed_action": "FALSE",
                        "terminal_summary": "A response was returned.",
                        "evidence_quotes": ["USER_MESSAGE:"],
                    }
                    for trace in payload["traces"]
                ]
            }
        return {
            "populations": [
                {
                    "label": row["display_label"],
                    "description": "A synthetic user-demand proposal.",
                    "kind": "PROPOSED_GOAL",
                    "member_labels": [row["label"]],
                }
                for row in payload["labels"]
            ]
        }

    def lineage(self) -> dict[str, Any]:
        return {
            "provider": "SYNTHETIC_TEST_BOUNDARY",
            "model_id": self.model_id,
            "last_failure_code": self.last_failure_code,
            "retry_policy": "NONE",
            "fallback_policy": "NONE",
        }

    def record_failure(self, code: str) -> None:
        self.last_failure_code = code


def _assert_partial_safety(report: dict[str, Any], output: Path) -> dict[str, Any]:
    queue = json.loads((output / "review_queue.json").read_bytes())
    assert report["populations"] == []
    assert report["behavior_candidate_inventory"] == []
    assert report["qualified_eval_inventory"] == []
    assert report["eval_proposals"] == []
    assert report["review_state"] == {"state": "NOT_AVAILABLE", "ruling_count": 0}
    assert queue["items"] == []
    assert report["stability"] == {
        "semantic_run_count": 1,
        "state": "PARTIAL",
        "disagreements": [],
        "rerun_selection": "NONE",
    }
    assert "SEMANTIC_BUDGET_EXCEEDED" in {gap["code"] for gap in report["gaps"]}
    partial = report["partial_handling_evidence"]
    assert partial["state"] == "PARTIAL"
    assert partial["authority"] == "PROPOSAL_ONLY"
    assert partial["completed_run_count"] == 1
    assert [run["run_index"] for run in partial["runs"]] == [1]
    return partial


def test_completed_run_survives_as_partial_handling_with_exact_outcome_join(
    tmp_path: Path,
) -> None:
    manifest, rewards = _manifest(tmp_path, outcomes=True)
    output = tmp_path / "output"
    report = run_trace_to_eval(
        manifest, output, semantic_model=_IncompleteSemanticModel(completed_runs=1)
    )

    partial = _assert_partial_safety(report, output)
    items = partial["runs"][0]["items"]
    development_ids = sorted(
        row["trace_id"]
        for row in report["conversation_inventory"]
        if row["split"] == "DEVELOPMENT"
    )
    assert [item["trace_id"] for item in items] == development_ids
    assert all(
        item["handling_mode"] == _handling_mode(item["trace_id"]) for item in items
    )

    expected: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"trace_ids": [], "success_count": 0, "failure_count": 0, "reward": 0.0}
    )
    for trace_id in development_ids:
        row = expected[_handling_mode(trace_id)]
        row["trace_ids"].append(trace_id)
        row["success_count"] += rewards[trace_id] == 1.0
        row["failure_count"] += rewards[trace_id] != 1.0
        row["reward"] += rewards[trace_id]
    expected_rows = [
        {
            "handling_mode": mode,
            "denominator": len(row["trace_ids"]),
            "trace_ids": row["trace_ids"],
            "success_count": row["success_count"],
            "failure_count": row["failure_count"],
            "mean_reward": row["reward"] / len(row["trace_ids"]),
        }
        for mode, row in sorted(expected.items())
    ]
    assert partial["outcome_by_handling_mode"] == expected_rows
    assert sum(row["denominator"] for row in expected_rows) == len(development_ids)


def test_partial_handling_without_authoritative_outcomes_invents_no_aggregate(
    tmp_path: Path,
) -> None:
    manifest, _ = _manifest(tmp_path, outcomes=False)
    output = tmp_path / "output"
    report = run_trace_to_eval(
        manifest, output, semantic_model=_IncompleteSemanticModel(completed_runs=1)
    )

    partial = _assert_partial_safety(report, output)
    assert "outcome_by_handling_mode" not in partial
    assert "outcome_analytics" not in report


def test_failure_before_first_completed_run_exposes_no_partial_handling(
    tmp_path: Path,
) -> None:
    manifest, _ = _manifest(tmp_path, outcomes=True)
    output = tmp_path / "output"
    report = run_trace_to_eval(
        manifest, output, semantic_model=_IncompleteSemanticModel(completed_runs=0)
    )

    queue = json.loads((output / "review_queue.json").read_bytes())
    assert report["stability"] == {
        "semantic_run_count": 0,
        "state": "UNAVAILABLE",
        "disagreements": [],
        "rerun_selection": "NONE",
    }
    assert "partial_handling_evidence" not in report
    assert report["populations"] == report["eval_proposals"] == []
    assert report["behavior_candidate_inventory"] == []
    assert queue["items"] == []
    assert "SEMANTIC_BUDGET_EXCEEDED" in {gap["code"] for gap in report["gaps"]}
