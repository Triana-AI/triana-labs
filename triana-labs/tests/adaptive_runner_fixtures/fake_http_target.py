"""Threaded localhost HTTP target for Target Connector V1 acceptance only."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class FakeHttpTarget:
    def __init__(self, *, mode: str = "success", secret: str | None = None) -> None:
        self.mode = mode
        self.secret = secret
        self.requests: list[dict[str, Any]] = []
        self._sessions = 0
        self._failed_close = False
        self._failed_chat = False
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, format: str, *args: object) -> None:
                del format, args

            def _body(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0"))
                payload = self.rfile.read(length)
                if not payload:
                    return {}
                value = json.loads(payload)
                assert isinstance(value, dict)
                return value

            def _record(self, body: dict[str, Any]) -> None:
                owner.requests.append(
                    {
                        "body": body,
                        "headers": {
                            key.casefold(): value for key, value in self.headers.items()
                        },
                        "method": self.command,
                        "path": self.path,
                    }
                )

            def _json(
                self,
                status: int,
                value: dict[str, Any],
                *,
                headers: dict[str, str] | None = None,
            ) -> None:
                payload = json.dumps(
                    value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
                ).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                for key, item in (headers or {}).items():
                    self.send_header(key, item)
                self.end_headers()
                self.wfile.write(payload)

            def _text(self, status: int, value: str) -> None:
                payload = value.encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self) -> None:
                body = self._body()
                self._record(body)
                if self.path == "/sessions":
                    owner._sessions += 1
                    if owner._sessions == 1 and owner.mode == "create_non_2xx":
                        self._json(503, {"error": "synthetic create failure"})
                        return
                    if owner._sessions == 1 and owner.mode == "create_non_json_500":
                        self._text(500, "Internal Server Error")
                        return
                    if owner._sessions == 1 and owner.mode == "create_missing_id":
                        self._json(201, {"created": True})
                        return
                    self._json(
                        201, {"session_id": f"synthetic-session-{owner._sessions}"}
                    )
                    return
                if self.path == "/redirect":
                    self._json(307, {}, headers={"Location": "/sink"})
                    return
                if self.path == "/sink":
                    self._json(200, {"response": "redirect followed"})
                    return
                if self.path.startswith("/sessions/") and self.path.endswith("/chat"):
                    if owner.mode == "fail_first_chat" and not owner._failed_chat:
                        owner._failed_chat = True
                        self._json(503, {"error": "synthetic unavailable"})
                        return
                    self._json(200, owner._remote_response(body))
                    return
                if self.path == "/v2/respond":
                    self._json(200, owner._stateless_response(body))
                    return
                self._json(404, {"error": "not found"})

            def do_DELETE(self) -> None:
                body = self._body()
                self._record(body)
                if owner.mode == "close_failure" and not owner._failed_close:
                    owner._failed_close = True
                    self._json(500, {"error": "synthetic close failure"})
                    return
                self._json(200, {"closed": True})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def _remote_response(self, body: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "secret_reflection":
            return {"response": f"reflected {self.secret}", "tool_calls": []}
        if self.mode == "malformed_tools":
            return {"response": "bounded assistant", "tool_calls": {"bad": True}}
        response: dict[str, Any] = {
            "response": f"remote observed {body.get('message', '')}",
            "tool_calls": [
                {"args": {"synthetic": True}, "name": "opaque_target_tool"},
                {"args": {"synthetic": True}, "name": "opaque_target_tool"},
            ],
        }
        if self.mode == "usage_present":
            response["usage"] = {
                "cost_usd": "0.125000",
                "http_exchanges": 4,
                "input_tokens": 101,
                "model_exchanges": 2,
                "output_tokens": 23,
            }
        elif self.mode == "malformed_usage":
            response["usage"] = {"input_tokens": True}
        return response

    def _stateless_response(self, body: dict[str, Any]) -> dict[str, Any]:
        dialog = body.get("payload", {}).get("dialog", [])
        return {
            "meter": {"calls": 1, "in": 17, "out": 5},
            "result": {
                "agent": {"text": f"stateless transcript length {len(dialog)}"},
                "ended": False,
                "events": [],
            },
        }

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


@contextmanager
def serve(
    *, mode: str = "success", secret: str | None = None
) -> Iterator[FakeHttpTarget]:
    target = FakeHttpTarget(mode=mode, secret=secret)
    target.start()
    try:
        yield target
    finally:
        target.close()
