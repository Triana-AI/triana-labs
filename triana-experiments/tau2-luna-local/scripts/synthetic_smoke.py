from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tau2_luna_local.capture import CompletionCapture
from tau2_luna_local.config import load_config
from tau2_luna_local.journal import EventJournal
from tau2_luna_local.otel import LocalTelemetry
from tau2_luna_local.runner import _write_manifest, build_completeness
from tau2_luna_local.serde import write_canonical_json
from tau2_luna_local.verify import verify_bundle


class FakeResponse(dict[str, Any]):
    def __init__(self) -> None:
        super().__init__(
            id="synthetic-response",
            created=1_750_000_000,
            choices=[
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "synthetic response",
                        "reasoning_content": "synthetic returned summary",
                        "tool_calls": [],
                    },
                }
            ],
            usage={
                "prompt_tokens": 2,
                "completion_tokens": 3,
                "total_tokens": 5,
                "prompt_tokens_details": {"cached_tokens": 0},
                "completion_tokens_details": {"reasoning_tokens": 1},
            },
        )
        self._hidden_params = {"response_cost": 0.001, "safe": "synthetic"}
        self._response_headers = {"x-request-id": "synthetic-request"}

    def model_dump(self) -> dict[str, Any]:
        return dict(self)


def main() -> int:
    secret = "synthetic-secret-never-persist"
    with tempfile.TemporaryDirectory(prefix="tau2-luna-local-") as temporary:
        root = Path(temporary)
        config = load_config(
            {
                "AZURE_API_KEY": secret,
                "AZURE_API_BASE": "https://synthetic.openai.azure.com",
                "AZURE_API_VERSION": "synthetic-no-network",
                "TAU2_LUNA_DEPLOYMENT": "synthetic-luna",
                "TAU2_TRACE_ROOT": str(root),
            }
        )
        run_dir = root / "run-synthetic"
        run_dir.mkdir()
        target = SimpleNamespace(completion=lambda **_: FakeResponse())
        with (
            EventJournal(run_dir / "events.jsonl", timestamp_ns=iter(range(100, 110)).__next__) as journal,
            LocalTelemetry(run_dir / "spans.jsonl", run_id="run-synthetic", secrets=(secret,)) as telemetry,
        ):
            journal.append("run.started", {"run_id": "run-synthetic"})
            with CompletionCapture(
                target=target,
                event_sink=journal.append,
                span_sink=telemetry.record_model_span,
                secrets=(secret,),
                wall_time_ns=iter([1_000, 1_100]).__next__,
                monotonic_ns=iter([10, 35]).__next__,
                call_id_factory=lambda: "call-synthetic",
                span_id_factory=lambda: "span-synthetic",
            ):
                target.completion(
                    model=config.model,
                    api_base=config.api_base,
                    api_version=config.api_version,
                    api_key=secret,
                    messages=[{"role": "user", "content": "synthetic"}],
                    tools=[],
                    tool_choice="auto",
                    num_retries=0,
                )
            journal.append("benchmark.finished", {"run_id": "run-synthetic", "result_published": True})
            journal.append("run.finished", {"run_id": "run-synthetic", "benchmark_succeeded": True})
        write_canonical_json(
            run_dir / "tau2-results.json",
            {
                "info": {"seed": 1729},
                "tasks": [{"id": "synthetic"}],
                "simulations": [
                    {
                        "task_id": "synthetic",
                        "trial": 0,
                        "seed": 1729,
                        "messages": [],
                        "termination_reason": "agent_stop",
                        "agent_cost": 0.001,
                        "user_cost": 0.0,
                        "reward_info": {"reward": 1.0, "reward_breakdown": {"task": 1.0}},
                    }
                ],
            },
        )
        write_canonical_json(
            run_dir / "completeness.json", build_completeness(run_dir, benchmark_succeeded=True)
        )
        _write_manifest(
            run_dir,
            run_id="run-synthetic",
            config=config,
            provenance={
                "distribution_version": "synthetic-no-network",
                "commit": "f8de30c298689cbe0117d76a378e7315a17e5bd8",
                "url": "https://github.com/sierra-research/tau2-bench.git",
            },
        )
        report = verify_bundle(run_dir, secret_values=(secret,))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
