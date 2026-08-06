from __future__ import annotations

import functools
import time
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any, Protocol, TypeVar
from urllib.parse import urlparse

T = TypeVar("T")
EventSink = Callable[[str, dict[str, Any]], Any]
SpanSink = Callable[[dict[str, Any]], Any]
RoleLaneResolver = Callable[[tuple[Any, ...], dict[str, Any]], str | None]
ResponseCostFallback = Callable[[Any], tuple[Any, dict[str, str]]]
_ROLE_LANES = frozenset({"agent", "user", "evaluator"})


class CompletionTarget(Protocol):
    completion: Callable[..., Any]


_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "x-api-key",
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "access_token",
        "refresh_token",
        "secret",
        "password",
    }
)


def _redacted_string(value: str, secrets: tuple[str, ...]) -> str:
    result = value
    for secret in secrets:
        if secret:
            result = result.replace(secret, "[REDACTED]")
    return result


def redact(value: Any, *, secrets: Iterable[str] = (), _seen: set[int] | None = None) -> Any:
    """Project arbitrary provider objects into JSON-safe, recursively redacted values."""
    secret_tuple = tuple(secret for secret in secrets if secret)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _redacted_string(value, secret_tuple)
    if isinstance(value, bytes):
        return _redacted_string(value.decode("utf-8", errors="replace"), secret_tuple)

    seen = set() if _seen is None else _seen
    identity = id(value)
    if identity in seen:
        return "[CYCLE]"
    seen.add(identity)
    try:
        if isinstance(value, Mapping):
            projected: dict[str, Any] = {}
            for key, item in value.items():
                safe_key = _redacted_string(str(key), secret_tuple)
                if safe_key.lower() in _SENSITIVE_KEYS:
                    projected[safe_key] = "[REDACTED]"
                else:
                    projected[safe_key] = redact(item, secrets=secret_tuple, _seen=seen)
            return projected
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [redact(item, secrets=secret_tuple, _seen=seen) for item in value]
        if isinstance(value, BaseException):
            attributes = {key: item for key, item in vars(value).items() if not key.startswith("__")}
            return {
                "exception_class": type(value).__name__,
                "message": _redacted_string(str(value), secret_tuple),
                "attributes": redact(attributes, secrets=secret_tuple, _seen=seen),
            }
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            return redact(model_dump(), secrets=secret_tuple, _seen=seen)
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            return redact(to_dict(), secrets=secret_tuple, _seen=seen)
        if hasattr(value, "__dict__"):
            attributes = {key: item for key, item in vars(value).items() if not key.startswith("__")}
            return redact(attributes, secrets=secret_tuple, _seen=seen)
        return _redacted_string(repr(value), secret_tuple)
    finally:
        seen.remove(identity)


def _response_mapping(response: Any, secrets: tuple[str, ...]) -> dict[str, Any]:
    if isinstance(response, Mapping):
        value = dict(response)
    elif callable(getattr(response, "model_dump", None)):
        value = response.model_dump()
    elif callable(getattr(response, "to_dict", None)):
        value = response.to_dict()
    else:
        value = {"projection": redact(response, secrets=secrets)}
    projected = redact(value, secrets=secrets)
    return projected if isinstance(projected, dict) else {"projection": projected}


class CompletionCapture(AbstractContextManager["CompletionCapture"]):
    """Temporarily intercept exactly one imported LiteLLM completion boundary."""

    def __init__(
        self,
        *,
        target: CompletionTarget,
        event_sink: EventSink,
        span_sink: SpanSink,
        secrets: Iterable[str] = (),
        wall_time_ns: Callable[[], int] = time.time_ns,
        monotonic_ns: Callable[[], int] = time.monotonic_ns,
        call_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
        span_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex[:16],
        role_lane: str | None = None,
        role_lane_resolver: RoleLaneResolver | None = None,
        response_cost_fallback: ResponseCostFallback | None = None,
        response_cost_fallbacks: Mapping[str, ResponseCostFallback] | None = None,
    ) -> None:
        self._target = target
        self._event_sink = event_sink
        self._span_sink = span_sink
        self._secrets = tuple(secret for secret in secrets if secret)
        self._wall_time_ns = wall_time_ns
        self._monotonic_ns = monotonic_ns
        self._call_id_factory = call_id_factory
        self._span_id_factory = span_id_factory
        self._role_lane = role_lane
        self._role_lane_resolver = role_lane_resolver
        self._response_cost_fallback = response_cost_fallback
        self._response_cost_fallbacks = dict(response_cost_fallbacks or {})
        self._original: Callable[..., Any] | None = None
        self._attempt = 0

    def __enter__(self) -> CompletionCapture:
        if self._original is not None:
            raise RuntimeError("completion capture is already installed")
        original = self._target.completion
        self._original = original

        @functools.wraps(original)
        def captured(*args: Any, **kwargs: Any) -> Any:
            self._attempt += 1
            candidate = (
                self._role_lane_resolver(args, kwargs)
                if self._role_lane_resolver is not None
                else self._role_lane
            )
            if candidate in _ROLE_LANES:
                lane_fields = {"role_lane": candidate}
            else:
                lane_fields = {
                    "role_lane": "unknown",
                    "role_lane_gap": (
                        "BOUNDARY_NOT_OBSERVABLE"
                        if candidate is None
                        else "INVALID_BOUNDARY_CLASSIFICATION"
                    ),
                }
            call_id = self._call_id_factory()
            span_id = self._span_id_factory()
            started_wall = self._wall_time_ns()
            started_mono = self._monotonic_ns()
            safe_kwargs = redact(kwargs, secrets=self._secrets)
            if not isinstance(safe_kwargs, dict):
                safe_kwargs = {"projection": safe_kwargs}
            endpoint = str(kwargs.get("api_base", ""))
            request_payload = {
                "call_id": call_id,
                "span_id": span_id,
                **lane_fields,
                "attempt": self._attempt,
                "start_time_ns": started_wall,
                "model": redact(kwargs.get("model"), secrets=self._secrets),
                "endpoint_host": (urlparse(endpoint).hostname or "").lower() or None,
                "api_version": redact(kwargs.get("api_version"), secrets=self._secrets),
                "kwargs": safe_kwargs,
                "messages": safe_kwargs.get("messages"),
                "tools": safe_kwargs.get("tools"),
                "tool_choice": safe_kwargs.get("tool_choice"),
                "retry_setting": safe_kwargs.get("num_retries"),
            }
            self._event_sink("model.request", request_payload)
            try:
                response = original(*args, **kwargs)
            except BaseException as exc:
                ended_wall = self._wall_time_ns()
                duration = self._monotonic_ns() - started_mono
                safe_exception = redact(exc, secrets=self._secrets)
                attributes = safe_exception.get("attributes", {}) if isinstance(safe_exception, dict) else {}
                error_payload = {
                    "call_id": call_id,
                    "span_id": span_id,
                    **lane_fields,
                    "attempt": self._attempt,
                    "outcome": "error",
                    "start_time_ns": started_wall,
                    "end_time_ns": ended_wall,
                    "duration_ns": duration,
                    "exception_class": type(exc).__name__,
                    "message": _redacted_string(str(exc), self._secrets),
                    "status_code": redact(getattr(exc, "status_code", None), secrets=self._secrets),
                    "retry_after": redact(getattr(exc, "retry_after", None), secrets=self._secrets),
                    "exception": safe_exception,
                    "safe_provider_response": redact(getattr(exc, "response", None), secrets=self._secrets),
                    "exception_attributes": attributes,
                }
                self._event_sink("model.error", error_payload)
                self._span_sink(
                    {
                        "name": "model.call",
                        "call_id": call_id,
                        "span_id": span_id,
                        **lane_fields,
                        "start_time_ns": started_wall,
                        "end_time_ns": ended_wall,
                        "duration_ns": duration,
                        "status": "ERROR",
                        "exception_class": type(exc).__name__,
                    }
                )
                raise
            ended_wall = self._wall_time_ns()
            duration = self._monotonic_ns() - started_mono
            mapping = _response_mapping(response, self._secrets)
            hidden = redact(getattr(response, "_hidden_params", None), secrets=self._secrets)
            headers = redact(getattr(response, "_response_headers", None), secrets=self._secrets)
            cost = hidden.get("response_cost") if isinstance(hidden, dict) else None
            cost_source = {
                "kind": "PROVIDER_RETURNED"
                if cost is not None
                else "UNAVAILABLE_PROVIDER_COST"
            }
            requested_model = kwargs.get("model")
            fallback = (
                self._response_cost_fallbacks.get(requested_model)
                if isinstance(requested_model, str)
                else None
            )
            if requested_model is None and len(self._response_cost_fallbacks) == 1:
                fallback = next(iter(self._response_cost_fallbacks.values()))
            if fallback is None:
                fallback = self._response_cost_fallback
            if cost is None and fallback is not None:
                cost, cost_source = fallback(mapping)
            response_payload = {
                "call_id": call_id,
                "span_id": span_id,
                **lane_fields,
                "attempt": self._attempt,
                "outcome": "success",
                "start_time_ns": started_wall,
                "end_time_ns": ended_wall,
                "duration_ns": duration,
                "response": mapping,
                "cost": cost,
                "cost_source": cost_source,
                "response_headers": headers,
                "hidden_metadata": hidden,
                "raw_response_class": type(response).__name__,
            }
            self._event_sink("model.response", response_payload)
            self._span_sink(
                {
                    "name": "model.call",
                    "call_id": call_id,
                    "span_id": span_id,
                    **lane_fields,
                    "start_time_ns": started_wall,
                    "end_time_ns": ended_wall,
                    "duration_ns": duration,
                    "status": "OK",
                }
            )
            return response

        self._target.completion = captured
        return self

    def __exit__(
        self,
        _exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        if self._original is not None:
            self._target.completion = self._original
            self._original = None
