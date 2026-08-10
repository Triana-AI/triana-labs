from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triana")
    commands = parser.add_subparsers(dest="surface", required=True)
    backend = commands.add_parser("backend")
    actions = backend.add_subparsers(dest="action", required=True)

    import_s3 = actions.add_parser("import-s3")
    import_s3.add_argument("--bucket", required=True)
    import_s3.add_argument("--key", required=True)
    import_s3.add_argument("--sha256", required=True)
    import_s3.add_argument("--workspace", required=True)
    import_s3.add_argument("--agent", required=True)
    import_s3.add_argument("--version", required=True)
    import_s3.add_argument("--evidence-class", required=True)
    import_s3.add_argument("--idempotency-key", required=True)

    run = actions.add_parser("run")
    run.add_argument("--import-id", required=True)
    run.add_argument("--idempotency-key", required=True)
    run.add_argument("--rerun", action="store_true")
    analysis_runs = actions.add_parser("analysis-runs")
    analysis_runs.add_argument("--agent-id", required=True)
    analysis_report = actions.add_parser("analysis-report")
    analysis_report.add_argument("--report-id", required=True)
    analysis_review = actions.add_parser("analysis-review")
    analysis_review.add_argument("--report-id", required=True)
    analysis_rule = actions.add_parser("analysis-rule")
    analysis_rule.add_argument("--report-id", required=True)
    analysis_rule.add_argument("--ruling", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    origin = os.environ.get("TRIANA_BACKEND_API_ORIGIN", "http://127.0.0.1:8000")
    if args.action.startswith("analysis-"):
        token = os.environ.get("TRIANA_ACCESS_TOKEN")
        if not token:
            print(
                "AUTHENTICATION_REQUIRED: TRIANA_ACCESS_TOKEN is missing",
                file=sys.stderr,
            )
            return 2
        report_path = (
            f"/api/v1/trace-to-eval/reports/{args.report_id}"
            if hasattr(args, "report_id")
            else ""
        )
        try:
            if args.action == "analysis-runs":
                response = _request_json(
                    origin,
                    f"/api/v1/agents/{args.agent_id}/analysis-runs",
                    token=token,
                )
            elif args.action == "analysis-report":
                response = _request_json(origin, report_path, token=token)
            elif args.action == "analysis-review":
                response = _request_json(origin, f"{report_path}/review", token=token)
            else:
                with open(args.ruling, encoding="utf-8") as stream:
                    ruling: Any = json.load(stream)
                if not isinstance(ruling, dict):
                    raise ValueError("ruling must be a JSON object")
                response = _request_json(
                    origin,
                    f"{report_path}/rulings",
                    token=token,
                    payload=ruling,
                )
        except (HTTPError, URLError, OSError, ValueError) as error:
            print(_safe_error(error), file=sys.stderr)
            return 2
        print(json.dumps(response, sort_keys=True, separators=(",", ":")))
        return 0
    if args.action == "import-s3":
        path = "/api/v1/imports"
        payload = {
            "workspace_slug": args.workspace,
            "agent_key": args.agent,
            "version_key": args.version,
            "source": {
                "bucket": args.bucket,
                "key": args.key,
                "sha256": args.sha256,
            },
            "evidence_class": args.evidence_class,
        }
    else:
        path = "/api/v1/runs"
        payload = {
            "import_id": args.import_id,
            "rerun": args.rerun,
        }

    try:
        response = _post_json(
            origin, path, payload, idempotency_key=args.idempotency_key
        )
    except (HTTPError, URLError, ValueError) as error:
        print(_safe_error(error), file=sys.stderr)
        return 2
    print(json.dumps(response, sort_keys=True, separators=(",", ":")))
    return 0


def _request_json(
    origin: str,
    path: str,
    *,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = Request(  # noqa: S310 - operator-selected endpoint
        f"{origin.rstrip('/')}{path}",
        data=(
            None
            if payload is None
            else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            **({"Content-Type": "application/json"} if payload is not None else {}),
        },
        method="POST" if payload is not None else "GET",
    )
    with urlopen(request, timeout=300) as response:  # noqa: S310
        result: Any = json.load(response)
    if not isinstance(result, dict):
        raise ValueError("backend returned a non-object response")
    return result


def _post_json(
    origin: str,
    path: str,
    payload: dict[str, Any],
    *,
    idempotency_key: str,
) -> dict[str, Any]:
    request = Request(  # noqa: S310 - operator-selected loopback endpoint
        f"{origin.rstrip('/')}{path}",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Idempotency-Key": idempotency_key,
        },
        method="POST",
    )
    with urlopen(request, timeout=300) as response:  # noqa: S310
        result: Any = json.load(response)
    if not isinstance(result, dict):
        raise ValueError("backend returned a non-object response")
    return result


def _safe_error(error: HTTPError | URLError | OSError | ValueError) -> str:
    if isinstance(error, HTTPError):
        try:
            payload: Any = json.load(error)
            if isinstance(payload, dict):
                code = payload.get("code", "HTTP_ERROR")
                return f"{code}: backend request failed with HTTP {error.code}"
        except (OSError, ValueError):
            pass
        return f"HTTP_ERROR: backend request failed with HTTP {error.code}"
    if isinstance(error, URLError):
        return "BACKEND_UNAVAILABLE: backend could not be reached"
    if isinstance(error, OSError):
        return "LOCAL_INPUT_UNAVAILABLE: local ruling file could not be read"
    return f"INVALID_BACKEND_RESPONSE: {error}"


if __name__ == "__main__":
    raise SystemExit(main())
