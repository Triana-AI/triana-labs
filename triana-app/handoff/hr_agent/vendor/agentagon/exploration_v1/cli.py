"""CLI for generalized semantic cold-start exploration."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path

from agentagon.evals.adapters import default_trace_adapter_registry
from agentagon.evals.models import ResetPolicy
from agentagon.exploration_v1.llm import CachedLiteLLMModel
from agentagon.exploration_v1.pipeline import freeze_review, run_exploration, write_exploration_artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--traces", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--customer-context", default="")
    run.add_argument("--customer-context-file", type=Path)
    run.add_argument("--adapter", default="normalized-jsonl-v1")
    run.add_argument("--adapter-class", help="Optional module:Class trace adapter")
    run.add_argument("--env-file", type=Path)
    run.add_argument("--model", default="openrouter/openai/gpt-4.1-mini")
    run.add_argument("--api-base", default="https://openrouter.ai/api/v1")
    run.add_argument("--batch-size", type=int, default=12)
    run.add_argument("--semantic-workers", type=int, default=6)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--exploration", type=Path, required=True)
    freeze.add_argument("--review", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        result = json.loads(args.exploration.read_text())
        review = json.loads(args.review.read_text())
        args.output.write_text(json.dumps(freeze_review(result, review), indent=2, sort_keys=True) + "\n")
        return 0
    if args.env_file:
        _load_env(args.env_file)
    if args.adapter_class:
        module_name, class_name = args.adapter_class.split(":", 1)
        adapter = getattr(importlib.import_module(module_name), class_name)()
    else:
        adapter = default_trace_adapter_registry().get(args.adapter)
    loaded = adapter.load(
        args.traces,
        default_reset_policy=ResetPolicy.ISOLATED_NAMESPACE,
    )
    bundles = loaded.bundles
    model = CachedLiteLLMModel(args.model, args.output / ".llm_cache", api_base=args.api_base)
    customer_context = args.customer_context
    if args.customer_context_file:
        customer_context = args.customer_context_file.read_text(encoding="utf-8")
    result = run_exploration(
        bundles,
        model,
        customer_context=customer_context,
        batch_size=args.batch_size,
        semantic_workers=args.semantic_workers,
    )
    result["trace_adapter"] = {
        "version": loaded.adapter_version,
        "source_path": loaded.source_path,
        "typed_gap_count": len(loaded.gaps),
    }
    result["usage"] = model.usage()
    write_exploration_artifacts(args.output, result)
    print(args.output / "REVIEW.html")
    return 0


def _load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


if __name__ == "__main__":
    raise SystemExit(main())
