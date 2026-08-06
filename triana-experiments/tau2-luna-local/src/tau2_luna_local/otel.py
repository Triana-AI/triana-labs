from __future__ import annotations

import os
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Status, StatusCode

from .capture import redact
from .serde import canonical_bytes


class JsonlSpanExporter(SpanExporter):
    """Synchronous, local-only exporter; it has no endpoint or network client."""

    def __init__(
        self,
        path: Path,
        *,
        secrets: Sequence[str] = (),
        remote_append: Callable[[str, bytes, str], None] | None = None,
        remote_object_name: str | None = None,
    ) -> None:
        self.path = path
        self._secrets = tuple(secrets)
        self._lock = threading.Lock()
        self._remote_append = remote_append
        self._remote_object_name = remote_object_name
        if (remote_append is None) != (remote_object_name is None):
            raise ValueError("remote append and object name must be configured together")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.path.open("x", encoding="utf-8")

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with self._lock:
            for span in spans:
                context = span.context
                parent = span.parent
                projection: dict[str, Any] = {
                    "name": span.name,
                    "trace_id": f"{context.trace_id:032x}" if context is not None else None,
                    "span_id": f"{context.span_id:016x}" if context is not None else None,
                    "parent_span_id": f"{parent.span_id:016x}" if parent is not None else None,
                    "start_time_ns": span.start_time,
                    "end_time_ns": span.end_time,
                    "status": span.status.status_code.name,
                    "attributes": dict(span.attributes or {}),
                    "events": [
                        {
                            "name": event.name,
                            "timestamp_ns": event.timestamp,
                            "attributes": dict(event.attributes or {}),
                        }
                        for event in span.events
                    ],
                    "resource": dict(span.resource.attributes),
                    "instrumentation_scope": (
                        span.instrumentation_scope.name if span.instrumentation_scope is not None else None
                    ),
                }
                safe = redact(projection, secrets=self._secrets)
                line = canonical_bytes(safe) + b"\n"
                self._stream.write(line.decode("utf-8"))
                self._stream.flush()
                os.fsync(self._stream.fileno())
                if self._remote_append is not None and self._remote_object_name is not None:
                    import hashlib

                    self._remote_append(self._remote_object_name, line, hashlib.sha256(line).hexdigest())
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        with self._lock:
            if not self._stream.closed:
                self._stream.flush()
                self._stream.close()


class LocalTelemetry:
    def __init__(
        self,
        path: Path,
        *,
        run_id: str,
        secrets: Sequence[str] = (),
        remote_append: Callable[[str, bytes, str], None] | None = None,
        remote_object_name: str | None = None,
    ) -> None:
        self.exporter = JsonlSpanExporter(
            path,
            secrets=secrets,
            remote_append=remote_append,
            remote_object_name=remote_object_name,
        )
        self.provider = TracerProvider(
            resource=Resource.create({"service.name": "tau2-luna-local", "run.id": run_id})
        )
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer = self.provider.get_tracer("tau2_luna_local", "0.1.0")
        self._run_span: Any = None
        self._scope: Any = None

    def __enter__(self) -> LocalTelemetry:
        self._run_span = self.tracer.start_span("run", attributes={"run.id": self.exporter.path.parent.name})
        self._scope = trace.use_span(self._run_span, end_on_exit=False)
        self._scope.__enter__()
        return self

    def record_model_span(self, payload: dict[str, Any]) -> None:
        attributes = {
            "evidence.call_id": str(payload["call_id"]),
            "evidence.span_id": str(payload["span_id"]),
            "llm.role_lane": str(payload["role_lane"]),
        }
        span = self.tracer.start_span(
            "model.call", attributes=attributes, start_time=int(payload["start_time_ns"])
        )
        if payload["status"] == "ERROR":
            span.set_status(Status(StatusCode.ERROR, str(payload.get("exception_class", "provider error"))))
        else:
            span.set_status(Status(StatusCode.OK))
        span.end(end_time=int(payload["end_time_ns"]))

    def boundary(self, name: str, attributes: dict[str, str] | None = None) -> Any:
        return self.tracer.start_as_current_span(name, attributes=attributes or {})

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._run_span is not None:
            if exc is None:
                self._run_span.set_status(Status(StatusCode.OK))
            else:
                self._run_span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
            self._run_span.end()
        if self._scope is not None:
            self._scope.__exit__(exc_type, exc, traceback)
        self.provider.shutdown()
