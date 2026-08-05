"""Run provider-neutral Diff V0 from completed normalized JSONL bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentagon.evals.adapters import default_trace_adapter_registry
from agentagon.evals.bundle_compiler import compile_release_run
from agentagon.evals.comparator import compare_release_run
from agentagon.evals.config import load_agent_version, load_measurements
from agentagon.evals.evaluators import EvaluatorRegistry
from agentagon.evals.models import ExecutorKind, ReleaseRunKind, ResetPolicy
from agentagon.evals.native_measurements import (
    default_mechanical_measurements,
    native_trace_evaluator,
)
from agentagon.evals.output import to_primitive, write_release_artifacts
from agentagon.evals.seed_bridge import build_seed_bridge


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    default_reset_policy = ResetPolicy(args.default_reset_policy)
    adapters = default_trace_adapter_registry()
    baseline_adapter = adapters.get(args.baseline_trace_adapter)
    candidate_adapter = adapters.get(
        args.candidate_trace_adapter or args.baseline_trace_adapter
    )
    baseline_load = baseline_adapter.load(
        args.baseline, default_reset_policy=default_reset_policy
    )
    candidate_load = candidate_adapter.load(
        args.candidate, default_reset_policy=default_reset_policy
    )
    baseline, baseline_gaps = baseline_load.bundles, baseline_load.gaps
    candidate, candidate_gaps = candidate_load.bundles, candidate_load.gaps
    baseline_version = load_agent_version(args.baseline_version)
    run_kind = ReleaseRunKind(args.run_kind)
    if args.candidate_version is None:
        if run_kind is not ReleaseRunKind.A_A_CONTROL:
            raise SystemExit("--candidate-version is required for A_B_CHANGE")
        candidate_version = baseline_version
    else:
        candidate_version = load_agent_version(args.candidate_version)
    measurements = (
        load_measurements(args.measurements)
        if args.measurements
        else default_mechanical_measurements()
    )
    registry = EvaluatorRegistry()
    registry.register(
        ExecutorKind.DETERMINISTIC,
        native_trace_evaluator(),
        evaluator_version="native-trace-v1",
    )
    run = compile_release_run(
        run_id=args.run_id,
        run_kind=run_kind,
        baseline_version=baseline_version,
        candidate_version=candidate_version,
        baseline_bundles=baseline,
        candidate_bundles=candidate,
        measurements=measurements,
        registry=registry,
        case_set_version=args.case_set_version,
        runner_adapter_version=args.runner_adapter_version,
        world_version=args.world_version,
        fixture_bundle_hash=args.fixture_bundle_hash,
        protocol_version=args.protocol_version,
        change_id=args.change_id,
        changed_artifacts=tuple(args.changed_artifact),
        developer_hypothesis=args.developer_hypothesis,
        commit_message=args.commit_message,
        execution_gaps=(*baseline_gaps, *candidate_gaps),
        trace_adapter_versions=(
            baseline_load.adapter_version,
            candidate_load.adapter_version,
        ),
    )
    release_diff = compare_release_run(run, measurements)
    args.output.mkdir(parents=True, exist_ok=True)
    paths = write_release_artifacts(
        args.output,
        run,
        release_diff,
        measurements,
        evidence_class=args.evidence_class,
    )
    seed_path = args.output / "baseline_seed_bridge.json"
    seed_path.write_text(
        json.dumps(build_seed_bridge(baseline), indent=2, sort_keys=True) + "\n"
    )
    ingestion_path = args.output / "ingestion_audit.json"
    ingestion_path.write_text(
        json.dumps(
            {
                "baseline_bundle_count": len(baseline),
                "candidate_bundle_count": len(candidate),
                "paired_identity_count": len(run.pairs),
                "valid_pair_count": sum(pair.is_valid for pair in run.pairs),
                "invalid_pair_count": sum(not pair.is_valid for pair in run.pairs),
                "baseline_version_id": baseline_version.version_id,
                "candidate_version_id": candidate_version.version_id,
                "measurement_versions": list(run.measurement_versions),
                "baseline_content_hashes": [item.content_hash for item in baseline],
                "candidate_content_hashes": [item.content_hash for item in candidate],
                "baseline_ingestion_gap_count": len(baseline_gaps),
                "candidate_ingestion_gap_count": len(candidate_gaps),
                "ingestion_gaps": to_primitive((*baseline_gaps, *candidate_gaps)),
                "run_kind": run.run_kind.value,
                "baseline_trace_adapter": baseline_load.adapter_version,
                "candidate_trace_adapter": candidate_load.adapter_version,
                "material_change": to_primitive(run.material_change),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"Wrote {len(paths) + 2} artifacts to {args.output}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--baseline-version", type=Path, required=True)
    parser.add_argument("--candidate-version", type=Path)
    parser.add_argument("--measurements", type=Path)
    parser.add_argument(
        "--run-kind",
        choices=[item.value for item in ReleaseRunKind],
        required=True,
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--case-set-version", required=True)
    parser.add_argument("--runner-adapter-version", required=True)
    parser.add_argument("--world-version", required=True)
    parser.add_argument("--fixture-bundle-hash", required=True)
    parser.add_argument("--protocol-version", required=True)
    parser.add_argument(
        "--baseline-trace-adapter",
        default="normalized-jsonl-v1",
    )
    parser.add_argument(
        "--candidate-trace-adapter",
        help="Defaults to --baseline-trace-adapter.",
    )
    parser.add_argument(
        "--default-reset-policy",
        choices=[item.value for item in ResetPolicy],
        default=ResetPolicy.REQUIRED_EQUIVALENT.value,
        help=(
            "Used only when a trace omits reset_policy. Choose ISOLATED_NAMESPACE "
            "only when the runner audit proves per-case isolation."
        ),
    )
    parser.add_argument("--change-id", default="aa-control")
    parser.add_argument("--changed-artifact", action="append", default=[])
    parser.add_argument("--developer-hypothesis")
    parser.add_argument("--commit-message")
    parser.add_argument(
        "--evidence-class",
        choices=("REAL_CONTROLLED", "PREVIEW_SYNTHETIC"),
        default="REAL_CONTROLLED",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
