#!/usr/bin/env python3
"""Build the smallest honest cross-stack release record around Braintrust."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    review = json.loads(args.input.read_text(encoding="utf-8"))
    gate = json.loads(args.gate.read_text(encoding="utf-8"))
    braintrust_checks = {
        f"braintrust:{check['name']}": check for check in gate["checks"]
    }
    external_checks = {
        item["id"]: item for item in review["external_evidence"]
    }

    requirement_results: list[dict[str, Any]] = []
    for requirement in review["requirements"]:
        evidence_id = requirement["evidence"]
        evidence = braintrust_checks.get(evidence_id) or external_checks.get(
            evidence_id
        )
        status = "MISSING" if evidence is None else evidence["status"]
        requirement_results.append(
            {
                **requirement,
                "status": status,
                "artifact": None if evidence is None else evidence.get("artifact"),
            }
        )

    required = [
        result
        for result in requirement_results
        if result["criticality"] == "release_required"
    ]
    blocking = [result for result in required if result["status"] == "FAIL"]
    gaps = [result for result in required if result["status"] == "MISSING"]
    if gate["comparability"]["status"] != "PASS":
        recommendation = "REVIEW"
    elif blocking:
        recommendation = "BLOCK"
    elif gaps or review["approval"] is None:
        recommendation = "REVIEW"
    else:
        recommendation = "PASS"

    record = {
        "schema": "synthetic-cross-stack-release-record-v1",
        "change": review["change"],
        "braintrust": {
            "baseline_experiment": gate["baseline_experiment"],
            "candidate_experiment": gate["candidate_experiment"],
            "comparability": gate["comparability"],
            "policy_version": gate["policy_version"],
        },
        "requirements": requirement_results,
        "recommendation": recommendation,
        "approval": review["approval"],
        "production_outcome_link": review["production_outcome_link"],
        "limitations": [
            "Braintrust supplied eval evidence, not requirement criticality.",
            "External evidence status and artifact identity were manually supplied.",
            "The hash detects later file changes but provides no trusted signer.",
            "No human release decision or production outcome is present.",
        ],
    }
    record["content_sha256"] = canonical_hash(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
