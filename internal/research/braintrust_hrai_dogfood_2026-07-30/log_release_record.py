#!/usr/bin/env python3
"""Store the synthetic cross-stack release record as a Braintrust trace."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from braintrust import init_logger


PROJECT_ID = "eeb39085-5524-49eb-87b3-2a7f76a27ed7"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()

    api_key = os.environ.get("BRAINTRUST_API_KEY")
    if not api_key:
        raise SystemExit("BRAINTRUST_API_KEY is required")
    record = json.loads(args.record.read_text(encoding="utf-8"))

    logger = init_logger(
        project_id=PROJECT_ID,
        api_key=api_key,
        async_flush=False,
    )
    with logger.start_span(
        name="synthetic-cross-stack-release-review",
        type="task",
        input=record["change"],
        expected={
            "required_requirement_ids": [
                requirement["id"]
                for requirement in record["requirements"]
                if requirement["criticality"] == "release_required"
            ]
        },
        metadata={
            "record_schema": record["schema"],
            "record_sha256": record["content_sha256"],
            "baseline_experiment": record["braintrust"]["baseline_experiment"],
            "candidate_experiment": record["braintrust"]["candidate_experiment"],
            "comparability": record["braintrust"]["comparability"],
            "requirements": record["requirements"],
            "approval": record["approval"],
            "production_outcome_link": record["production_outcome_link"],
            "synthetic": True,
        },
        tags=["release-record", "synthetic", "cross-stack"],
    ) as span:
        span.log(
            output={
                "recommendation": record["recommendation"],
                "limitations": record["limitations"],
            },
            scores={
                "required_evidence_complete": float(
                    all(
                        requirement["status"] != "MISSING"
                        for requirement in record["requirements"]
                        if requirement["criticality"] == "release_required"
                    )
                ),
                "release_authorized": float(
                    record["recommendation"] == "PASS"
                    and record["approval"] is not None
                ),
            },
        )
        print(
            json.dumps(
                {
                    "span_id": span.id,
                    "root_span_id": span.root_span_id,
                    "record_sha256": record["content_sha256"],
                },
                indent=2,
            )
        )
    logger.flush()


if __name__ == "__main__":
    main()
