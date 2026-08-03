from __future__ import annotations

import copy
import hashlib
import http.client
import json
import re
import ssl
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote, urlsplit

from .contracts import (
    AdaptiveRunFailure,
    JsonObject,
    TargetLaunch,
    TargetProtocolFailure,
)

_ENV = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_HEADER = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]{1,128}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_MONEY = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_MAX = 9_007_199_254_740_991
_MAX_BODY = 1_048_576
_SOURCES = {"episode_id", "case_id", "session_id", "user_turn", "transcript"}


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _integer(value: Any) -> bool:
    return type(value) is int and 0 <= value <= _MAX


def _text(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, str)
        and (not nonempty or bool(value))
        and len(value.encode()) <= 16_384
        and all(ord(char) >= 32 or char == "\n" for char in value)
        and not any(127 <= ord(char) <= 159 for char in value)
    )


def _closed(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _pointer(pointer: Any) -> tuple[str, ...]:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError
    result = []
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            raise ValueError
        result.append(raw.replace("~1", "/").replace("~0", "~"))
    return tuple(result)


def _extract(value: Any, pointer: str, *, missing: Any = ...) -> Any:
    try:
        current = value
        for token in _pointer(pointer):
            if isinstance(current, dict):
                current = current[token]
            elif isinstance(current, list) and token.isdigit():
                current = current[int(token)]
            else:
                raise KeyError
        return current
    except (KeyError, IndexError):
        if missing is ...:
            raise ValueError from None
        return missing


def _assign(value: dict[str, Any], pointer: str, item: Any) -> None:
    tokens = _pointer(pointer)
    if not tokens:
        raise ValueError
    parent: Any = value
    for token in tokens[:-1]:
        if not isinstance(parent, dict) or token not in parent:
            raise ValueError
        parent = parent[token]
    if not isinstance(parent, dict) or tokens[-1] not in parent:
        raise ValueError
    parent[tokens[-1]] = copy.deepcopy(item)


def _operation(value: Any, *, mode: str, turn: bool = False) -> None:
    if not _closed(value, {"method", "path_template", "constant_json", "assignments"}):
        raise ValueError
    if value["method"] not in {"GET", "POST", "DELETE"}:
        raise ValueError
    path = value["path_template"]
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or "?" in path
        or "#" in path
        or urlsplit(path).scheme
        or any(part in {".", ".."} for part in path.split("/"))
        or ("{" in path or "}" in path)
        and mode != "REMOTE_SESSION"
        or re.sub(r"\{session_id\}", "", path).find("{") >= 0
        or "{session_id}" in path
        and "{session_id}" not in path.split("/")
    ):
        raise ValueError
    constant = value["constant_json"]
    if not isinstance(constant, dict) or len(_canonical(constant)) > 65_536:
        raise ValueError
    assignments = value["assignments"]
    if not isinstance(assignments, list):
        raise TypeError
    pointers: list[tuple[str, ...]] = []
    sources: set[str] = set()
    for assignment in assignments:
        if not _closed(assignment, {"pointer", "source"}):
            raise ValueError
        source, pointer = assignment["source"], assignment["pointer"]
        if source not in _SOURCES or source in sources:
            raise ValueError
        tokens = _pointer(pointer)
        if any(a == tokens[: len(a)] or tokens == a[: len(tokens)] for a in pointers):
            raise ValueError
        current = _extract(constant, pointer)
        if source == "transcript" and not isinstance(current, list):
            raise ValueError
        if source != "transcript" and not isinstance(current, str):
            raise ValueError
        pointers.append(tokens)
        sources.add(source)
    if turn:
        if "user_turn" not in sources:
            raise ValueError
        if (mode == "STATELESS_TRANSCRIPT") != ("transcript" in sources):
            raise ValueError
    if "session_id" in sources and mode != "REMOTE_SESSION":
        raise ValueError


def _response_mapping(value: Any) -> None:
    keys = {
        "assistant_content_pointer",
        "target_status_pointer",
        "termination_pointer",
        "error_pointer",
        "tool_events",
        "internal_usage",
    }
    if not _closed(value, keys):
        raise ValueError
    if not isinstance(value["assistant_content_pointer"], str):
        raise TypeError
    for name in ("target_status_pointer", "termination_pointer", "error_pointer"):
        if value[name] is not None and not isinstance(value[name], str):
            raise ValueError
        if isinstance(value[name], str):
            _pointer(value[name])
    _pointer(value["assistant_content_pointer"])
    tools = value["tool_events"]
    if tools is not None:
        if not _closed(
            tools,
            {"list_pointer", "name_pointer", "arguments_pointer", "status_pointer"},
        ):
            raise ValueError
        for item in tools.values():
            if item is not None:
                _pointer(item)
    usage = value["internal_usage"]
    allowed = {
        "model_exchanges_pointer",
        "http_exchanges_pointer",
        "input_tokens_pointer",
        "output_tokens_pointer",
        "cost_usd_pointer",
    }
    if usage is not None:
        if not isinstance(usage, dict) or not usage or not set(usage) <= allowed:
            raise ValueError
        for item in usage.values():
            _pointer(item)


def validate_http_target(target: Any, environ: Mapping[str, str]) -> None:
    keys = {
        "connector_id",
        "connector_kind",
        "base_url",
        "allowed_host",
        "timeout_seconds",
        "auth",
        "session",
        "turn",
        "target_identity",
        "data_class",
        "state_isolation",
    }
    try:
        if not _closed(target, keys):
            raise ValueError
        if (
            target["connector_kind"] != "HTTP_JSON_V1"
            or not _ID.fullmatch(target["connector_id"])
            or target["data_class"]
            not in {"SYNTHETIC_LOCAL_TARGET", "OWNER_AUTHORIZED_REAL_TARGET"}
            or not _integer(target["timeout_seconds"])
            or not 1 <= target["timeout_seconds"] <= 180
        ):
            raise ValueError
        parsed = urlsplit(target["base_url"])
        host = (
            parsed.hostname.encode("idna").decode().lower() if parsed.hostname else ""
        )
        allowed = target["allowed_host"].encode("idna").decode().lower()
        local = host in {"localhost", "127.0.0.1", "::1"}
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.scheme == "http"
            and not local
            or host != allowed
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise AdaptiveRunFailure("TARGET_ENDPOINT_REFUSED", 4)
        auth = target["auth"]
        if auth == {"kind": "NONE"} or (
            _closed(auth, {"kind", "header_name", "env_name"})
            and auth["kind"] == "HEADER_ENV"
            and _HEADER.fullmatch(auth["header_name"])
            and _ENV.fullmatch(auth["env_name"])
            and bool(environ.get(auth["env_name"]))
        ):
            pass
        else:
            raise ValueError
        identity = target["target_identity"]
        if not _closed(
            identity, {"agent_id", "protocol", "version", "model", "prompt", "tools"}
        ):
            raise ValueError
        if not all(
            _text(identity[key], nonempty=True)
            for key in ("agent_id", "protocol", "version")
        ):
            raise ValueError
        optional_identity = (identity["model"], identity["prompt"], identity["tools"])
        if not all(
            item is None or _text(item, nonempty=True) for item in optional_identity
        ):
            raise ValueError
        if any(
            secret and secret in item
            for item in optional_identity
            if isinstance(item, str)
            for secret in environ.values()
        ):
            raise ValueError
        mode = (
            target["session"].get("mode")
            if isinstance(target["session"], dict)
            else None
        )
        if mode == "STATELESS_TRANSCRIPT":
            if target["session"] != {"mode": mode} or target["state_isolation"] != mode:
                raise ValueError
        elif mode == "REMOTE_SESSION":
            session = target["session"]
            if (
                not _closed(session, {"mode", "create", "close", "session_id_pointer"})
                or target["state_isolation"] != "TARGET_GLOBAL_STATE_UNKNOWN"
                or not isinstance(session["session_id_pointer"], str)
            ):
                raise ValueError
            _pointer(session["session_id_pointer"])
            _operation(session["create"], mode=mode)
            _operation(session["close"], mode=mode)
        else:
            raise ValueError
        if not _closed(target["turn"], {"operation", "response_mapping"}):
            raise ValueError
        _operation(target["turn"]["operation"], mode=mode, turn=True)
        _response_mapping(target["turn"]["response_mapping"])
    except AdaptiveRunFailure:
        raise
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        raise AdaptiveRunFailure("TARGET_CONNECTOR_CONFIG_INVALID", 2) from None


class _HttpSession:
    def __init__(self, launch: TargetLaunch) -> None:
        self._launch = launch
        self._target = launch.target_config
        self._session_id: str | None = None
        self._http = 0
        self._tools = 0
        self._closed = False
        self._opened = False

    def _request(
        self, operation: Mapping[str, Any], sources: Mapping[str, Any]
    ) -> tuple[int, dict[str, Any], str]:
        body = copy.deepcopy(operation["constant_json"])
        for assignment in operation["assignments"]:
            _assign(body, assignment["pointer"], sources[assignment["source"]])
        path = operation["path_template"]
        if "{session_id}" in path:
            if not self._session_id:
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            path = path.replace("{session_id}", quote(self._session_id, safe=""))
        parsed = urlsplit(self._target["base_url"])
        host = parsed.hostname
        if host is None:
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
        connection_type = (
            http.client.HTTPSConnection
            if parsed.scheme == "https"
            else http.client.HTTPConnection
        )
        kwargs: dict[str, Any] = {"timeout": self._target["timeout_seconds"]}
        if parsed.scheme == "https":
            kwargs["context"] = ssl.create_default_context()
        connection = connection_type(host, parsed.port, **kwargs)
        payload = _canonical(body)
        headers = {"Content-Type": "application/json", "Connection": "close"}
        auth = self._target["auth"]
        if auth["kind"] == "HEADER_ENV":
            headers[auth["header_name"]] = self._launch.environment[auth["env_name"]]
        try:
            connection.request(operation["method"], path, body=payload, headers=headers)
            response = connection.getresponse()
            raw = response.read(_MAX_BODY + 1)
            status = response.status
        except (OSError, TimeoutError, http.client.HTTPException) as error:
            raise TargetProtocolFailure("TARGET_HTTP_ERROR", observed_http=1) from error
        finally:
            connection.close()
        self._http += 1
        if len(raw) > _MAX_BODY:
            raise TargetProtocolFailure("TARGET_RESPONSE_INVALID", observed_http=1)
        if any(
            secret.encode() in raw
            for secret in self._launch.environment.values()
            if secret
        ):
            raise TargetProtocolFailure("TARGET_RESPONSE_INVALID", observed_http=1)
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        if not 200 <= status < 300:
            return status, {}, digest
        try:
            value = json.loads(raw.decode(), object_pairs_hook=_pairs)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise TargetProtocolFailure(
                "TARGET_RESPONSE_INVALID", observed_http=1
            ) from error
        if not isinstance(value, dict):
            raise TargetProtocolFailure("TARGET_RESPONSE_INVALID", observed_http=1)
        return status, value, digest

    def _turn_result(self, request: JsonObject) -> JsonObject:
        operation = self._target["turn"]["operation"]
        sources = {
            "episode_id": request["episode_id"],
            "case_id": self._launch.case_id,
            "session_id": self._session_id,
            "user_turn": request["content"],
            "transcript": request["transcript"],
        }
        status_code, value, digest = self._request(operation, sources)
        if not 200 <= status_code < 300:
            raise TargetProtocolFailure("TARGET_HTTP_ERROR", observed_http=1)
        mapping = self._target["turn"]["response_mapping"]
        try:
            error = (
                _extract(value, mapping["error_pointer"], missing=None)
                if mapping["error_pointer"]
                else None
            )
            if error is not None:
                if not _text(error):
                    raise ValueError
                raise TargetProtocolFailure("TARGET_HTTP_ERROR", observed_http=1)
            content = _extract(value, mapping["assistant_content_pointer"])
            if not _text(content, nonempty=True):
                raise ValueError
            target_status = (
                _extract(value, mapping["target_status_pointer"])
                if mapping["target_status_pointer"]
                else "SUCCEEDED"
            )
            termination = (
                _extract(value, mapping["termination_pointer"])
                if mapping["termination_pointer"]
                else None
            )
            if (
                not _text(target_status, nonempty=True)
                or termination is not None
                and type(termination) is not bool
            ):
                raise ValueError
            tool_mapping = mapping["tool_events"]
            tools: list[dict[str, Any]] | None = None
            gaps = ["TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED"]
            if tool_mapping is None:
                gaps.append("TARGET_TOOL_TRACE_UNAVAILABLE")
            else:
                raw_tools = _extract(value, tool_mapping["list_pointer"])
                if not isinstance(raw_tools, list):
                    raise ValueError
                tools = []
                for raw in raw_tools:
                    if not isinstance(raw, dict):
                        raise TypeError
                    name = _extract(raw, tool_mapping["name_pointer"])
                    arguments = _extract(raw, tool_mapping["arguments_pointer"])
                    item_status = (
                        _extract(raw, tool_mapping["status_pointer"])
                        if tool_mapping["status_pointer"]
                        else "SUCCEEDED"
                    )
                    if (
                        not _text(name, nonempty=True)
                        or not isinstance(arguments, dict)
                        or not _text(item_status, nonempty=True)
                    ):
                        raise ValueError
                    self._tools += 1
                    tools.append(
                        {
                            "tool_event_id": f"tool-event-{self._tools}",
                            "ordinal": self._tools,
                            "name": name,
                            "arguments": arguments,
                            "result": {},
                            "status": item_status,
                            "reason_code": None
                            if item_status == "SUCCEEDED"
                            else "TARGET_TOOL_FAILED",
                            "cached": False,
                        }
                    )
            usage_mapping = mapping["internal_usage"]
            reported: dict[str, Any] | None = None
            if usage_mapping is None:
                gaps.append("TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE")
            else:
                reported = {}
                for name, pointer in usage_mapping.items():
                    item = _extract(value, pointer)
                    key = name.removesuffix("_pointer")
                    if key == "cost_usd":
                        if (
                            not isinstance(item, str)
                            or not _MONEY.fullmatch(item)
                            or Decimal(item) < 0
                        ):
                            raise ValueError
                    elif not _integer(item):
                        raise ValueError
                    reported[key] = item
            if self._target["state_isolation"] == "TARGET_GLOBAL_STATE_UNKNOWN":
                gaps.append("TARGET_STATE_ISOLATION_UNAVAILABLE")
        except TargetProtocolFailure:
            raise
        except (InvalidOperation, KeyError, TypeError, ValueError):
            raise TargetProtocolFailure(
                "TARGET_RESPONSE_INVALID", observed_http=1
            ) from None
        return {
            "kind": "turn_result",
            "episode_id": request["episode_id"],
            "turn_index": request["turn_index"],
            "status": target_status,
            "assistant_content": content,
            "tool_events": tools,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "provider_http_exchange_count": 1,
                "provider_reported_cost_usd": None,
            },
            "reason_code": None,
            "termination_signal": termination,
            "reported_internal_usage": reported,
            "telemetry_gaps": gaps,
            "response_provenance": {
                "connector_id": self._target["connector_id"],
                "http_status": status_code,
                "response_hash": digest,
            },
        }

    def exchange(self, request: JsonObject) -> JsonObject:
        kind = request.get("kind")
        if kind == "hello":
            create_http = 0
            if self._target["session"]["mode"] == "REMOTE_SESSION":
                status, value, _ = self._request(
                    self._target["session"]["create"],
                    {
                        "episode_id": request["episode_id"],
                        "case_id": request["case_id"],
                        "session_id": "",
                        "user_turn": "",
                        "transcript": [],
                    },
                )
                if not 200 <= status < 300:
                    raise TargetProtocolFailure(
                        "TARGET_SESSION_CREATE_FAILED", observed_http=1
                    )
                try:
                    session_id = _extract(
                        value, self._target["session"]["session_id_pointer"]
                    )
                except ValueError:
                    raise TargetProtocolFailure(
                        "TARGET_SESSION_CREATE_FAILED", observed_http=1
                    ) from None
                if not _text(session_id, nonempty=True):
                    raise TargetProtocolFailure(
                        "TARGET_SESSION_CREATE_FAILED", observed_http=1
                    )
                self._session_id, self._opened, create_http = session_id, True, 1
            return {
                **dict(request),
                "kind": "ready",
                "memory_state": "EMPTY",
                "fallback_enabled": False,
                "create_http_exchange_count": create_http,
            }
        if kind == "turn":
            return self._turn_result(request)
        if kind != "close" or self._closed:
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
        self._closed = True
        close_http = 0
        if self._target["session"]["mode"] == "REMOTE_SESSION" and self._opened:
            status, _, _ = self._request(
                self._target["session"]["close"],
                {
                    "episode_id": request["episode_id"],
                    "case_id": self._launch.case_id,
                    "session_id": self._session_id,
                    "user_turn": "",
                    "transcript": [],
                },
            )
            close_http = 1
            if not 200 <= status < 300:
                raise TargetProtocolFailure(
                    "TARGET_SESSION_CLOSE_FAILED", observed_http=1
                )
        return {
            "kind": "closed",
            "episode_id": request["episode_id"],
            "last_turn_index": request["last_turn_index"],
            "memory_state": "DISCARDED",
            "provider_http_exchange_count": self._http,
            "tool_call_count": self._tools,
            "close_http_exchange_count": close_http,
        }

    def terminate(self) -> None:
        self._closed = True


class HttpJsonTargetFactory:
    """Restricted one-request-per-operation HTTP/JSON target connector."""

    def start(self, launch: TargetLaunch) -> _HttpSession:
        return _HttpSession(launch)
