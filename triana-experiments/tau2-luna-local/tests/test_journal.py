from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from conftest import EVENT_DOMAIN, canonical_bytes


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("tau2_luna_local") is None,
    reason="production package absent; test_package_contract owns the RED signal",
)


def test_journal_writes_monotonic_domain_separated_chain(tmp_path: Path) -> None:
    from tau2_luna_local.journal import EventJournal, verify_event_chain

    ticks = iter([101, 102])
    path = tmp_path / "events.jsonl"
    with EventJournal(path, timestamp_ns=lambda: next(ticks)) as journal:
        first = journal.append("run.started", {"run_id": "run-1"})
        second = journal.append("run.finished", {"run_id": "run-1"})

    assert first["sequence"] == 1
    assert second["sequence"] == 2
    assert second["previous_event_hash"] == first["event_hash"]
    unhashed = dict(first)
    actual_hash = unhashed.pop("event_hash")
    assert actual_hash == hashlib.sha256(EVENT_DOMAIN + canonical_bytes(unhashed)).hexdigest()
    assert verify_event_chain(path)["valid"] is True


@pytest.mark.parametrize("mutation", ["payload", "sequence", "previous_hash", "malformed"])
def test_journal_tamper_is_invalid(tmp_path: Path, mutation: str) -> None:
    from tau2_luna_local.journal import EventJournal, verify_event_chain

    path = tmp_path / "events.jsonl"
    with EventJournal(path, timestamp_ns=lambda: 101) as journal:
        journal.append("run.started", {"run_id": "run-1"})
    record = json.loads(path.read_text())
    if mutation == "payload":
        record["payload"]["run_id"] = "tampered"
    elif mutation == "sequence":
        record["sequence"] = 2
    elif mutation == "previous_hash":
        record["previous_event_hash"] = "0" * 64
    else:
        path.write_text("{not-json}\n")
        assert verify_event_chain(path)["valid"] is False
        return
    path.write_bytes(canonical_bytes(record) + b"\n")
    assert verify_event_chain(path)["valid"] is False


def test_identical_events_with_fixed_clock_produce_identical_bytes(tmp_path: Path) -> None:
    from tau2_luna_local.journal import EventJournal

    paths = [tmp_path / "one.jsonl", tmp_path / "two.jsonl"]
    for path in paths:
        with EventJournal(path, timestamp_ns=lambda: 101) as journal:
            journal.append("model.request", {"call_id": "fixed", "messages": []})
    assert paths[0].read_bytes() == paths[1].read_bytes()
