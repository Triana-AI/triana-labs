from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


def test_event_journal_fsyncs_each_append_before_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tau2_luna_local.journal import EventJournal

    fsynced: list[int] = []
    monkeypatch.setattr(os, "fsync", lambda descriptor: fsynced.append(descriptor))
    with EventJournal(tmp_path / "events.jsonl", timestamp_ns=lambda: 101) as journal:
        journal.append("model.request", {"call_id": "call-1"})
        assert len(fsynced) == 1
        journal.append("model.response", {"call_id": "call-1"})
        assert len(fsynced) == 2


def test_span_exporter_fsyncs_each_export_before_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tau2_luna_local.otel import JsonlSpanExporter

    fsynced: list[int] = []
    monkeypatch.setattr(os, "fsync", lambda descriptor: fsynced.append(descriptor))
    exporter = JsonlSpanExporter(tmp_path / "spans.jsonl")
    span: Any = SimpleNamespace(
        name="model.call",
        context=SimpleNamespace(trace_id=1, span_id=2),
        parent=SimpleNamespace(span_id=1),
        start_time=100,
        end_time=200,
        status=SimpleNamespace(status_code=SimpleNamespace(name="OK")),
        attributes={"evidence.call_id": "call-1"},
        events=[],
        resource=SimpleNamespace(attributes={"service.name": "test"}),
        instrumentation_scope=SimpleNamespace(name="tau2-test"),
    )
    try:
        exporter.export([span])
        assert len(fsynced) == 1
    finally:
        exporter.shutdown()
