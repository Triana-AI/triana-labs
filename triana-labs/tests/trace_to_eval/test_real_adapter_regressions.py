"""Independent regressions discovered by auditing real Trace-to-Eval artifacts."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

from triana_labs.trace_to_eval import run_trace_to_eval
from triana_labs.trace_to_eval.adapters import prepare_evidence_manifest


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    assert isinstance(value, dict)
    return value


def test_grouped_langsmith_embedded_tools_survive_canonical_behavior_accounting(
    tmp_path: Path,
) -> None:
    """AI tool_calls and matching ToolMessage outputs are observable behavior."""

    call_id = "call-synthetic-1"
    source = tmp_path / "grouped-langsmith.jsonl"
    source_bytes = _canonical(
        {
            "trace_id": "raw-trace-synthetic-1",
            "session_key": "session-synthetic-1",
            "start_time": "2026-08-07T00:00:00Z",
            "runs": [
                {
                    "id": "run-synthetic-1",
                    "run_type": "chain",
                    "dotted_order": "1",
                    "status": "success",
                    "inputs": {
                        "messages": [
                            {
                                "type": "human",
                                "content": "Look up the synthetic order.",
                            },
                            {
                                "type": "constructor",
                                "id": [
                                    "langchain",
                                    "schema",
                                    "messages",
                                    "AIMessage",
                                ],
                                "kwargs": {
                                    "content": "",
                                    "tool_calls": [
                                        {
                                            "id": call_id,
                                            "name": "lookup_synthetic_order",
                                            "args": {"order_id": "synthetic-1"},
                                            "type": "tool_call",
                                        }
                                    ],
                                },
                            },
                            {
                                "type": "constructor",
                                "id": [
                                    "langchain",
                                    "schema",
                                    "messages",
                                    "ToolMessage",
                                ],
                                "kwargs": {
                                    "content": "Synthetic order is ready.",
                                    "tool_call_id": call_id,
                                    "status": "success",
                                },
                            },
                        ]
                    },
                    "outputs": {
                        "generations": [
                            [
                                {
                                    "message": {
                                        "type": "ai",
                                        "content": "The synthetic order is ready.",
                                    }
                                }
                            ]
                        ]
                    },
                }
            ],
        },
        lf=True,
    )
    source.write_bytes(source_bytes)

    prepared = tmp_path / "prepared"
    manifest_path = prepare_evidence_manifest(
        source,
        prepared,
        source_kind="langsmith-grouped-jsonl",
    )
    preview_trace = json.loads(
        (prepared / "preview_traces.jsonl").read_bytes().splitlines()[0]
    )
    events = preview_trace["events"]
    tool_call = next(event for event in events if event["event_kind"] == "TOOL_CALL")
    tool_result = next(
        event for event in events if event["event_kind"] == "TOOL_RESULT"
    )

    assert tool_call == {
        "sequence": 1,
        "event_kind": "TOOL_CALL",
        "call_id": call_id,
        "tool_name": "lookup_synthetic_order",
        "arguments": {"order_id": "synthetic-1"},
    }
    assert tool_result == {
        "sequence": 2,
        "event_kind": "TOOL_RESULT",
        "call_id": call_id,
        "result_state": "SUCCEEDED",
        "result": "Synthetic order is ready.",
    }
    assert [event["event_kind"] for event in events] == [
        "USER_MESSAGE",
        "TOOL_CALL",
        "TOOL_RESULT",
        "ASSISTANT_MESSAGE",
        "TERMINAL",
    ]

    report = run_trace_to_eval(manifest_path, tmp_path / "report")
    assert report["behavior_analytics"]["tool_observed_conversation_count"] == 1
    assert report["behavior_analytics"]["event_kind_counts"] == {
        "ASSISTANT_MESSAGE": 1,
        "TERMINAL": 1,
        "TOOL_CALL": 1,
        "TOOL_RESULT": 1,
        "USER_MESSAGE": 1,
    }


def test_tau_archive_without_outcome_payload_cannot_claim_outcome_capability(
    tmp_path: Path,
) -> None:
    """The archive container alone is not outcome truth."""

    result = {
        "simulations": [
            {
                "messages": [
                    {"role": "user", "content": "Synthetic task."},
                    {"role": "assistant", "content": "Synthetic completion."},
                ]
            }
        ]
    }
    result_bytes = _canonical(result)
    archive = tmp_path / "tau.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        member = tarfile.TarInfo(
            "tasks/task-synthetic/attempts/attempt-synthetic/tau2-results.json"
        )
        member.size = len(result_bytes)
        member.mtime = 0
        bundle.addfile(member, io.BytesIO(result_bytes))

    manifest_path = prepare_evidence_manifest(
        archive,
        tmp_path / "prepared",
        source_kind="tau-archive",
    )
    manifest = _read_object(manifest_path)
    assert manifest["outcomes"] is None
    assert manifest["capabilities"]["outcomes"] is False

    report = run_trace_to_eval(manifest_path, tmp_path / "report")
    assert report["capabilities"]["outcomes"] is False
    assert {
        "code": "OUTCOMES_UNAVAILABLE",
        "capability": "OUTCOMES",
        "state": "UNAVAILABLE",
    } in report["gaps"]
    assert "outcome" not in {
        key.casefold() for item in report["qualified_eval_inventory"] for key in item
    }


def test_prepared_manifest_binds_raw_source_and_normalized_engine_input(
    tmp_path: Path,
) -> None:
    """Raw-to-session accounting remains reproducible without retaining raw content."""

    source = tmp_path / "grouped-source.jsonl"
    source_bytes = _canonical(
        {
            "trace_id": "raw-lineage-trace",
            "session_key": "raw-lineage-session",
            "runs": [
                {
                    "id": "raw-lineage-run",
                    "run_type": "chain",
                    "inputs": {
                        "messages": [{"type": "human", "content": "Synthetic input."}]
                    },
                    "outputs": {
                        "generations": [
                            [
                                {
                                    "message": {
                                        "type": "ai",
                                        "content": "Synthetic output.",
                                    }
                                }
                            ]
                        ]
                    },
                }
            ],
        },
        lf=True,
    )
    source.write_bytes(source_bytes)
    prepared = tmp_path / "prepared"
    manifest_path = prepare_evidence_manifest(
        source,
        prepared,
        source_kind="langsmith-grouped-jsonl",
    )
    manifest = _read_object(manifest_path)
    normalized_bytes = (prepared / "preview_traces.jsonl").read_bytes()

    assert manifest["source"]["sha256"] == (
        "sha256:" + hashlib.sha256(normalized_bytes).hexdigest()
    )
    assert manifest["source"]["upstream_sha256"] == (
        "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    )
    assert manifest["source"]["upstream_source_kind"] == ("langsmith-grouped-jsonl")
    assert manifest["source"]["upstream_physical_record_count"] == 1


def test_grouped_session_reconstruction_selects_complete_runs_without_echoes(
    tmp_path: Path,
) -> None:
    """Nested control/LLM echoes cannot inflate one session's message history."""

    first_user = {"type": "human", "content": "Synthetic first request."}
    first_answer = {"type": "ai", "content": "Synthetic first answer."}
    second_user = {"type": "human", "content": "Synthetic second request."}
    source_rows = [
        {
            "trace_id": "raw-session-row-1",
            "session_key": "session-reconstruction-synthetic",
            "start_time": "2026-08-07T00:01:00Z",
            "runs": [
                {
                    "id": "row-1-child",
                    "run_type": "llm",
                    "dotted_order": "1.1",
                    "end_time": "2026-08-07T00:01:01Z",
                    "inputs": {"messages": [first_user]},
                    "outputs": {
                        "generations": [
                            [
                                {
                                    "message": {
                                        "type": "ai",
                                        "content": "Synthetic intermediate answer.",
                                    }
                                }
                            ]
                        ]
                    },
                },
                {
                    "id": "row-1-parent",
                    "run_type": "chain",
                    "dotted_order": "1.2",
                    "end_time": "2026-08-07T00:01:02Z",
                    "inputs": {"messages": [first_user]},
                    "outputs": {"generations": [[{"message": first_answer}]]},
                },
                {
                    "id": "tool-row-1",
                    "name": "first_synthetic_tool",
                    "run_type": "tool",
                    "dotted_order": "1.3",
                    "inputs": {"value": "synthetic-one"},
                    "outputs": {"value": "synthetic-one-result"},
                },
            ],
        },
        {
            "trace_id": "raw-session-row-2",
            "session_key": "session-reconstruction-synthetic",
            "start_time": "2026-08-07T00:02:00Z",
            "runs": [
                {
                    "id": "row-2-window",
                    "run_type": "llm",
                    "dotted_order": "2.1",
                    "end_time": "2026-08-07T00:02:01Z",
                    "inputs": {"messages": [second_user]},
                    "outputs": {
                        "generations": [
                            [
                                {
                                    "message": {
                                        "type": "ai",
                                        "content": "Synthetic window-only answer.",
                                    }
                                }
                            ]
                        ]
                    },
                },
                {
                    "id": "row-2-complete-a",
                    "run_type": "chain",
                    "dotted_order": "2.2",
                    "end_time": "2026-08-07T00:02:02Z",
                    "inputs": {"messages": [first_user, first_answer, second_user]},
                    "outputs": {
                        "generations": [
                            [
                                {
                                    "message": {
                                        "type": "ai",
                                        "content": "Synthetic stale complete answer.",
                                    }
                                }
                            ]
                        ]
                    },
                },
                {
                    "id": "row-2-complete-z",
                    "run_type": "chain",
                    "dotted_order": "2.3",
                    "end_time": "2026-08-07T00:02:02Z",
                    "inputs": {"messages": [first_user, first_answer, second_user]},
                    "outputs": {
                        "generations": [
                            [
                                {
                                    "message": {
                                        "type": "ai",
                                        "content": "Synthetic final second answer.",
                                    }
                                }
                            ]
                        ]
                    },
                },
                {
                    "id": "tool-row-2",
                    "name": "second_synthetic_tool",
                    "run_type": "tool",
                    "dotted_order": "2.4",
                    "inputs": {"value": "synthetic-two"},
                    "outputs": {"value": "synthetic-two-result"},
                },
            ],
        },
    ]
    source = tmp_path / "grouped-session.jsonl"
    source.write_bytes(b"".join(_canonical(row, lf=True) for row in source_rows))
    prepared = tmp_path / "prepared"
    manifest_path = prepare_evidence_manifest(
        source,
        prepared,
        source_kind="langsmith-grouped-jsonl",
    )
    manifest = _read_object(manifest_path)
    preview_trace = json.loads(
        (prepared / "preview_traces.jsonl").read_bytes().splitlines()[0]
    )
    events = preview_trace["events"]
    observed_messages = [
        (event["event_kind"], event["content"])
        for event in events
        if event["event_kind"] in {"USER_MESSAGE", "ASSISTANT_MESSAGE"}
    ]

    assert observed_messages == [
        ("USER_MESSAGE", "Synthetic first request."),
        ("ASSISTANT_MESSAGE", "Synthetic first answer."),
        ("USER_MESSAGE", "Synthetic second request."),
        ("ASSISTANT_MESSAGE", "Synthetic final second answer."),
    ]
    assert {
        event["call_id"] for event in events if event["event_kind"] == "TOOL_CALL"
    } == {"ls-tool-row-1", "ls-tool-row-2"}
    assert {
        event["call_id"] for event in events if event["event_kind"] == "TOOL_RESULT"
    } == {"ls-tool-row-1", "ls-tool-row-2"}

    reconstruction = manifest["source"]["session_reconstruction"]
    assert reconstruction["policy"] == "MOST_COMPLETE_MESSAGE_RUN_PER_GROUP_V0"
    assert reconstruction["ordering"] == [
        "INPUT_MESSAGE_COUNT",
        "END_TIME",
        "RUN_ID",
    ]
    assert reconstruction["exact_duplicate_key"] == ["ROLE", "CONTENT"]
    assert reconstruction["suppressed_fact_count"] >= 2
    assert set(reconstruction) == {
        "policy",
        "ordering",
        "exact_duplicate_key",
        "suppressed_fact_count",
    }


def test_tau_official_rewards_create_truthful_outcomes_or_fail_closed(
    tmp_path: Path,
) -> None:
    """Outcome capability requires finite official reward truth for every trace."""

    def archive_with_rewards(path: Path, rewards: dict[str, float | None]) -> Path:
        with tarfile.open(path, "w:gz") as bundle:
            for task_id, reward in sorted(rewards.items()):
                simulation: dict[str, Any] = {
                    "messages": [
                        {"role": "user", "content": f"Synthetic task {task_id}."},
                        {
                            "role": "assistant",
                            "content": f"Synthetic completion {task_id}.",
                        },
                    ]
                }
                if reward is not None:
                    simulation["reward_info"] = {"reward": reward}
                payload = _canonical({"simulations": [simulation]})
                member = tarfile.TarInfo(
                    f"tasks/{task_id}/attempts/attempt-{task_id}/tau2-results.json"
                )
                member.size = len(payload)
                member.mtime = 0
                bundle.addfile(member, io.BytesIO(payload))
        return path

    complete_archive = archive_with_rewards(
        tmp_path / "complete-rewards.tar.gz",
        {"task-failure": 0.0, "task-success": 1.0},
    )
    complete_manifest_path = prepare_evidence_manifest(
        complete_archive,
        tmp_path / "complete-prepared",
        source_kind="tau-archive",
    )
    complete_manifest = _read_object(complete_manifest_path)
    assert complete_manifest["capabilities"]["outcomes"] is True
    assert complete_manifest["outcomes"] == [
        {
            "trace_id": "tau2-task-failure",
            "group_id": "task-failure",
            "source": "TAU2_REWARD_INFO",
            "reward": 0.0,
            "outcome": "FAILURE",
        },
        {
            "trace_id": "tau2-task-success",
            "group_id": "task-success",
            "source": "TAU2_REWARD_INFO",
            "reward": 1.0,
            "outcome": "SUCCESS",
        },
    ]

    complete_report = run_trace_to_eval(
        complete_manifest_path,
        tmp_path / "complete-report",
    )
    assert complete_report["outcome_analytics"] == {
        "authority": "DETERMINISTIC",
        "source": "TAU2_REWARD_INFO",
        "denominator": 2,
        "success_count": 1,
        "failure_count": 1,
        "mean_reward": 0.5,
    }
    rendered = _canonical(complete_report).decode().casefold()
    assert "first-broken-link" not in rendered
    assert '"l4"' not in rendered

    mixed_archive = archive_with_rewards(
        tmp_path / "mixed-rewards.tar.gz",
        {"task-missing": None, "task-success": 1.0},
    )
    mixed_manifest_path = prepare_evidence_manifest(
        mixed_archive,
        tmp_path / "mixed-prepared",
        source_kind="tau-archive",
    )
    mixed_manifest = _read_object(mixed_manifest_path)
    assert mixed_manifest["capabilities"]["outcomes"] is False
    assert mixed_manifest["outcomes"] is None
    mixed_report = run_trace_to_eval(
        mixed_manifest_path,
        tmp_path / "mixed-report",
    )
    assert "outcome_analytics" not in mixed_report
    assert {
        "code": "OUTCOMES_UNAVAILABLE",
        "capability": "OUTCOMES",
        "state": "UNAVAILABLE",
    } in mixed_report["gaps"]
