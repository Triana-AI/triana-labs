"""Generate or verify checked-in JSON Schema projections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from triana.contracts.models import DOCUMENT_MODELS

ROOT = Path(__file__).parents[1]
SCHEMA_DIR = ROOT / "schemas"


def _strip_invalid_defaults(value: object) -> None:
    """Remove null defaults that are not members of non-nullable wire types."""
    if isinstance(value, dict):
        if value.get("default") is None:
            value.pop("default", None)
        for item in value.values():
            _strip_invalid_defaults(item)
    elif isinstance(value, list):
        for item in value:
            _strip_invalid_defaults(item)


def rendered_schemas() -> dict[Path, bytes]:
    result: dict[Path, bytes] = {}
    for kind, model in sorted(DOCUMENT_MODELS.items()):
        schema = model.model_json_schema(mode="validation")
        _strip_invalid_defaults(schema)
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://schemas.triana.invalid/v1/{kind}.schema.json"
        result[SCHEMA_DIR / f"{kind}.schema.json"] = (
            json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    failures: list[str] = []
    for path, expected in rendered_schemas().items():
        if arguments.check:
            if not path.exists() or path.read_bytes() != expected:
                failures.append(path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if failures:
        parser.error("schema drift: " + ", ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
