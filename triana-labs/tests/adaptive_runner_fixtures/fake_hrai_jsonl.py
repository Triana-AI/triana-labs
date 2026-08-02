#!/usr/bin/env python3
"""Deterministic raw JSONL target used only by LABS-05 acceptance tests."""

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
    total_http = 0
    for raw_line in sys.stdin:
        request = json.loads(raw_line)
        if _malform(mode):
            return
        kind = request["kind"]
        if kind == "hello":
            ready = {
                "agent_model": request["agent_model"],
                "case_id": request["case_id"],
                "episode_id": request["episode_id"],
                "fallback_enabled": False,
                "kind": "ready",
                "memory_state": "EMPTY",
                "prompt_version": request["prompt_version"],
                "protocol": request["protocol"],
                "source_commit": request["source_commit"],
                "world_hash": request["world_hash"],
            }
            if mode == "identity_mismatch":
                ready["episode_id"] = "episode-wrong"
            if mode == "unknown_field":
                ready["private_payload"] = "must-refuse"
            _emit(ready)
        elif kind == "turn":
            total_http += 1
            status = "SUCCEEDED"
            reason: str | None = None
            content = f"assistant {request['turn_index']} observed {request['content']}"
            if mode == "tool_refused":
                status, reason, content = "TOOL_REFUSED", "TOOL_NOT_ALLOWED", ""
            elif mode == "provider_failed":
                status, reason, content = "PROVIDER_FAILED", "PROVIDER_ERROR", ""
            result = {
                "assistant_content": content,
                "episode_id": request["episode_id"],
                "kind": "turn_result",
                "reason_code": reason,
                "status": status,
                "tool_events": [],
                "turn_index": request["turn_index"],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "provider_http_exchange_count": 1,
                    "provider_reported_cost_usd": None,
                },
            }
            if mode == "out_of_order":
                result["turn_index"] = request["turn_index"] + 1
            _emit(result)
        elif kind == "close":
            _emit(
                {
                    "episode_id": request["episode_id"],
                    "kind": "closed",
                    "last_turn_index": request["last_turn_index"],
                    "memory_state": "DISCARDED",
                    "provider_http_exchange_count": total_http,
                    "tool_call_count": 0,
                }
            )


if __name__ == "__main__":
    _serve(sys.argv[1] if len(sys.argv) > 1 else "success")
