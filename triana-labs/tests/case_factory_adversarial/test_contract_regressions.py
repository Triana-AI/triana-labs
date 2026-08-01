"""Adversarial regressions for the frozen LABS-04 wire contract."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _acceptance_helpers() -> ModuleType:
    path = Path(__file__).parents[1] / "case_factory_acceptance" / "conftest.py"
    spec = importlib.util.spec_from_file_location("labs04_acceptance_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("acceptance helper module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


HELPERS = _acceptance_helpers()


def _invoke(
    tmp_path: Path,
    observer: Path,
    intelligence: Path,
    callbacks: list[Any],
    *,
    publisher: Any,
) -> tuple[Any, Any]:
    generate_module, _ = HELPERS.api()
    transport = HELPERS.ScriptedTransport(callbacks)
    result = generate_module.generate(
        observer,
        intelligence,
        HELPERS.write_config(tmp_path),
        tmp_path / "case-factory",
        cache_path=tmp_path / "provider-cache",
        transport=transport,
        environ=HELPERS.ENVIRON,
        publisher=publisher,
    )
    return result, transport


def _rehash_intelligence_artifact(
    intelligence: Path, manifest: dict[str, Any], name: str, value: Any
) -> None:
    payload = HELPERS.canonical(value, lf=True)
    (intelligence.parent / name).write_bytes(payload)
    manifest["artifacts"][name] = HELPERS.artifact_hash(payload)


def test_self_consistent_forged_intelligence_refuses_before_egress(
    tmp_path: Path,
) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path)
    manifest = json.loads(intelligence.read_bytes())
    manifest.update(
        artifact_kind="forged_kind",
        schema_version=999,
        privacy_class="FORGED",
        producer={"name": "attacker"},
        fidelity="REAL",
        counts={"trace_count": 999_999},
        forged=True,
    )
    for name in (
        "derivation_report.json",
        "personas/index.json",
        "intents/index.json",
        "turn_policies/index.json",
    ):
        _rehash_intelligence_artifact(intelligence, manifest, name, {"forged": True})
    clusters_path = intelligence.parent / "clusters.json"
    clusters = json.loads(clusters_path.read_bytes())
    clusters["forged"] = True
    for cluster in clusters["clusters"]:
        cluster["forged"] = True
    _rehash_intelligence_artifact(intelligence, manifest, "clusters.json", clusters)
    intelligence.write_bytes(HELPERS.canonical(manifest, lf=True))

    generate_module, _ = HELPERS.api()
    transport = HELPERS.ScriptedTransport(
        [
            HELPERS.proposal_callback(),
            HELPERS.critique_callback,
            HELPERS.proposal_callback(),
        ]
    )
    output = tmp_path / "case-factory"
    with pytest.raises(generate_module.GenerateFailure) as caught:
        generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path),
            output,
            cache_path=tmp_path / "provider-cache",
            transport=transport,
            environ=HELPERS.ENVIRON,
        )

    assert (caught.value.reason_code, caught.value.exit_code) == (
        "INTELLIGENCE_MISMATCH",
        5,
    )
    assert transport.requests == []
    assert not output.exists()


def _large_proposal(request: Any) -> tuple[int, bytes]:
    user = HELPERS.request_user_value(request)
    proposal = HELPERS.valid_proposal(user["citations"])
    generated = {
        "text": "x" * 4096,
        "basis": "GENERATED_VARIATION",
        "claim_keys": [],
    }
    proposal["personas"][0]["constraints"] = [generated] * 20
    proposal["personas"][0]["communication_tendencies"] = [generated] * 20
    proposal["intents"][0]["known_constraints"] = [generated] * 20
    return 200, HELPERS.azure_body(proposal)


def _large_critique(_request: Any) -> tuple[int, bytes]:
    issues = [
        {
            "issue_key": f"issue_{index}",
            "severity": "MINOR",
            "target_kind": "CASE",
            "target_key": "case_0",
            "reason_code": "WEAK_EVALUATION",
            "explanation": "x" * 4096,
            "citation_ids": [],
        }
        for index in range(60)
    ]
    return 200, HELPERS.azure_body({"issues": issues})


@pytest.mark.parametrize(
    ("callbacks", "expected_reason", "expected_calls"),
    [
        pytest.param(
            [_large_proposal],
            "CRITIQUE_REQUEST_TOO_LARGE",
            1,
            id="critique",
        ),
        pytest.param(
            [HELPERS.proposal_callback(), _large_critique],
            "REVISION_REQUEST_TOO_LARGE",
            2,
            id="revise",
        ),
    ],
)
def test_later_stage_request_limit_has_exact_partial_reason(
    tmp_path: Path,
    callbacks: list[Callable[[Any], tuple[int, bytes]]],
    expected_reason: str,
    expected_calls: int,
) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path)
    publisher = HELPERS.CapturePublisher()

    result, transport = _invoke(
        tmp_path, observer, intelligence, callbacks, publisher=publisher
    )

    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == expected_reason
    assert len(transport.requests) == expected_calls
    assert publisher.artifacts is not None


def test_non_money_provider_cost_closes_as_typed_provider_failure(
    tmp_path: Path,
) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path)

    def invalid_cost(request: Any) -> tuple[int, bytes]:
        user = HELPERS.request_user_value(request)
        body = json.loads(HELPERS.azure_body(HELPERS.valid_proposal(user["citations"])))
        body["usage"]["cost"] = "not-money"
        return 200, HELPERS.canonical(body)

    generate_module, _ = HELPERS.api()
    transport = HELPERS.ScriptedTransport([invalid_cost])
    output = tmp_path / "case-factory"
    with pytest.raises(generate_module.GenerateFailure) as caught:
        generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path),
            output,
            cache_path=tmp_path / "provider-cache",
            transport=transport,
            environ=HELPERS.ENVIRON,
        )

    assert (caught.value.reason_code, caught.value.exit_code) == (
        "PROVIDER_FAILED",
        8,
    )
    assert len(transport.requests) == 1
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["artifact_kind"] == "case_factory_failure_manifest"
    assert manifest["reason_code"] == "PROVIDER_FAILED"


def test_atomic_publisher_fsyncs_staging_directory_before_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, provider = HELPERS.api()
    timeline: list[str] = []
    real_fsync = provider.os.fsync
    real_rename = Path.rename

    def record_fsync(file_descriptor: int) -> None:
        kind = (
            "directory-fsync"
            if stat.S_ISDIR(os.fstat(file_descriptor).st_mode)
            else "file-fsync"
        )
        timeline.append(kind)
        real_fsync(file_descriptor)

    def record_rename(source: Path, target: Path) -> Path:
        timeline.append("rename")
        return real_rename(source, target)

    monkeypatch.setattr(provider.os, "fsync", record_fsync)
    monkeypatch.setattr(Path, "rename", record_rename)
    provider.AtomicPublisher().publish(
        tmp_path / "published",
        {"artifact.json": b"{}\n", "manifest.json": b"{}\n"},
    )

    assert "directory-fsync" in timeline
    assert timeline.index("directory-fsync") < timeline.index("rename")


def test_publish_race_never_replaces_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path)
    generate_module, provider = HELPERS.api()
    transport = HELPERS.ScriptedTransport(
        [
            HELPERS.proposal_callback(),
            HELPERS.critique_callback,
            HELPERS.proposal_callback(),
        ]
    )
    output = tmp_path / "case-factory"
    real_lexists = provider.os.path.lexists
    checks = 0
    raced_inode: int | None = None

    def race_after_final_check(path: str | bytes | os.PathLike[str]) -> bool:
        nonlocal checks, raced_inode
        exists = real_lexists(path)
        if Path(path) == output:
            checks += 1
            if checks == 2 and not exists:
                output.mkdir()
                raced_inode = output.stat().st_ino
        return exists

    monkeypatch.setattr(provider.os.path, "lexists", race_after_final_check)
    with pytest.raises(generate_module.GenerateFailure) as caught:
        generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path),
            output,
            cache_path=tmp_path / "provider-cache",
            transport=transport,
            environ=HELPERS.ENVIRON,
        )

    assert (caught.value.reason_code, caught.value.exit_code) == (
        "OUTPUT_WRITE_FAILED",
        7,
    )
    assert len(transport.requests) == 3
    assert raced_inode is not None
    assert output.stat().st_ino == raced_inode
    assert list(output.iterdir()) == []
