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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    origin = os.environ.get("TRIANA_BACKEND_API_ORIGIN", "http://127.0.0.1:8000")
    if args.action == "import-s3":
        path = "/api/v1/imports"
        payload = {
            "source": {"storage_backend": "S3", "bucket": args.bucket, "key": args.key},
            "expected_sha256": args.sha256,
            "workspace_slug": args.workspace,
            "agent_key": args.agent,
            "version_key": args.version,
            "evidence_class": args.evidence_class,
            "idempotency_key": args.idempotency_key,
        }
    else:
        path = "/api/v1/runs"
        payload = {
            "import_id": args.import_id,
            "idempotency_key": args.idempotency_key,
            "new_attempt": args.rerun,
        }

    try:
        response = _post_json(origin, path, payload)
    except (HTTPError, URLError, ValueError) as error:
        print(_safe_error(error), file=sys.stderr)
        return 2
    print(json.dumps(response, sort_keys=True, separators=(",", ":")))
    return 0


def _post_json(origin: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(  # noqa: S310 - operator-selected loopback endpoint
        f"{origin.rstrip('/')}{path}",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=300) as response:  # noqa: S310
        result: Any = json.load(response)
    if not isinstance(result, dict):
        raise ValueError("backend returned a non-object response")
    return result


def _safe_error(error: HTTPError | URLError | ValueError) -> str:
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
    return f"INVALID_BACKEND_RESPONSE: {error}"


if __name__ == "__main__":
    raise SystemExit(main())
