"""Strict target-neutral JSONL bridge used only by connector acceptance."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any


def _emit(value: dict[str, Any]) -> None:
    sys.stdout.write(
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    )
    sys.stdout.flush()


def _malform(mode: str) -> bool:
    if mode == "blank":
        sys.stdout.write("\n")
    elif mode == "duplicate":
        sys.stdout.write('{"kind":"ready","kind":"ready"}\n')
    elif mode == "invalid_utf8":
        os.write(sys.stdout.fileno(), b"\xff\n")
    elif mode == "extra_line":
        _emit({"kind": "unexpected"})
        _emit({"kind": "unexpected-again"})
    elif mode == "stderr":
        sys.stderr.write("PRIVATE_TARGET_EXCEPTION secret-token\n")
        sys.stderr.flush()
        _emit({"kind": "unexpected"})
    elif mode == "nonzero":
        raise SystemExit(17)
    elif mode == "partial_stall":
        os.write(sys.stdout.fileno(), b'{"kind":"ready"')
        sys.stdout.flush()
        time.sleep(1)
    else:
        return False
    sys.stdout.flush()
    return True


def _serve(mode: str) -> None:
    for raw_line in sys.stdin:
        request = json.loads(raw_line)
        if _malform(mode):
            return
        kind = request["kind"]
        if kind == "hello":
            ready = {
                key: value
                for key, value in request.items()
                if key
                in {
                    "case_id",
                    "connector_config_hash",
                    "connector_id",
                    "connector_kind",
                    "episode_id",
                    "protocol",
                    "source_commit",
                    "target_identity",
                }
            }
            ready.update(fallback_enabled=False, kind="ready", memory_state="EMPTY")
            if mode == "identity_mismatch":
                ready["episode_id"] = "episode-wrong"
            if mode == "unknown_field":
                ready["private_payload"] = "must-refuse"
            _emit(ready)
        elif kind == "turn":
            turn_index = request["turn_index"]
            result = {
                "assistant_content": f"bridge {turn_index} observed {request['content']}",
                "episode_id": request["episode_id"],
                "kind": "turn_result",
                "reason_code": None,
                "status": "SUCCEEDED",
                "tool_events": None,
                "turn_index": turn_index,
                "usage": None,
            }
            if mode == "out_of_order":
                result["turn_index"] += 1
            _emit(result)
        elif kind == "close":
            _emit(
                {
                    "episode_id": request["episode_id"],
                    "kind": "closed",
                    "last_turn_index": request["last_turn_index"],
                    "memory_state": "DISCARDED",
                }
            )


if __name__ == "__main__":
    _serve(sys.argv[1] if len(sys.argv) > 1 else "success")
