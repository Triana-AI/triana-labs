"""Exact fail-fast local-resource ceilings and inherited Observer boundaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import (
    ENVIRON,
    ScriptedTransport,
    api,
    artifact_hash,
    build_upstream,
    canonical,
    write_config,
)

KIB = 1024
MIB = 1024 * KIB
CONFIG_LIMIT = 64 * KIB
INTELLIGENCE_LIMITS = {
    "clusters.json": 16 * MIB,
    "derivation_report.json": MIB,
    "personas/index.json": MIB,
    "intents/index.json": MIB,
    "turn_policies/index.json": MIB,
}
OBSERVER_LIMITS = {
    "corpus_profile.json": MIB,
    "corpus_profile.md": MIB,
    "normalized_traces.jsonl": 16 * MIB,
    "rejected_traces.jsonl": 16 * MIB,
}


def assert_refusal(
    observer: Path,
    intelligence: Path,
    config: Path,
    output: Path,
    reason: str,
    exit_code: int,
) -> None:
    generate_module, _ = api()
    transport = ScriptedTransport([])
    with pytest.raises(Exception) as caught:
        generate_module.generate(
            observer,
            intelligence,
            config,
            output,
            cache_path=output.parent / "provider-cache",
            transport=transport,
            environ=ENVIRON,
        )
    assert caught.value.__class__.__name__ == "GenerateFailure"
    assert caught.value.reason_code == reason
    assert caught.value.exit_code == exit_code
    assert transport.requests == []
    assert not output.exists()


def rehash_intelligence_artifact(
    manifest_path: Path, name: str, payload: bytes
) -> None:
    artifact = manifest_path.parent / name
    artifact.write_bytes(payload)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["artifacts"][name] = artifact_hash(payload)
    manifest_path.write_bytes(canonical(manifest, lf=True))


def rehash_observer_artifact(manifest_path: Path, name: str, payload: bytes) -> None:
    artifact = manifest_path.parent / name
    artifact.write_bytes(payload)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["artifacts"][name] = artifact_hash(payload)
    manifest_path.write_bytes(canonical(manifest, lf=True))


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(b"x" * CONFIG_LIMIT + b"\n", id="above-byte-limit"),
        pytest.param(b"{}\n{}\n", id="second-physical-line"),
    ],
)
def test_config_resource_excess_precedes_parsing(
    tmp_path: Path, payload: bytes
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = tmp_path / "config.json"
    config.write_bytes(payload)
    assert_refusal(
        observer,
        intelligence,
        config,
        tmp_path / "output",
        "INPUT_TOO_LARGE",
        3,
    )


def test_config_exact_ceiling_is_parsed_instead_of_classified_as_too_large(
    tmp_path: Path,
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = tmp_path / "config.json"
    config.write_bytes(b"x" * (CONFIG_LIMIT - 1) + b"\n")
    assert config.stat().st_size == CONFIG_LIMIT
    assert_refusal(
        observer,
        intelligence,
        config,
        tmp_path / "output",
        "CONFIG_INVALID",
        2,
    )


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(b"x" * MIB + b"\n", id="above-byte-limit"),
        pytest.param(b"{}\n{}\n", id="second-physical-line"),
    ],
)
def test_intelligence_manifest_resource_excess_precedes_parsing(
    tmp_path: Path, payload: bytes
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    intelligence.write_bytes(payload)
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "INPUT_TOO_LARGE",
        3,
    )


def test_intelligence_manifest_exact_ceiling_reaches_manifest_validation(
    tmp_path: Path,
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    intelligence.write_bytes(b"x" * (MIB - 1) + b"\n")
    assert intelligence.stat().st_size == MIB
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "MANIFEST_INVALID",
        4,
    )


@pytest.mark.parametrize(("name", "limit"), INTELLIGENCE_LIMITS.items())
def test_correctly_rehashed_oversized_intelligence_artifact_still_refuses_first(
    tmp_path: Path, name: str, limit: int
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    payload = b"x" * limit + b"\n"
    rehash_intelligence_artifact(intelligence, name, payload)
    assert json.loads(intelligence.read_bytes())["artifacts"][name] == artifact_hash(
        payload
    )
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "INPUT_TOO_LARGE",
        3,
    )


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(b"x" * MIB + b"\n", id="above-byte-limit"),
        pytest.param(b"{}\n{}\n", id="second-physical-line"),
    ],
)
def test_intelligence_resource_excess_precedes_stale_digest_mismatch(
    tmp_path: Path, payload: bytes
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    (intelligence.parent / "derivation_report.json").write_bytes(payload)
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "INPUT_TOO_LARGE",
        3,
    )


@pytest.mark.parametrize(("name", "_limit"), INTELLIGENCE_LIMITS.items())
def test_rehashed_second_line_in_intelligence_artifact_is_resource_excess(
    tmp_path: Path, name: str, _limit: int
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    payload = (intelligence.parent / name).read_bytes() + b"\n"
    rehash_intelligence_artifact(intelligence, name, payload)
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "INPUT_TOO_LARGE",
        3,
    )


@pytest.mark.parametrize(("name", "limit"), INTELLIGENCE_LIMITS.items())
def test_intelligence_artifact_exact_ceiling_reaches_integrity_validation(
    tmp_path: Path, name: str, limit: int
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    payload = b"x" * (limit - 1) + b"\n"
    rehash_intelligence_artifact(intelligence, name, payload)
    assert (intelligence.parent / name).stat().st_size == limit
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "INTELLIGENCE_MISMATCH",
        5,
    )


@pytest.mark.parametrize(("name", "limit"), OBSERVER_LIMITS.items())
def test_inherited_observer_artifact_byte_limits_are_not_widened(
    tmp_path: Path, name: str, limit: int
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    payload = b"x" * limit + b"\n"
    rehash_observer_artifact(observer, name, payload)
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "INPUT_TOO_LARGE",
        3,
    )


@pytest.mark.parametrize(
    ("payload", "reason", "exit_code"),
    [
        pytest.param(b"x" * MIB + b"\n", "INPUT_TOO_LARGE", 3, id="above-byte-limit"),
        pytest.param(b"x" * (MIB - 1) + b"\n", "MANIFEST_INVALID", 4, id="exact-limit"),
    ],
)
def test_inherited_observer_manifest_ceiling_is_literal(
    tmp_path: Path, payload: bytes, reason: str, exit_code: int
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    observer.write_bytes(payload)
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        reason,
        exit_code,
    )


@pytest.mark.parametrize(
    ("payload", "reason", "exit_code"),
    [
        pytest.param(b"{}\n" * 1001, "INPUT_TOO_LARGE", 3, id="1001-lines"),
        pytest.param(b"x" * MIB + b"\n", "INPUT_TOO_LARGE", 3, id="line-above-one-mib"),
        pytest.param(
            b"x" * (MIB - 1) + b"\n",
            "CORPUS_INTEGRITY_FAILED",
            5,
            id="line-exactly-one-mib",
        ),
    ],
)
def test_inherited_observer_trace_line_limits_are_literal(
    tmp_path: Path, payload: bytes, reason: str, exit_code: int
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    rehash_observer_artifact(observer, "normalized_traces.jsonl", payload)
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        reason,
        exit_code,
    )


def test_invalid_selected_observer_never_reads_valid_backup_or_schema_fallback(
    tmp_path: Path,
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    valid_bytes = observer.read_bytes()
    observer.with_name("manifest.backup.json").write_bytes(valid_bytes)
    observer.write_bytes(canonical({"artifact_kind": "legacy_trace_manifest"}, lf=True))
    assert_refusal(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "output",
        "MANIFEST_INVALID",
        4,
    )
