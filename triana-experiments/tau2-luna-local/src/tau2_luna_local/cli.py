from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import ConfigurationError, load_config
from .runner import RunRefused, run_experiment
from .verify import verify_bundle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tau2-luna-local")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run one pinned local tau-squared task")
    run.add_argument("--domain", default="retail")
    run.add_argument("--task-id")
    run.add_argument("--task-count", type=int, default=1)
    run.add_argument("--trial-count", type=int, default=1)
    run.add_argument("--seed", type=int, default=1729)
    run.add_argument("--max-steps", type=int, default=100)
    run.add_argument("--max-errors", type=int, default=10)
    run.add_argument("--concurrency", type=int, default=1)
    verify = subparsers.add_parser("verify", help="verify a local trace bundle")
    verify.add_argument("run_directory", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "verify":
            secret = os.environ.get("AZURE_API_KEY", "")
            report = verify_bundle(arguments.run_directory, secret_values=(secret,) if secret else ())
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0 if report["valid"] else 1
        config = load_config(
            domain=arguments.domain,
            task_id=arguments.task_id,
            task_count=arguments.task_count,
            trial_count=arguments.trial_count,
            seed=arguments.seed,
            max_steps=arguments.max_steps,
            max_errors=arguments.max_errors,
            concurrency=arguments.concurrency,
        )
        run_dir = run_experiment(config)
        print(json.dumps({"valid": True, "run_directory": str(run_dir)}, indent=2, sort_keys=True))
        return 0
    except (ConfigurationError, RunRefused) as exc:
        print(f"tau2-luna-local: {exc}", file=sys.stderr)
        return 2


def entrypoint() -> None:
    raise SystemExit(main())
