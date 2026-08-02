"""Validation, deterministic control, accounting, and custody for LABS-05."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from triana_labs.case_factory.provider import AtomicPublisher, PublicationFailure

from .contracts import (
    AdaptiveRunFailure,
    AdaptiveRunResult,
    ArtifactPublisher,
    CaseFactoryInputLoader,
    Clock,
    JsonObject,
    SimulatorResponse,
    SimulatorTransport,
    TargetLaunch,
    TargetProcessFactory,
    TargetProtocolFailure,
    TargetSourceIdentity,
    TargetSourceVerifier,
    VerifiedCaseFactoryInput,
    VerifiedCaseProjection,
)

WIRE = "LABS05_WIRE_V1"
MANIFEST_HASH = (
    "sha256:817000637daef25bff9bd95eee46a25976f575d1b2d5aa62965a6c6d9c5b6cb9"
)
CASE_HASH = "sha256:06a3a2267f39041d98e08ef24466ffbc695e7833ebb16bd536f19f71c37ecbe4"
CASE_IDS = (
    "case-b2b9570f6e763ca0",
    "case-62ca79446e3a22d5",
    "case-9a0d8a895afcd860",
)
OUTPUTS = (
    "episode_attempts.jsonl",
    "transcripts.jsonl",
    "target_tool_events.jsonl",
    "provider_ledger.jsonl",
    "gaps.jsonl",
    "trajectory_clusters.json",
    "human_adaptation_review.json",
)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_ENV = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_PORTABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_MONEY = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_DNS = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*$"
)
_MAX_INT = 9_007_199_254_740_991


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    data = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return data + (b"\n" if lf else b"")


def _hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _has_secret(value: Any, sentinels: tuple[bytes, ...]) -> bool:
    """Check exact configured secret bytes before hashing or retaining a response."""

    if isinstance(value, bytes):
        return any(sentinel and sentinel in value for sentinel in sentinels)
    if isinstance(value, str):
        return _has_secret(value.encode(), sentinels)
    if isinstance(value, dict):
        return any(
            _has_secret(key, sentinels) or _has_secret(item, sentinels)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_has_secret(item, sentinels) for item in value)
    return False


def _integer(value: Any) -> bool:
    return type(value) is int and 0 <= value <= _MAX_INT


def _text(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, str)
        and (not nonempty or bool(value))
        and len(value.encode()) <= 16_384
        and all(ord(char) >= 32 or char == "\n" for char in value)
        and not any(127 <= ord(char) <= 159 for char in value)
    )


def _money(value: Any) -> bool:
    return value is None or _text(value) and _MONEY.fullmatch(value) is not None


def _bounded_json(value: Any, depth: int = 1) -> bool:
    if depth > 8:
        return False
    if value is None or isinstance(value, (str, bool)) or _integer(value):
        return _text(value) if isinstance(value, str) else True
    if isinstance(value, list):
        return len(value) <= 100 and all(
            _bounded_json(item, depth + 1) for item in value
        )
    if isinstance(value, dict):
        return len(value) <= 100 and all(
            isinstance(key, str) and _text(key) and _bounded_json(item, depth + 1)
            for key, item in value.items()
        )
    return False


def _safe_usage(response: Any) -> dict[str, Any]:
    usage = response.get("usage") if isinstance(response, dict) else None
    if not isinstance(usage, dict):
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "provider_http_exchange_count": 0,
        }
    return {
        key: value if _integer(value) else 0
        for key, value in (
            ("input_tokens", usage.get("input_tokens")),
            ("output_tokens", usage.get("output_tokens")),
            ("provider_http_exchange_count", usage.get("provider_http_exchange_count")),
        )
    }


def _id(prefix: str, value: Any) -> str:
    return f"{prefix}-{hashlib.sha256(_canonical(value)).hexdigest()[:16]}"


def _read_object(
    path: Path, reason: str, exit_code: int
) -> tuple[dict[str, Any], bytes]:
    try:
        if path.is_symlink():
            raise OSError
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise OSError
            payload = stream.read(65_537)
        if len(payload) > 65_536 or not payload.endswith(b"\n"):
            raise ValueError
        value = json.loads(payload, object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise AdaptiveRunFailure(reason, exit_code) from error
    if not isinstance(value, dict):
        raise AdaptiveRunFailure(reason, exit_code)
    return value, payload


def _closed(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _strict_int(value: Any, expected: int) -> bool:
    return type(value) is int and value == expected


def _validate_review(value: dict[str, Any]) -> None:
    keys = set(
        "artifact_kind schema_version rubric_version case_factory_manifest_file_hash case_candidate_file_hash reviewer review_date review_state cases".split()  # noqa: SIM905
    )
    if not _closed(value, keys):
        raise AdaptiveRunFailure("REVIEW_INVALID", 4)
    structural = (
        value["artifact_kind"] == "labs04_usefulness_ruling"
        and _strict_int(value["schema_version"], 1)
        and value["rubric_version"] == "LABS04_USEFULNESS_V1"
        and value["case_factory_manifest_file_hash"] == MANIFEST_HASH
        and value["case_candidate_file_hash"] == CASE_HASH
        and value["reviewer"] == "Akarsh"
        and value["review_date"] == "2026-08-02"
        and isinstance(value["cases"], list)
        and len(value["cases"]) == 5
    )
    if not structural:
        raise AdaptiveRunFailure("REVIEW_INVALID", 4)
    case_keys = set(
        "case_id would_run opening_understandable adaptive_multi_turn judgeable_expected_behavior materially_distinct support_sufficient depends_on_hidden_or_fabricated_fact".split()  # noqa: SIM905
    )
    ids: list[str] = []
    accepted = value["review_state"] == "PASSED"
    for item in value["cases"]:
        if not _closed(item, case_keys) or not isinstance(item["case_id"], str):
            raise AdaptiveRunFailure("REVIEW_INVALID", 4)
        ids.append(item["case_id"])
        accepted = (
            accepted
            and all(
                item[key] is True
                for key in (
                    "would_run",
                    "opening_understandable",
                    "adaptive_multi_turn",
                    "judgeable_expected_behavior",
                    "materially_distinct",
                    "support_sufficient",
                )
            )
            and item["depends_on_hidden_or_fabricated_fact"] is False
        )
    if (
        ids != sorted(ids)
        or len(ids) != len(set(ids))
        or not set(CASE_IDS).issubset(ids)
    ):
        raise AdaptiveRunFailure("REVIEW_INVALID", 4)
    if not accepted:
        raise AdaptiveRunFailure("REVIEW_NOT_ACCEPTED", 4)


def _validate_config(value: dict[str, Any], environ: Mapping[str, str]) -> None:
    top = set(
        "artifact_kind schema_version protocol_version privacy_class selected_case_ids simulator target budget".split()  # noqa: SIM905
    )
    if not _closed(value, top):
        raise AdaptiveRunFailure("CONFIG_INVALID", 2)
    if value["privacy_class"] != "SYNTHETIC":
        raise AdaptiveRunFailure("UNSUPPORTED_PRIVACY_CLASS", 4)
    if not (
        value["artifact_kind"] == "adaptive_runner_config"
        and _strict_int(value["schema_version"], 1)
        and value["protocol_version"] == WIRE
        and value["selected_case_ids"] == list(CASE_IDS)
    ):
        raise AdaptiveRunFailure("CONFIG_INVALID", 2)
    simulator = value["simulator"]
    sim_keys = set(
        "provider_kind endpoint allowed_host api_key_env deployment model_name model_version seed prompt_version timeout_seconds".split()  # noqa: SIM905
    )
    if not _closed(simulator, sim_keys):
        raise AdaptiveRunFailure("CONFIG_INVALID", 2)
    if not (
        simulator["provider_kind"] == "MICROSOFT_FOUNDRY_FIREWORKS"
        and simulator["deployment"] == "FW-GLM-5.2"
        and simulator["model_name"] == "FW-GLM-5.2"
        and simulator["model_version"] == "1"
        and _strict_int(simulator["seed"], 2026080205)
        and simulator["prompt_version"] == "LABS05_ADAPTIVE_USER_V1"
        and _strict_int(simulator["timeout_seconds"], 180)
        and isinstance(simulator["api_key_env"], str)
        and _ENV.fullmatch(simulator["api_key_env"])
    ):
        raise AdaptiveRunFailure("CONFIG_INVALID", 2)
    url = urlsplit(
        simulator["endpoint"] if isinstance(simulator["endpoint"], str) else ""
    )
    if not (
        url.scheme == "https"
        and url.hostname == simulator["allowed_host"]
        and url.port is None
        and isinstance(simulator["allowed_host"], str)
        and _DNS.fullmatch(simulator["allowed_host"]) is not None
        and url.path == "/openai/v1"
        and not url.username
        and not url.password
        and not url.query
        and not url.fragment
    ):
        raise AdaptiveRunFailure("SIMULATOR_ENDPOINT_REFUSED", 4)
    target = value["target"]
    kind = target.get("connector_kind") if isinstance(target, dict) else None
    if kind == "HTTP_JSON_V1":
        from .http_target import validate_http_target

        validate_http_target(target, environ)
        target_http = 15 if target["session"]["mode"] == "REMOTE_SESSION" else 9
    elif kind == "EXECUTABLE_JSONL_V1":
        keys = set(
            "connector_id connector_kind data_class state_isolation target_identity protocol source_commit argv cwd env_names timeout_seconds".split()  # noqa: SIM905
        )
        argv, names, identity = (
            target.get("argv"),
            target.get("env_names"),
            target.get("target_identity"),
        )
        if not (
            _closed(target, keys)
            and target["data_class"] == "SYNTHETIC_LOCAL_TARGET"
            and target["state_isolation"] == "EPISODE_PROCESS"
            and isinstance(target["connector_id"], str)
            and _PORTABLE_ID.fullmatch(target["connector_id"])
            and isinstance(target["protocol"], str)
            and _PORTABLE_ID.fullmatch(target["protocol"])
            and isinstance(target["source_commit"], str)
            and re.fullmatch(r"[0-9a-f]{40}", target["source_commit"])
            and _closed(
                identity,
                {"agent_id", "protocol", "version", "model", "prompt", "tools"},
            )
            and all(
                _text(identity[key], nonempty=True)
                for key in ("agent_id", "protocol", "version")
            )
            and all(
                identity[key] is None or _text(identity[key], nonempty=True)
                for key in ("model", "prompt", "tools")
            )
            and not _has_secret(
                identity,
                tuple(item.encode() for item in environ.values() if item),
            )
            and _strict_int(target["timeout_seconds"], 180)
            and isinstance(argv, list)
            and 2 <= len(argv) <= 8
            and all(
                isinstance(item, str) and 1 <= len(item.encode()) <= 4096
                for item in argv
            )
            and all(os.path.isabs(item) for item in argv[:2])
            and sum(len(item.encode()) for item in argv) <= 16_384
            and isinstance(target["cwd"], str)
            and os.path.isabs(target["cwd"])
            and isinstance(names, list)
            and len(names) == len(set(names))
            and all(isinstance(name, str) and _ENV.fullmatch(name) for name in names)
        ):
            raise AdaptiveRunFailure("TARGET_CONNECTOR_CONFIG_INVALID", 2)
        target_http = 0
    else:
        raise AdaptiveRunFailure("TARGET_CONNECTOR_CONFIG_INVALID", 2)
    expected_budget = {
        "all_http_exchanges": target_http + 6,
        "episode_count": 3,
        "episode_timeout_seconds": 180,
        "max_usd": "23.000000",
        "role_turns_per_episode": 6,
        "run_timeout_seconds": 600,
        "simulator_http_exchanges": 6,
        "simulator_input_tokens_per_exchange": 131072,
        "simulator_output_tokens_per_exchange": 4096,
        "simulator_reservation_usd_per_exchange": "1.000000",
        "target_http_exchanges": target_http,
        "target_reservation_usd_per_turn": "1.888888",
    }
    if value["budget"] != expected_budget:
        raise AdaptiveRunFailure("CONFIG_INVALID", 2)


def _validate_cases(source: VerifiedCaseFactoryInput) -> None:
    if (
        source.manifest_file_hash != MANIFEST_HASH
        or source.case_candidate_file_hash != CASE_HASH
    ):
        raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
    if not _DIGEST.fullmatch(source.input_manifest_hash) or not _DIGEST.fullmatch(
        source.intelligence_manifest_hash
    ):
        raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
    if tuple(item.case.get("case_id") for item in source.cases) != CASE_IDS:
        raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
    for item in source.cases:
        case = item.case
        if not all(
            isinstance(value, dict)
            for value in (case, item.persona, item.intent, item.turn_policy)
        ):
            raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)
        if not (
            case.get("artifact_kind") == "simulation_case_candidate"
            and case.get("schema_version") == 1
            and case.get("proposal_state") == "PROPOSED"
            and case.get("fidelity") == "SYNTHETIC_CORPUS_GROUNDED"
            and case.get("persona_id") == item.persona.get("persona_id")
            and case.get("intent_id") == item.intent.get("intent_id")
            and case.get("turn_policy_id") == item.turn_policy.get("turn_policy_id")
            and case.get("input_manifest_hash") == source.input_manifest_hash
            and case.get("intelligence_manifest_hash")
            == source.intelligence_manifest_hash
            and isinstance(case.get("scenario"), dict)
            and isinstance(case["scenario"].get("opening_user_turn"), dict)
            and isinstance(case["scenario"]["opening_user_turn"].get("text"), str)
        ):
            raise AdaptiveRunFailure("CASE_INTEGRITY_FAILED", 4)


@dataclass
class _Episode:
    episode_id: str
    attempt_id: str
    slot: int
    case_id: str
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    ledger: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    termination: str = "TURN_LIMIT_REACHED"
    valid: bool = False
    fingerprint: str | None = None
    effective: bool = False
    sim_http: int = 0
    target_http: int = 0
    sim_input: int = 0
    sim_output: int = 0
    target_input: int = 0
    target_output: int = 0
    tool_count: int = 0
    reported_http: int = 0
    reported_model: int = 0
    reported_input: int = 0
    reported_output: int = 0
    reported_cost: Decimal | None = None
    reserved: Decimal = Decimal(0)
    actual: Decimal | None = None


def _lineage(manifest: str, review: str, config: str) -> dict[str, Any]:
    return {
        "artifact_kind": "labs05_record",
        "schema_version": 1,
        "protocol_version": WIRE,
        "case_factory_manifest_hash": manifest,
        "owner_review_hash": review,
        "config_hash": config,
    }


def _turn_record(
    base: dict[str, Any],
    episode: _Episode,
    ordinal: int,
    role: str,
    content: str,
    source: str,
    attempt_id: str,
    **extra: Any,
) -> dict[str, Any]:
    seed = [episode.episode_id, ordinal, role, content]
    return {
        **base,
        "record_id": _id("turn", seed),
        "episode_id": episode.episode_id,
        "ordinal": ordinal,
        "role": role,
        "content": content,
        "source": source,
        "source_attempt_id": attempt_id,
        **extra,
    }


def _validate_ready(value: JsonObject, hello: JsonObject) -> int:
    keys = set(hello) | {"memory_state", "fallback_enabled"}
    create_http = value.get("create_http_exchange_count", 0)
    if "create_http_exchange_count" in value:
        keys.add("create_http_exchange_count")
    if (
        not _closed(value, keys)
        or not all(
            value.get(key) == item for key, item in hello.items() if key != "kind"
        )
        or value.get("kind") != "ready"
        or value.get("memory_state") != "EMPTY"
        or value.get("fallback_enabled") is not False
        or not _integer(create_http)
        or create_http > 1
    ):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    return int(create_http)


def _validate_turn(
    value: JsonObject,
    request: JsonObject,
    remaining: dict[str, int],
    prior_tool_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any] | None, list[str]]:
    base_keys = set(
        "kind episode_id turn_index status assistant_content tool_events usage reason_code".split()  # noqa: SIM905
    )
    extended = {
        "termination_signal",
        "reported_internal_usage",
        "telemetry_gaps",
        "response_provenance",
    }
    if (
        not isinstance(value, dict)
        or set(value) not in {frozenset(base_keys), frozenset(base_keys | extended)}
        or value.get("kind") != "turn_result"
        or value.get("episode_id") != request["episode_id"]
        or value.get("turn_index") != request["turn_index"]
        or not _integer(value.get("turn_index"))
    ):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    status = value["status"]
    content = value["assistant_content"]
    reason = value["reason_code"]
    reasons = {
        "SUCCEEDED": None,
        "REFUSED": "TARGET_REFUSAL",
        "TOOL_REFUSED": "TOOL_NOT_ALLOWED",
        "PROVIDER_FAILED": "PROVIDER_ERROR",
        "BUDGET_EXHAUSTED": "BUDGET_EXHAUSTED",
        "TIMED_OUT": "TARGET_TIMEOUT",
        "INTERNAL_FAILED": "TARGET_INTERNAL_FAILED",
    }
    if status not in reasons or not _text(content) or reason != reasons[status]:
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    if (status == "SUCCEEDED") != bool(content):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    gaps = list(value.get("telemetry_gaps", []))
    allowed_gaps = {
        "TARGET_TOOL_TRACE_UNAVAILABLE",
        "TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE",
        "TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED",
        "TARGET_STATE_ISOLATION_UNAVAILABLE",
    }
    if len(gaps) != len(set(gaps)) or not all(item in allowed_gaps for item in gaps):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    usage = value["usage"]
    if usage is None:
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "provider_http_exchange_count": 0,
            "provider_reported_cost_usd": None,
        }
        gaps.extend(
            [
                "TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE",
                "TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED",
            ]
        )
    if not _closed(
        usage,
        {
            "input_tokens",
            "output_tokens",
            "provider_http_exchange_count",
            "provider_reported_cost_usd",
        },
    ):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    for key in ("input_tokens", "output_tokens", "provider_http_exchange_count"):
        if not _integer(usage[key]):
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    if not _money(usage["provider_reported_cost_usd"]):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    events = value["tool_events"]
    if events is None:
        events = []
        gaps.append("TARGET_TOOL_TRACE_UNAVAILABLE")
    if not isinstance(events, list):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    event_keys = set(
        "tool_event_id ordinal name arguments result status reason_code cached".split()  # noqa: SIM905
    )
    expected = list(range(prior_tool_count + 1, prior_tool_count + len(events) + 1))
    if (
        any(
            not _closed(item, event_keys)
            or not _text(item.get("name"), nonempty=True)
            or not isinstance(item.get("tool_event_id"), str)
            or _PORTABLE_ID.fullmatch(item["tool_event_id"]) is None
            or not _integer(item.get("ordinal"))
            or item.get("status") not in {"SUCCEEDED", "REFUSED", "FAILED"}
            or (item.get("reason_code") is None) != (item.get("status") == "SUCCEEDED")
            or (
                item.get("reason_code") is not None
                and (
                    not isinstance(item["reason_code"], str)
                    or _SAFE_CODE.fullmatch(item["reason_code"]) is None
                )
            )
            or type(item.get("cached")) is not bool
            or not _bounded_json(item.get("arguments"))
            or not _bounded_json(item.get("result"))
            or len(_canonical(item)) > 65_536
            for item in events
        )
        or [item["ordinal"] for item in events] != expected
    ):
        raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    if (
        usage["provider_http_exchange_count"] > remaining["http_exchanges"]
        or usage["input_tokens"] > remaining["input_tokens"]
        or usage["output_tokens"] > remaining["output_tokens"]
        or len(events) > remaining["tool_calls"]
    ):
        raise AdaptiveRunFailure("BUDGET_EXHAUSTED", 9)
    reported = value.get("reported_internal_usage")
    if reported is not None:
        if not isinstance(reported, dict) or not set(reported) <= {
            "model_exchanges",
            "http_exchanges",
            "input_tokens",
            "output_tokens",
            "cost_usd",
        }:
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
        for key, item in reported.items():
            if key == "cost_usd":
                if not _money(item) or item is None:
                    raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
            elif not _integer(item):
                raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    if set(value) == base_keys | extended:
        if (
            value["termination_signal"] is not None
            and type(value["termination_signal"]) is not bool
        ):
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
        if not _bounded_json(value["response_provenance"]):
            raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
    return events, dict(usage), reported, list(dict.fromkeys(gaps))


def _target_reason(status: str) -> str:
    return {
        "REFUSED": "TARGET_REFUSAL",
        "TOOL_REFUSED": "TARGET_TOOL_REFUSED",
        "PROVIDER_FAILED": "TARGET_PROVIDER_ERROR",
        "BUDGET_EXHAUSTED": "BUDGET_EXHAUSTED",
        "TIMED_OUT": "TARGET_TIMEOUT",
        "INTERNAL_FAILED": "TARGET_PROTOCOL_ERROR",
    }[status]


def _observation(
    assistant: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, Any]:
    core = {
        "assistant_turn_id": assistant["record_id"],
        "assistant_content": assistant["content"],
        "tool_events": events,
    }
    return {**core, "observation_hash": _hash(_canonical(core))}


def _ledger(
    base: dict[str, Any],
    episode: _Episode,
    lane: str,
    turn: int,
    status: str,
    request: bytes | None,
    response: bytes | None,
    http: int,
    input_tokens: int,
    output_tokens: int,
    reservation: Decimal,
    actual: str | None,
    reason: str | None,
) -> dict[str, Any]:
    attempt = _id("provider-attempt", [episode.episode_id, lane, turn])
    return {
        **base,
        "record_id": _id("ledger", [attempt, status]),
        "episode_id": episode.episode_id,
        "turn_ordinal": turn,
        "lane": lane,
        "attempt_id": attempt,
        "status": status,
        "request_hash": _hash(request) if request is not None else None,
        "response_hash": _hash(response) if response is not None else None,
        "provider_http_exchange_count": http,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reserved_cost_usd": f"{reservation:.6f}",
        "actual_cost_usd": actual,
        "reason_code": reason,
    }


def _run_episode(
    case: VerifiedCaseProjection,
    slot: int,
    config: dict[str, Any],
    source: TargetSourceIdentity,
    simulator: SimulatorTransport,
    target_factory: TargetProcessFactory,
    clock: Clock,
    environment: dict[str, str],
    base: dict[str, Any],
    identity_seed: dict[str, Any],
    sentinels: tuple[bytes, ...],
) -> _Episode:
    episode_id = _id(
        "episode", {**identity_seed, "case_id": case.case["case_id"], "slot": slot}
    )
    episode = _Episode(
        episode_id, _id("attempt", [episode_id, 1]), slot, case.case["case_id"]
    )
    opening = case.case["scenario"]["opening_user_turn"]["text"]
    episode.transcripts.append(
        _turn_record(
            base, episode, 1, "USER", opening, "CASE_OPENING", episode.attempt_id
        )
    )
    world = {
        "case_projection": {
            "case": case.case,
            "persona": case.persona,
            "intent": case.intent,
            "turn_policy": case.turn_policy,
        }
    }
    world_hash = _hash(_canonical(world))
    launch = TargetLaunch(
        episode_id,
        episode.case_id,
        config["target"],
        world,
        world_hash,
        source,
        environment,
    )
    session = None
    last_turn = 0
    started = clock.monotonic_ns()
    try:
        session = target_factory.start(launch)
        target = config["target"]
        hello: dict[str, Any] = {
            "kind": "hello",
            "protocol": target.get("protocol", "LABS05_TARGET_SESSION_V1"),
            "episode_id": episode_id,
            "case_id": episode.case_id,
            "connector_id": target["connector_id"],
            "connector_kind": target["connector_kind"],
            "connector_config_hash": identity_seed["connector_config_hash"],
            "target_identity": target["target_identity"],
        }
        if target["connector_kind"] == "EXECUTABLE_JSONL_V1":
            hello["source_commit"] = target["source_commit"]
        create_http = _validate_ready(session.exchange(hello), hello)
        episode.target_http += create_http
        if create_http:
            episode.ledger.append(
                _ledger(
                    base,
                    episode,
                    "TARGET",
                    0,
                    "SUCCEEDED",
                    _canonical(hello),
                    None,
                    create_http,
                    0,
                    0,
                    Decimal(0),
                    None,
                    None,
                )
            )
        for target_index in range(1, 4):
            if (clock.monotonic_ns() - started) > 180_000_000_000:
                episode.gaps.append("EPISODE_TIMEOUT")
                episode.termination = "EPISODE_TIMEOUT"
                break
            remaining = {
                "http_exchanges": 4,
                "input_tokens": 393216 - episode.target_input,
                "output_tokens": 24576 - episode.target_output,
                "tool_calls": 12 - episode.tool_count,
                "timeout_ms": 180000,
            }
            user = episode.transcripts[-1]
            request = {
                "kind": "turn",
                "episode_id": episode_id,
                "turn_index": target_index,
                "user_turn_id": user["record_id"],
                "content": user["content"],
                "transcript": [
                    {"role": item["role"], "content": item["content"]}
                    for item in episode.transcripts
                ],
                "remaining_budget": remaining,
            }
            reservation = Decimal("1.888888")
            episode.reserved += reservation
            try:
                response = session.exchange(request)
            except TimeoutError:
                episode.ledger.append(
                    _ledger(
                        base,
                        episode,
                        "TARGET",
                        target_index * 2,
                        "FAILED",
                        _canonical(request),
                        None,
                        0,
                        0,
                        0,
                        reservation,
                        None,
                        "TARGET_TIMEOUT",
                    )
                )
                episode.gaps.append("TARGET_TIMEOUT")
                episode.termination = "TARGET_TIMEOUT"
                break
            except (OSError, TargetProtocolFailure) as failure:
                reason = (
                    failure.reason_code
                    if isinstance(failure, TargetProtocolFailure)
                    else "TARGET_PROTOCOL_ERROR"
                )
                observed_http = (
                    failure.observed_http
                    if isinstance(failure, TargetProtocolFailure)
                    else 0
                )
                episode.target_http += observed_http
                episode.ledger.append(
                    _ledger(
                        base,
                        episode,
                        "TARGET",
                        target_index * 2,
                        "FAILED",
                        _canonical(request),
                        None,
                        observed_http,
                        0,
                        0,
                        reservation,
                        None,
                        reason,
                    )
                )
                episode.gaps.append(reason)
                episode.termination = reason
                break
            observed = _safe_usage(response)
            observed_tools = (
                len(response.get("tool_events", []))
                if isinstance(response, dict)
                and isinstance(response.get("tool_events"), list)
                else 0
            )
            try:
                if _has_secret(response, sentinels):
                    raise TargetProtocolFailure("TARGET_PROTOCOL_ERROR")
                events, usage, reported, telemetry_gaps = _validate_turn(
                    response, request, remaining, episode.tool_count
                )
            except (AdaptiveRunFailure, TargetProtocolFailure) as failure:
                reason = failure.reason_code
                episode.target_http += observed["provider_http_exchange_count"]
                episode.target_input += observed["input_tokens"]
                episode.target_output += observed["output_tokens"]
                episode.tool_count += observed_tools
                episode.ledger.append(
                    _ledger(
                        base,
                        episode,
                        "TARGET",
                        target_index * 2,
                        "OVER_BUDGET" if reason == "BUDGET_EXHAUSTED" else "FAILED",
                        _canonical(request),
                        None,
                        observed["provider_http_exchange_count"],
                        observed["input_tokens"],
                        observed["output_tokens"],
                        reservation,
                        None,
                        reason,
                    )
                )
                episode.gaps.append(reason)
                episode.termination = reason
                break
            status = response["status"]
            actual = usage["provider_reported_cost_usd"]
            episode.target_http += usage["provider_http_exchange_count"]
            episode.target_input += usage["input_tokens"]
            episode.target_output += usage["output_tokens"]
            episode.tool_count += len(events)
            episode.gaps.extend(
                gap for gap in telemetry_gaps if gap not in episode.gaps
            )
            if reported is not None:
                episode.reported_http += reported.get("http_exchanges", 0)
                episode.reported_model += reported.get("model_exchanges", 0)
                episode.reported_input += reported.get("input_tokens", 0)
                episode.reported_output += reported.get("output_tokens", 0)
                if reported.get("cost_usd") is not None:
                    episode.reported_cost = (
                        episode.reported_cost or Decimal(0)
                    ) + Decimal(reported["cost_usd"])
            assistant_ordinal = target_index * 2
            episode.ledger.append(
                _ledger(
                    base,
                    episode,
                    "TARGET",
                    target_index * 2,
                    status,
                    _canonical(request),
                    _canonical(response),
                    usage["provider_http_exchange_count"],
                    usage["input_tokens"],
                    usage["output_tokens"],
                    reservation,
                    actual,
                    response["reason_code"],
                )
            )
            for raw in events:
                episode.tools.append(
                    {
                        **base,
                        **raw,
                        "record_id": _id("target-tool-event", [episode_id, raw]),
                        "episode_id": episode_id,
                        "assistant_turn_ordinal": assistant_ordinal,
                        "connector_kind": target["connector_kind"],
                        "connector_id": target["connector_id"],
                        "connector_config_hash": identity_seed["connector_config_hash"],
                        "target_identity": target["target_identity"],
                    }
                )
            if actual is not None:
                try:
                    episode.actual = (episode.actual or Decimal(0)) + Decimal(actual)
                except InvalidOperation:
                    episode.gaps.append("TARGET_PROTOCOL_ERROR")
                    episode.termination = "TARGET_PROTOCOL_ERROR"
                    break
            if status != "SUCCEEDED":
                reason = _target_reason(status)
                episode.gaps.append(reason)
                episode.termination = reason
                break
            assistant = _turn_record(
                base,
                episode,
                assistant_ordinal,
                "ASSISTANT",
                response["assistant_content"],
                "TARGET",
                episode.ledger[-1]["attempt_id"],
            )
            episode.transcripts.append(assistant)
            last_turn = target_index
            if clock.monotonic_ns() - started > 180_000_000_000:
                episode.gaps.append("EPISODE_TIMEOUT")
                episode.termination = "EPISODE_TIMEOUT"
                break
            if target_index == 3:
                episode.valid, episode.termination = True, "TURN_LIMIT_REACHED"
                break
            observation = _observation(assistant, events)
            simulator_request = {
                "protocol_version": WIRE,
                "episode_id": episode_id,
                "case": case.case,
                "turn_index": target_index + 1,
                "transcript": episode.transcripts,
                "latest_observation": observation,
                "remaining_turns": 2 - target_index,
            }
            sim_reservation = Decimal("1.000000")
            episode.reserved += sim_reservation
            try:
                sim = simulator.complete(simulator_request)
            except (OSError, TimeoutError):
                episode.ledger.append(
                    _ledger(
                        base,
                        episode,
                        "SIMULATOR",
                        assistant_ordinal + 1,
                        "FAILED",
                        _canonical(simulator_request),
                        None,
                        0,
                        0,
                        0,
                        sim_reservation,
                        None,
                        "SIMULATOR_PROVIDER_ERROR",
                    )
                )
                episode.gaps.append("SIMULATOR_PROVIDER_ERROR")
                episode.termination = "SIMULATOR_PROVIDER_ERROR"
                break
            if not isinstance(sim, SimulatorResponse):
                episode.gaps.append("SIMULATOR_INVALID_RESPONSE")
                episode.termination = "SIMULATOR_INVALID_RESPONSE"
                break
            sim_http = (
                sim.provider_http_exchange_count
                if _integer(sim.provider_http_exchange_count)
                else 0
            )
            sim_input = sim.input_tokens if _integer(sim.input_tokens) else 0
            sim_output = sim.output_tokens if _integer(sim.output_tokens) else 0
            invalid = (
                sim.status not in {"SUCCEEDED", "FAILED"}
                or not _money(sim.provider_reported_cost_usd)
                or type(sim.proposed_stop) is not bool
                or (
                    sim.status == "SUCCEEDED"
                    and (
                        not _text(sim.next_user_content, nonempty=True)
                        or not isinstance(sim.consumed_observation_hash, str)
                        or _DIGEST.fullmatch(sim.consumed_observation_hash) is None
                        or sim.reason_code is not None
                    )
                )
                or (sim.proposed_stop and not _text(sim.stop_reason, nonempty=True))
                or (not sim.proposed_stop and sim.stop_reason is not None)
                or sim.status == "FAILED"
                and sim.reason_code != "SIMULATOR_PROVIDER_ERROR"
                or not all(
                    _integer(item)
                    for item in (
                        sim.input_tokens,
                        sim.output_tokens,
                        sim.provider_http_exchange_count,
                    )
                )
            )
            unsafe = _has_secret(sim.response_bytes or b"", sentinels) or _has_secret(
                {
                    "next_user_content": sim.next_user_content,
                    "consumed_observation_hash": sim.consumed_observation_hash,
                    "stop_reason": sim.stop_reason,
                },
                sentinels,
            )
            over_budget = sim_input > 131072 or sim_output > 4096 or sim_http > 1
            sim_reason: str | None = (
                "SIMULATOR_INVALID_RESPONSE"
                if invalid or unsafe
                else "BUDGET_EXHAUSTED"
                if over_budget
                else sim.reason_code
            )
            episode.sim_http += sim_http
            episode.sim_input += sim_input
            episode.sim_output += sim_output
            episode.ledger.append(
                _ledger(
                    base,
                    episode,
                    "SIMULATOR",
                    assistant_ordinal + 1,
                    "FAILED" if sim_reason else sim.status,
                    sim.request_bytes,
                    None if sim_reason else sim.response_bytes,
                    sim_http,
                    sim_input,
                    sim_output,
                    sim_reservation,
                    None if sim_reason else sim.provider_reported_cost_usd,
                    sim_reason,
                )
            )
            if sim_reason:
                episode.gaps.append(sim_reason)
                episode.termination = sim_reason
                break
            if (
                sim.status != "SUCCEEDED"
                or not isinstance(sim.next_user_content, str)
                or not sim.next_user_content
            ):
                reason = sim.reason_code or "SIMULATOR_INVALID_RESPONSE"
                episode.gaps.append(reason)
                episode.termination = reason
                break
            if sim.consumed_observation_hash != observation["observation_hash"]:
                episode.gaps.append("ADAPTATION_BINDING_MISMATCH")
                episode.termination = "ADAPTATION_BINDING_MISMATCH"
                break
            episode.transcripts.append(
                _turn_record(
                    base,
                    episode,
                    assistant_ordinal + 1,
                    "USER",
                    sim.next_user_content,
                    "SIMULATOR",
                    episode.ledger[-1]["attempt_id"],
                    consumed_observation_hash=sim.consumed_observation_hash,
                    latest_observation_hash=observation["observation_hash"],
                )
            )
    except KeyboardInterrupt:
        raise
    except TimeoutError:
        episode.gaps.append("TARGET_TIMEOUT")
        episode.termination = "TARGET_TIMEOUT"
    except OSError:
        episode.gaps.append("TARGET_PROTOCOL_ERROR")
        episode.termination = "TARGET_PROTOCOL_ERROR"
    except TargetProtocolFailure as failure:
        episode.gaps.append(failure.reason_code)
        episode.termination = failure.reason_code
        episode.target_http += failure.observed_http
        if failure.observed_http:
            episode.ledger.append(
                _ledger(
                    base,
                    episode,
                    "TARGET",
                    0,
                    "FAILED",
                    None,
                    None,
                    failure.observed_http,
                    0,
                    0,
                    Decimal(0),
                    None,
                    failure.reason_code,
                )
            )
    finally:
        if session is not None:
            try:
                closed = session.exchange(
                    {
                        "kind": "close",
                        "episode_id": episode_id,
                        "last_turn_index": last_turn,
                    }
                )
                base_closed = {"kind", "episode_id", "last_turn_index", "memory_state"}
                counted = base_closed | {
                    "provider_http_exchange_count",
                    "tool_call_count",
                }
                close_http = closed.get("close_http_exchange_count", 0)
                if "close_http_exchange_count" in closed:
                    counted.add("close_http_exchange_count")
                episode.target_http += close_http if _integer(close_http) else 0
                if close_http:
                    episode.ledger.append(
                        _ledger(
                            base,
                            episode,
                            "TARGET",
                            last_turn * 2 + 1,
                            "SUCCEEDED",
                            None,
                            _canonical(closed),
                            close_http,
                            0,
                            0,
                            Decimal(0),
                            None,
                            None,
                        )
                    )
                if not (
                    isinstance(closed, dict)
                    and set(closed) in {frozenset(base_closed), frozenset(counted)}
                    and closed.get("kind") == "closed"
                    and closed.get("episode_id") == episode_id
                    and closed.get("last_turn_index") == last_turn
                    and _integer(closed.get("last_turn_index"))
                    and closed.get("memory_state") == "DISCARDED"
                    and _integer(close_http)
                    and close_http <= 1
                    and (
                        set(closed) == base_closed
                        or _integer(closed.get("provider_http_exchange_count"))
                        and _integer(closed.get("tool_call_count"))
                        and closed.get("provider_http_exchange_count")
                        == episode.target_http
                        and closed.get("tool_call_count") == episode.tool_count
                    )
                ):
                    if "TARGET_PROTOCOL_ERROR" not in episode.gaps:
                        episode.gaps.append("TARGET_PROTOCOL_ERROR")
                    episode.valid, episode.termination = False, "TARGET_PROTOCOL_ERROR"
            except (
                OSError,
                TimeoutError,
                TargetProtocolFailure,
                KeyError,
                TypeError,
            ) as failure:
                reason = (
                    failure.reason_code
                    if isinstance(failure, TargetProtocolFailure)
                    else "TARGET_PROTOCOL_ERROR"
                )
                observed_http = (
                    failure.observed_http
                    if isinstance(failure, TargetProtocolFailure)
                    else 0
                )
                episode.target_http += observed_http
                if observed_http:
                    episode.ledger.append(
                        _ledger(
                            base,
                            episode,
                            "TARGET",
                            last_turn * 2 + 1,
                            "FAILED",
                            None,
                            None,
                            observed_http,
                            0,
                            0,
                            Decimal(0),
                            None,
                            reason,
                        )
                    )
                if reason not in episode.gaps:
                    episode.gaps.append(reason)
                episode.termination, episode.valid = reason, False
            finally:
                session.terminate()
    if episode.valid:
        ordered = [(item["role"], item["content"]) for item in episode.transcripts]
        tools = [
            (item["name"], item["status"], item["arguments"], item["result"])
            for item in episode.tools
        ]
        episode.fingerprint = _hash(
            _canonical(
                {"turns": ordered, "tools": tools, "termination": episode.termination}
            )
        )
    return episode


def _tokens(episode: _Episode) -> set[str]:
    return set(
        " ".join(str(item["content"]) for item in episode.transcripts)
        .casefold()
        .split()
    )


def _cluster(episodes: list[_Episode]) -> dict[str, Any]:
    valid = [episode for episode in episodes if episode.valid]
    parent = {episode.episode_id: episode.episode_id for episode in valid}
    exact: list[list[str]] = []
    near: list[list[str]] = []

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for index, left in enumerate(valid):
        for right in valid[index + 1 :]:
            edge = None
            if left.fingerprint == right.fingerprint:
                exact.append([left.episode_id, right.episode_id])
                edge = exact
            else:
                left_tools = [(x["name"], x["status"]) for x in left.tools]
                right_tools = [(x["name"], x["status"]) for x in right.tools]
                a, b = _tokens(left), _tokens(right)
                score = len(a & b) / len(a | b) if a | b else 1.0
                if left_tools == right_tools and score >= 0.85:
                    near.append([left.episode_id, right.episode_id])
                    edge = near
            if edge is not None:
                union(left.episode_id, right.episode_id)
    components_map: dict[str, list[str]] = {}
    for episode in valid:
        components_map.setdefault(find(episode.episode_id), []).append(
            episode.episode_id
        )
    components = list(components_map.values())
    effective_ids: list[str] = []
    for component in components:
        winner = min(
            (episode for episode in valid if episode.episode_id in component),
            key=lambda item: item.slot,
        )
        winner.effective = True
        effective_ids.append(winner.episode_id)
        for episode in valid:
            if episode.episode_id in component and episode is not winner:
                episode.gaps.append("DUPLICATE_TRAJECTORY")
    return {
        "artifact_kind": "trajectory_clusters",
        "schema_version": 1,
        "protocol_version": WIRE,
        "exact_algorithm": "LABS05_TRAJECTORY_EXACT_V1",
        "near_algorithm": "LABS05_TRAJECTORY_JACCARD_TOOLS_V1",
        "threshold": "0.85",
        "raw_n": len(episodes),
        "valid_n": len(valid),
        "effective_n": len(effective_ids),
        "exact_edges": exact,
        "near_edges": near,
        "components": components,
        "effective_episode_ids": effective_ids,
    }


def _artifacts(
    episodes: list[_Episode],
    cluster: dict[str, Any],
    base: dict[str, Any],
    output: Path,
    outcome: str,
    reason: str | None,
) -> tuple[dict[str, bytes], AdaptiveRunResult]:
    effective = [item for item in episodes if item.effective]
    gaps: list[dict[str, Any]] = []
    for episode in episodes:
        for code in episode.gaps:
            gaps.append(
                {
                    **base,
                    "record_id": _id("gap", [episode.episode_id, code]),
                    "episode_id": episode.episode_id,
                    "turn_ordinal": len(episode.transcripts),
                    "reason_code": code,
                    "detail_code": None,
                    "originating_attempt_id": episode.attempt_id,
                }
            )
    if len(effective) < 3:
        gaps.append(
            {
                **base,
                "record_id": _id("gap", ["run", "INSUFFICIENT_DISTINCT_TRAJECTORIES"]),
                "episode_id": None,
                "turn_ordinal": None,
                "reason_code": "INSUFFICIENT_DISTINCT_TRAJECTORIES",
                "detail_code": None,
                "originating_attempt_id": None,
            }
        )
    attempts = [
        {
            **base,
            "record_id": _id("episode-attempt", episode.attempt_id),
            "episode_id": episode.episode_id,
            "attempt_id": episode.attempt_id,
            "slot": episode.slot,
            "case_id": episode.case_id,
            "status": "VALID" if episode.valid else "PARTIAL",
            "termination_reason": episode.termination,
            "completed_role_turn_count": len(episode.transcripts),
            "simulator_http_exchange_count": episode.sim_http,
            "target_http_exchange_count": episode.target_http,
            "simulator_input_tokens": episode.sim_input,
            "simulator_output_tokens": episode.sim_output,
            "target_input_tokens": episode.target_input,
            "target_output_tokens": episode.target_output,
            "target_tool_call_count": episode.tool_count,
            "target_reported_internal_http_exchange_count": episode.reported_http,
            "target_reported_internal_model_exchange_count": episode.reported_model,
            "target_reported_internal_input_tokens": episode.reported_input,
            "target_reported_internal_output_tokens": episode.reported_output,
            "target_reported_internal_cost_usd": f"{episode.reported_cost:.6f}"
            if episode.reported_cost is not None
            else None,
            "reserved_cost_usd": f"{episode.reserved:.6f}",
            "actual_cost_usd": f"{episode.actual:.6f}"
            if episode.actual is not None
            else None,
            "trajectory_fingerprint": episode.fingerprint,
            "effective": episode.effective,
            "gap_codes": sorted(set(episode.gaps)),
        }
        for episode in episodes
    ]
    review_items = []
    for episode in effective:
        for ordinal in (3, 5):
            user = next(
                item for item in episode.transcripts if item["ordinal"] == ordinal
            )
            prior = next(
                item for item in episode.transcripts if item["ordinal"] == ordinal - 1
            )
            review_items.append(
                {
                    "episode_id": episode.episode_id,
                    "case_id": episode.case_id,
                    "user_turn_id": user["record_id"],
                    "user_turn_ordinal": ordinal,
                    "prior_target_observation": prior["content"],
                    "generated_user_turn": user["content"],
                    "materially_reacts": None,
                    "notes": None,
                }
            )
    human = {
        "artifact_kind": "labs05_adaptation_review",
        "schema_version": 1,
        "protocol_version": WIRE,
        "rubric_version": "LABS05_ADAPTATION_V1",
        "manifest_hash": base["case_factory_manifest_hash"],
        "review_state": "PENDING",
        "review_items": review_items,
    }
    payloads: dict[str, bytes] = {
        "episode_attempts.jsonl": b"".join(
            _canonical(item, lf=True) for item in attempts
        ),
        "transcripts.jsonl": b"".join(
            _canonical(item, lf=True)
            for episode in episodes
            for item in episode.transcripts
        ),
        "target_tool_events.jsonl": b"".join(
            _canonical(item, lf=True) for episode in episodes for item in episode.tools
        ),
        "provider_ledger.jsonl": b"".join(
            _canonical(item, lf=True) for episode in episodes for item in episode.ledger
        ),
        "gaps.jsonl": b"".join(_canonical(item, lf=True) for item in gaps),
        "trajectory_clusters.json": _canonical({**base, **cluster}, lf=True),
        "human_adaptation_review.json": _canonical(human, lf=True),
    }
    sim_http = sum(item.sim_http for item in episodes)
    target_http = sum(item.target_http for item in episodes)
    reserved = sum((item.reserved for item in episodes), Decimal(0))
    actuals = [item.actual for item in episodes if item.actual is not None]
    manifest = {
        **base,
        "artifact_kind": "adaptive_run_manifest",
        "outcome": outcome,
        "reason_code": reason,
        "privacy_class": "SYNTHETIC",
        "producing_component": "triana-labs-adaptive-runner",
        "producing_version": "1",
        "selected_episode_count": 3,
        "attempted_episode_count": len(episodes),
        "valid_episode_count": sum(item.valid for item in episodes),
        "effective_trajectory_count": len(effective),
        "duplicate_count": sum(
            "DUPLICATE_TRAJECTORY" in item.gaps for item in episodes
        ),
        "gap_count": len(gaps),
        "simulator_http_exchange_count": sim_http,
        "target_http_exchange_count": target_http,
        "all_http_exchange_count": sim_http + target_http,
        "simulator_input_tokens": sum(item.sim_input for item in episodes),
        "simulator_output_tokens": sum(item.sim_output for item in episodes),
        "target_input_tokens": sum(item.target_input for item in episodes),
        "target_output_tokens": sum(item.target_output for item in episodes),
        "target_tool_call_count": sum(item.tool_count for item in episodes),
        "target_reported_internal_http_exchange_count": sum(
            item.reported_http for item in episodes
        ),
        "target_reported_internal_model_exchange_count": sum(
            item.reported_model for item in episodes
        ),
        "target_reported_internal_input_tokens": sum(
            item.reported_input for item in episodes
        ),
        "target_reported_internal_output_tokens": sum(
            item.reported_output for item in episodes
        ),
        "target_reported_internal_cost_usd": (
            f"{sum((item.reported_cost or Decimal(0) for item in episodes), Decimal(0)):.6f}"
            if any(item.reported_cost is not None for item in episodes)
            else None
        ),
        "reserved_cost_usd": f"{reserved:.6f}",
        "actual_cost_usd": f"{sum(actuals, Decimal(0)):.6f}" if actuals else None,
        "human_review_state": "PENDING",
        "artifacts": {name: _hash(data) for name, data in payloads.items()},
    }
    payloads["manifest.json"] = _canonical(manifest, lf=True)
    exit_code = (
        0 if outcome == "COMPLETED" else (130 if reason == "INTERRUPTED" else 10)
    )
    result = AdaptiveRunResult(
        outcome,
        reason,
        exit_code,
        output / "manifest.json",
        len(episodes),
        sum(item.valid for item in episodes),
        len(effective),
        sim_http,
        target_http,
        sim_http + target_http,
        f"{reserved:.6f}",
        manifest["actual_cost_usd"],
    )
    return payloads, result


def run(
    case_factory_manifest: Path,
    owner_review: Path,
    config_path: Path,
    output_path: Path,
    *,
    simulator: SimulatorTransport,
    target_factory: TargetProcessFactory,
    clock: Clock,
    environ: Mapping[str, str],
    publisher: ArtifactPublisher | None = None,
    source_verifier: TargetSourceVerifier | None = None,
    case_loader: CaseFactoryInputLoader | None = None,
) -> AdaptiveRunResult:
    """Execute the exact three-slot LABS-05 controller and publish safe custody."""
    if os.path.lexists(output_path):
        raise AdaptiveRunFailure("OUTPUT_ALREADY_EXISTS", 2)
    if not output_path.parent.is_dir() or output_path.parent.is_symlink():
        raise AdaptiveRunFailure("OUTPUT_PARENT_MISSING", 2)
    review, review_bytes = _read_object(owner_review, "REVIEW_INVALID", 4)
    config, config_bytes = _read_object(config_path, "CONFIG_INVALID", 2)
    _validate_review(review)
    _validate_config(config, environ)
    if case_loader is None:
        from .boundaries import CaseFactoryLoader

        case_loader = CaseFactoryLoader()
    try:
        source_input = case_loader.load(case_factory_manifest)
    except AdaptiveRunFailure:
        raise
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise AdaptiveRunFailure("MANIFEST_INVALID", 4) from error
    _validate_cases(source_input)
    if not environ.get(config["simulator"]["api_key_env"]):
        raise AdaptiveRunFailure("SIMULATOR_AUTHORIZATION_REFUSED", 4)
    review_hash, config_hash = _hash(review_bytes), _hash(config_bytes)
    base = _lineage(source_input.manifest_file_hash, review_hash, config_hash)
    target = config["target"]
    connector_hash = _hash(_canonical(target))
    if target["connector_kind"] == "EXECUTABLE_JSONL_V1":
        if any(not environ.get(name) for name in target["env_names"]):
            raise AdaptiveRunFailure("TARGET_SOURCE_MISMATCH", 4)
        if source_verifier is None:
            from .boundaries import GitTargetSourceVerifier

            source_verifier = GitTargetSourceVerifier()
        source_identity = source_verifier.verify(target)
        if source_identity.source_commit != target["source_commit"]:
            raise AdaptiveRunFailure("TARGET_SOURCE_MISMATCH", 4)
        environment = {name: environ[name] for name in target["env_names"]}
    else:
        source_identity = TargetSourceIdentity(
            "HTTP_JSON_V1", connector_hash, connector_hash
        )
        names = [name for name in ("AWS_PROFILE", "AWS_REGION") if environ.get(name)]
        if target["auth"]["kind"] == "HEADER_ENV":
            names.append(target["auth"]["env_name"])
        environment = {name: environ[name] for name in names}
    sentinels = tuple(
        value.encode("utf-8")
        for value in (
            environ[config["simulator"]["api_key_env"]],
            *environment.values(),
        )
        if value
    )
    identity_seed = {
        "case_factory_manifest_hash": source_input.manifest_file_hash,
        "case_candidate_file_hash": source_input.case_candidate_file_hash,
        "input_manifest_hash": source_input.input_manifest_hash,
        "intelligence_manifest_hash": source_input.intelligence_manifest_hash,
        "owner_review_hash": review_hash,
        "config_hash": config_hash,
        "connector_config_hash": connector_hash,
        "connector_kind": target["connector_kind"],
        "target_identity": target["target_identity"],
        "state_isolation": target["state_isolation"],
        "target_source_tree_hash": source_identity.source_tree_hash,
        "target_adapter_file_hash": source_identity.adapter_file_hash,
    }
    episodes: list[_Episode] = []
    interrupted = False
    run_started = clock.monotonic_ns()
    for slot, case in enumerate(source_input.cases, start=1):
        if (clock.monotonic_ns() - run_started) > 600_000_000_000:
            for timeout_slot, pending in enumerate(
                source_input.cases[slot - 1 :], start=slot
            ):
                episode_id = _id(
                    "episode",
                    {
                        **identity_seed,
                        "case_id": pending.case["case_id"],
                        "slot": timeout_slot,
                    },
                )
                partial = _Episode(
                    episode_id,
                    _id("attempt", [episode_id, 1]),
                    timeout_slot,
                    pending.case["case_id"],
                )
                partial.gaps.append("RUN_TIMEOUT")
                partial.termination = "RUN_TIMEOUT"
                episodes.append(partial)
            break
        try:
            episodes.append(
                _run_episode(
                    case,
                    slot,
                    config,
                    source_identity,
                    simulator,
                    target_factory,
                    clock,
                    environment,
                    base,
                    identity_seed,
                    sentinels,
                )
            )
        except KeyboardInterrupt:
            interrupted = True
            # Preserve the opening of the interrupted slot through a deterministic shell episode.
            episode_id = _id(
                "episode",
                {**identity_seed, "case_id": case.case["case_id"], "slot": slot},
            )
            partial = _Episode(
                episode_id, _id("attempt", [episode_id, 1]), slot, case.case["case_id"]
            )
            partial.transcripts.append(
                _turn_record(
                    base,
                    partial,
                    1,
                    "USER",
                    case.case["scenario"]["opening_user_turn"]["text"],
                    "CASE_OPENING",
                    partial.attempt_id,
                )
            )
            partial.gaps.append("INTERRUPTED")
            partial.termination = "INTERRUPTED"
            episodes.append(partial)
            break
    cluster = _cluster(episodes)
    outcome = (
        "COMPLETED"
        if len(episodes) == 3
        and cluster["effective_n"] == 3
        and not any(item.gaps for item in episodes)
        else "COMPLETED_WITH_GAPS"
    )
    reason = "INTERRUPTED" if interrupted else None
    payloads, result = _artifacts(episodes, cluster, base, output_path, outcome, reason)
    try:
        (publisher or AtomicPublisher()).publish(output_path, payloads)
    except PublicationFailure as failure:
        raise AdaptiveRunFailure(
            "OUTPUT_CLEANUP_FAILED"
            if failure.cleanup_failed
            else "OUTPUT_WRITE_FAILED",
            7,
        ) from failure
    except OSError as error:
        raise AdaptiveRunFailure("OUTPUT_WRITE_FAILED", 7) from error
    return result
