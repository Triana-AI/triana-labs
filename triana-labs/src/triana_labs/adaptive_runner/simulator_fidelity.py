"""Deterministic LABS-06 context, semantics, and teacher-forced evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from .contracts import (
    AdaptiveRunFailure,
    JsonObject,
    SimulatorContextBundle,
    SimulatorContextLoader,
    SimulatorResponse,
    SimulatorTransport,
    VerifiedCaseProjection,
)

PROTOCOL = "LABS06_SIMULATOR_FIDELITY_V1"
ECHO_ALGORITHM = "LABS06_ASSISTANT_ECHO_V1"
RUBRIC = "REGULAR_USER_SIMULATION_FIDELITY_V1"
SEMANTIC_CODES = frozenset(
    {
        "ROLE_INVERSION",
        "EXACT_ASSISTANT_ECHO",
        "NEAR_ASSISTANT_ECHO",
        "HIDDEN_FACT_LEAK",
        "FIXED_FACT_CONFLICT",
        "UNAUTHORIZED_REACTION",
        "UNAUTHORIZED_ACTION",
        "STOP_NOT_ALLOWED",
    }
)
CRITICAL_CODES = (
    "EXACT_ASSISTANT_ECHO",
    "FIXED_FACT_CONFLICT",
    "HIDDEN_FACT_LEAK",
    "NEAR_ASSISTANT_ECHO",
    "ROLE_INVERSION",
    "UNAUTHORIZED_ACTION",
)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_LEVELS = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
_GOALS = {"OPEN", "SATISFIED", "ABANDONED", "UNKNOWN"}
_STRATA = Counter(
    {
        "ORDINARY": 24,
        "ANGRY": 1,
        "IMPATIENT": 1,
        "SKEPTICAL": 1,
        "INFORMAL": 1,
        "MISTAKEN": 1,
        "ADVERSARIAL": 1,
    }
)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return payload + (b"\n" if lf else b"")


def _hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _identity(prefix: str, value: Any) -> str:
    return f"{prefix}-{hashlib.sha256(_canonical(value)).hexdigest()[:16]}"


def _closed(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _text(value: Any, *, nonempty: bool = True) -> bool:
    return (
        isinstance(value, str)
        and (bool(value) or not nonempty)
        and len(value.encode("utf-8")) <= 16_384
        and all(ord(char) >= 32 or char == "\n" for char in value)
        and not any(127 <= ord(char) <= 159 for char in value)
    )


def _ids(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and len(value) == len(set(value))
        and all(isinstance(item, str) and _SAFE_ID.fullmatch(item) for item in value)
    )


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join("".join(char if char.isalnum() else " " for char in value).split())


def _match(utterance: str, matchers: Any) -> bool:
    normalized = _normalize(utterance)
    return any(_normalize(item) in normalized for item in matchers)


def _contains_literal(value: Any, literal: str) -> bool:
    if isinstance(value, str):
        return _normalize(literal) in _normalize(value)
    if isinstance(value, dict):
        return any(
            _contains_literal(key, literal) or _contains_literal(item, literal)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_literal(item, literal) for item in value)
    return False


def _valid_matchers(value: Any, *, required: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not required)
        and len(value) == len(set(value))
        and all(_text(item) and _normalize(item) == item for item in value)
    )


def _valid_state(value: Any) -> bool:
    return (
        _closed(
            value,
            {
                "patience_level",
                "trust_level",
                "urgency_level",
                "confusion_level",
                "goal_state",
                "remaining_disclosure_ids",
            },
        )
        and value["patience_level"] in _LEVELS
        and value["trust_level"] in _LEVELS
        and value["urgency_level"] in _LEVELS
        and value["confusion_level"] in _LEVELS
        and value["goal_state"] in _GOALS
        and _ids(value["remaining_disclosure_ids"])
    )


def _validate_context(context: Any) -> None:
    keys = {
        "context_id",
        "context_version",
        "source",
        "persona",
        "intent",
        "known_facts",
        "hidden_facts",
        "user_turn_policy",
        "initial_interaction_state",
        "reaction_registry",
        "action_registry",
        "stop_registry",
        "assistant_only_literal_matchers",
        "fixed_fact_conflict_literal_matchers",
    }
    if not _closed(context, keys) or context["context_version"] != 1:
        raise ValueError("context shape")
    source_keys = {
        "case_id",
        "case_hash",
        "persona_id",
        "persona_hash",
        "intent_id",
        "intent_hash",
        "turn_policy_id",
        "turn_policy_hash",
    }
    source = context["source"]
    if (
        not _closed(source, source_keys)
        or not all(
            _text(source[key]) for key in source_keys if not key.endswith("hash")
        )
        or not all(
            _DIGEST.fullmatch(source[key])
            for key in source_keys
            if key.endswith("hash")
        )
        or not isinstance(context["persona"], dict)
        or not isinstance(context["intent"], dict)
        or not isinstance(context["known_facts"], list)
        or not _valid_state(context["initial_interaction_state"])
        or not _valid_matchers(
            context["assistant_only_literal_matchers"], required=True
        )
        or not _valid_matchers(
            context["fixed_fact_conflict_literal_matchers"], required=True
        )
    ):
        raise ValueError("context authority")
    policy = context["user_turn_policy"]
    if (
        not _closed(
            policy, {"policy_id", "owner", "allowed_reaction_ids", "allowed_action_ids"}
        )
        or policy["owner"] != "USER"
        or not _text(policy["policy_id"])
        or not _ids(policy["allowed_reaction_ids"], nonempty=True)
        or not _ids(policy["allowed_action_ids"])
    ):
        raise ValueError("user policy")
    hidden_ids: list[str] = []
    for fact in (
        context["hidden_facts"] if isinstance(context["hidden_facts"], list) else ()
    ):
        if (
            not _closed(fact, {"fact_id", "literal_matchers", "value", "visibility"})
            or fact["visibility"] != "HIDDEN"
            or not _text(fact["fact_id"])
            or not _text(fact["value"])
            or not _valid_matchers(fact["literal_matchers"], required=True)
        ):
            raise ValueError("hidden fact")
        hidden_ids.append(fact["fact_id"])
    if len(hidden_ids) != len(set(hidden_ids)):
        raise ValueError("hidden identity")
    provider_projection = {
        "persona": context["persona"],
        "intent": context["intent"],
        "known_facts": context["known_facts"],
        "user_turn_policy": context["user_turn_policy"],
    }
    hidden_literals = [
        literal
        for fact in context["hidden_facts"]
        for literal in [fact["value"], *fact["literal_matchers"]]
    ]
    if any(
        _contains_literal(provider_projection, literal) for literal in hidden_literals
    ):
        raise ValueError("hidden fact egress")
    actions: dict[str, Any] = {}
    for action in (
        context["action_registry"]
        if isinstance(context["action_registry"], list)
        else ()
    ):
        if (
            not _closed(action, {"action_id", "literal_matchers"})
            or not _text(action["action_id"])
            or not _valid_matchers(action["literal_matchers"], required=True)
            or action["action_id"] in actions
        ):
            raise ValueError("action registry")
        actions[action["action_id"]] = action
    reactions: dict[str, Any] = {}
    for reaction in (
        context["reaction_registry"]
        if isinstance(context["reaction_registry"], list)
        else ()
    ):
        if (
            not _closed(
                reaction,
                {
                    "reaction_id",
                    "allowed_action_ids",
                    "stop_reason_codes",
                    "state_transition",
                },
            )
            or not _text(reaction["reaction_id"])
            or not _ids(reaction["allowed_action_ids"])
            or not _ids(reaction["stop_reason_codes"])
            or not _valid_state(reaction["state_transition"])
            or reaction["reaction_id"] in reactions
            or not set(reaction["allowed_action_ids"]) <= set(actions)
        ):
            raise ValueError("reaction registry")
        reactions[reaction["reaction_id"]] = reaction
    if not set(policy["allowed_reaction_ids"]) <= set(reactions) or not set(
        policy["allowed_action_ids"]
    ) <= set(actions):
        raise ValueError("policy registry")
    stops: set[tuple[str, str]] = set()
    for stop in (
        context["stop_registry"] if isinstance(context["stop_registry"], list) else ()
    ):
        if (
            not _closed(stop, {"reaction_id", "stop_reason_code"})
            or stop["reaction_id"] not in reactions
            or not _text(stop["stop_reason_code"])
        ):
            raise ValueError("stop registry")
        stops.add((stop["reaction_id"], stop["stop_reason_code"]))
    if len(stops) != len(context["stop_registry"]):
        raise ValueError("stop identity")


def _validate_item(item: Any, contexts: Mapping[str, JsonObject]) -> None:
    keys = {
        "item_id",
        "stratum",
        "context_id",
        "turn_index",
        "transcript",
        "latest_observation",
        "interaction_state",
        "allowed_reaction_ids",
        "allowed_action_ids",
        "allowed_stop_reason_codes",
        "remaining_turns",
    }
    if (
        not _closed(item, keys)
        or item["context_id"] not in contexts
        or type(item["turn_index"]) is not int
        or item["turn_index"] < 1
        or type(item["remaining_turns"]) is not int
        or item["remaining_turns"] < 0
        or not _valid_state(item["interaction_state"])
        or not _ids(item["allowed_reaction_ids"], nonempty=True)
        or not _ids(item["allowed_action_ids"])
        or not _ids(item["allowed_stop_reason_codes"])
        or not isinstance(item["transcript"], list)
    ):
        raise ValueError("panel item")
    for turn in item["transcript"]:
        if (
            not _closed(turn, {"role", "content"})
            or turn["role"] not in {"USER", "ASSISTANT"}
            or not _text(turn["content"])
        ):
            raise ValueError("panel transcript")
    observation = item["latest_observation"]
    if (
        not _closed(
            observation,
            {
                "assistant_turn_id",
                "assistant_content",
                "tool_events",
                "observation_hash",
            },
        )
        or not _text(observation["assistant_turn_id"])
        or not _text(observation["assistant_content"])
        or not isinstance(observation["tool_events"], list)
        or observation["observation_hash"]
        != _hash(
            _canonical(
                {
                    key: observation[key]
                    for key in ("assistant_content", "assistant_turn_id", "tool_events")
                }
            )
        )
    ):
        raise ValueError("panel observation")


def validate_bundle(bundle: SimulatorContextBundle) -> None:
    if (
        not _DIGEST.fullmatch(bundle.bundle_hash)
        or len(bundle.contexts) != 3
        or len(bundle.teacher_forced_items) != 30
    ):
        raise ValueError("bundle bounds")
    contexts: dict[str, JsonObject] = {}
    for context in bundle.contexts:
        _validate_context(context)
        context_id = context["context_id"]
        if not isinstance(context_id, str) or context_id in contexts:
            raise ValueError("context identity")
        contexts[context_id] = context
    for item in bundle.teacher_forced_items:
        _validate_item(item, contexts)
    if (
        len({item["item_id"] for item in bundle.teacher_forced_items}) != 30
        or Counter(item["stratum"] for item in bundle.teacher_forced_items) != _STRATA
    ):
        raise ValueError("panel denominator")


class FileSimulatorContextLoader:
    """Strict canonical local bundle loader; no alternate source or fallback."""

    def load(self, path: Path) -> SimulatorContextBundle:
        try:
            if path.is_symlink():
                raise OSError
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(descriptor, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise OSError
                payload = stream.read(1_048_577)
            if (
                len(payload) > 1_048_576
                or not payload.endswith(b"\n")
                or payload.endswith(b"\n\n")
            ):
                raise ValueError
            value = json.loads(payload, object_pairs_hook=_pairs)
            top = {
                "artifact_kind",
                "schema_version",
                "protocol_version",
                "source_case_set_hash",
                "source_policy_selection_hash",
                "panel_identity_hash",
                "contexts",
                "teacher_forced_items",
                "bundle_hash",
            }
            if not _closed(value, top) or _canonical(value, lf=True) != payload:
                raise ValueError
            body = {key: item for key, item in value.items() if key != "bundle_hash"}
            if (
                value["artifact_kind"] != "labs06_simulator_context_bundle"
                or value["schema_version"] != 1
                or value["protocol_version"] != PROTOCOL
                or value["bundle_hash"] != _hash(_canonical(body))
                or value["panel_identity_hash"]
                != _hash(
                    _canonical(
                        [item["item_id"] for item in value["teacher_forced_items"]]
                    )
                )
                or not _DIGEST.fullmatch(value["source_case_set_hash"])
                or not _DIGEST.fullmatch(value["source_policy_selection_hash"])
            ):
                raise ValueError
            for context in value["contexts"]:
                if context.get("context_id") != _identity(
                    "sim-context",
                    {key: item for key, item in context.items() if key != "context_id"},
                ):
                    raise ValueError
            for item in value["teacher_forced_items"]:
                if item.get("item_id") != _identity(
                    "fidelity-item",
                    {key: part for key, part in item.items() if key != "item_id"},
                ):
                    raise ValueError
            bundle = SimulatorContextBundle(
                value["bundle_hash"],
                tuple(value["contexts"]),
                tuple(value["teacher_forced_items"]),
            )
            validate_bundle(bundle)
            return bundle
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise AdaptiveRunFailure("SIMULATOR_CONTEXT_INVALID", 4) from error


def load_bundle(
    path: Path, loader: SimulatorContextLoader | None
) -> SimulatorContextBundle:
    try:
        bundle = (loader or FileSimulatorContextLoader()).load(path)
        if not isinstance(bundle, SimulatorContextBundle):
            raise TypeError
        validate_bundle(bundle)
        return bundle
    except AdaptiveRunFailure:
        raise
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise AdaptiveRunFailure("SIMULATOR_CONTEXT_INVALID", 4) from error


def bind_contexts(
    bundle: SimulatorContextBundle, cases: tuple[VerifiedCaseProjection, ...]
) -> dict[str, JsonObject]:
    by_case = {context["source"]["case_id"]: context for context in bundle.contexts}
    if set(by_case) != {case.case["case_id"] for case in cases}:
        raise AdaptiveRunFailure("SIMULATOR_CONTEXT_INVALID", 4)
    for case in cases:
        context = by_case[case.case["case_id"]]
        expected = {
            "case_hash": _hash(_canonical(case.case)),
            "persona_hash": _hash(_canonical(case.persona)),
            "intent_hash": _hash(_canonical(case.intent)),
            "turn_policy_hash": _hash(_canonical(case.turn_policy)),
            "persona_id": case.persona["persona_id"],
            "intent_id": case.intent["intent_id"],
            "turn_policy_id": case.turn_policy["turn_policy_id"],
        }
        if any(context["source"][key] != value for key, value in expected.items()):
            raise AdaptiveRunFailure("SIMULATOR_CONTEXT_INVALID", 4)
    return by_case


def case_projection(
    context: JsonObject, allowed_reactions: list[str] | None = None
) -> dict[str, Any]:
    return {
        "context_id": context["context_id"],
        "context_version": context["context_version"],
        "persona": context["persona"],
        "intent": context["intent"],
        "known_facts": context["known_facts"],
        "hidden_fact_ids": [fact["fact_id"] for fact in context["hidden_facts"]],
        "user_turn_policy": context["user_turn_policy"],
        "allowed_reaction_ids": allowed_reactions
        or context["user_turn_policy"]["allowed_reaction_ids"],
    }


def _echo_codes(utterance: str, transcript: list[JsonObject]) -> set[str]:
    proposal = _normalize(utterance)
    proposal_tokens = proposal.split()
    result: set[str] = set()
    for turn in transcript:
        if turn.get("role") != "ASSISTANT" or not isinstance(turn.get("content"), str):
            continue
        prior = _normalize(turn["content"])
        prior_tokens = prior.split()
        shorter = min(len(proposal_tokens), len(prior_tokens))
        if proposal == prior or (
            shorter >= 12 and (proposal in prior or prior in proposal)
        ):
            result.add("EXACT_ASSISTANT_ECHO")
            continue
        left = set(zip(proposal_tokens, proposal_tokens[1:], proposal_tokens[2:]))
        right = set(zip(prior_tokens, prior_tokens[1:], prior_tokens[2:]))
        if left and right and len(left & right) / len(left | right) >= 0.80:
            result.add("NEAR_ASSISTANT_ECHO")
    return result


def response_structure(response: SimulatorResponse) -> str | None:
    reason, _ = response_structure_diagnostic(response)
    return reason


_PROPOSAL_KEYS = {"disposition", "user_utterance", "stop_reason_code"}


def _field_class(value: Any, present: bool) -> str:
    if not present:
        return "MISSING"
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "EMPTY_STRING" if not value else "NONEMPTY_STRING"
    return "OTHER"


def _disposition_class(value: Any, present: bool) -> str:
    if not present:
        return "MISSING"
    if value == "EMIT":
        return "EMIT"
    if value == "STOP":
        return "STOP"
    return "NON_STRING" if not isinstance(value, str) else "OTHER"


def _finish_class(value: Any, present: bool) -> str:
    if not present:
        return "MISSING"
    if not isinstance(value, str):
        return "NON_STRING"
    return {
        "stop": "STOP",
        "length": "LENGTH",
        "content_filter": "CONTENT_FILTER",
        "tool_calls": "TOOL_CALLS",
    }.get(value, "OTHER")


def _diagnostic(
    stage: str,
    response_bytes: bytes,
    envelope_class: str,
    content_class: str,
    finish_reason_class: str,
    content: str | None,
    proposal: Any,
) -> dict[str, Any]:
    mapping = proposal if isinstance(proposal, dict) else {}
    presence = {key: key in mapping for key in sorted(_PROPOSAL_KEYS)}
    return {
        "diagnostic_version": "LABS06_SIMULATOR_DIAGNOSTIC_V1",
        "stage": stage,
        "response_byte_count": len(response_bytes),
        "content_byte_count": len(content.encode("utf-8"))
        if content is not None
        else None,
        "envelope_class": envelope_class,
        "content_class": content_class,
        "finish_reason_class": finish_reason_class,
        "known_field_presence": presence,
        "missing_known_field_count": sum(not item for item in presence.values()),
        "unknown_field_count": len(set(mapping) - _PROPOSAL_KEYS)
        if isinstance(proposal, dict)
        else None,
        "disposition_class": _disposition_class(
            mapping.get("disposition"), "disposition" in mapping
        ),
        "user_utterance_class": _field_class(
            mapping.get("user_utterance"), "user_utterance" in mapping
        ),
        "stop_reason_code_class": _field_class(
            mapping.get("stop_reason_code"), "stop_reason_code" in mapping
        ),
    }


def response_structure_diagnostic(
    response: SimulatorResponse, *, privacy_invalid: bool = False
) -> tuple[str | None, dict[str, Any] | None]:
    """Reparse provider bytes and return the first safe structural failure."""

    response_bytes = response.response_bytes or b""
    envelope_class = "INVALID_JSON"
    content_class = "NOT_APPLICABLE"
    finish_class = "MISSING"
    content: str | None = None
    proposal: Any = None

    def fail(stage: str) -> tuple[str, dict[str, Any]]:
        return (
            "SIMULATOR_INVALID_RESPONSE",
            _diagnostic(
                stage,
                response_bytes,
                envelope_class,
                content_class,
                finish_class,
                content,
                proposal,
            ),
        )

    if privacy_invalid:
        return fail("SIMULATOR_RESPONSE_PRIVACY_INVALID")
    try:
        raw = json.loads(response_bytes, object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return fail("SIMULATOR_ENVELOPE_JSON_INVALID")
    if not isinstance(raw, dict):
        envelope_class = "NON_OBJECT"
        return fail("SIMULATOR_ENVELOPE_SHAPE_INVALID")
    if "choices" in raw:
        envelope_class = "CHAT_COMPLETION"
        choices = raw.get("choices")
        if (
            not isinstance(choices, list)
            or not choices
            or not isinstance(choices[0], dict)
            or not isinstance(choices[0].get("message"), dict)
        ):
            return fail("SIMULATOR_ENVELOPE_SHAPE_INVALID")
        first = choices[0]
        finish_class = _finish_class(
            first.get("finish_reason"), "finish_reason" in first
        )
        message = first["message"]
        raw_content = message.get("content")
        content_class = (
            "MISSING"
            if "content" not in message
            else "NULL"
            if raw_content is None
            else "STRING"
            if isinstance(raw_content, str)
            else "OTHER"
        )
        if not isinstance(raw_content, str):
            return fail("SIMULATOR_CONTENT_TYPE_INVALID")
        content = raw_content
        try:
            proposal = json.loads(content, object_pairs_hook=_pairs)
        except (json.JSONDecodeError, ValueError):
            return fail("SIMULATOR_CONTENT_JSON_INVALID")
    elif _PROPOSAL_KEYS & set(raw):
        envelope_class = "DIRECT_PROPOSAL"
        proposal = raw
    else:
        envelope_class = "OTHER_OBJECT"
        return fail("SIMULATOR_ENVELOPE_SHAPE_INVALID")
    if not isinstance(proposal, dict) or set(proposal) != _PROPOSAL_KEYS:
        return fail("SIMULATOR_CONTENT_KEYS_INVALID")
    if envelope_class == "CHAT_COMPLETION" and "usage" in raw:
        usage = raw["usage"]
        if (
            not isinstance(usage, dict)
            or {"prompt_tokens", "completion_tokens"} - set(usage)
            or not all(
                type(usage[key]) is int and usage[key] >= 0
                for key in ("prompt_tokens", "completion_tokens")
            )
        ):
            return fail("SIMULATOR_USAGE_INVALID")
    if not (
        response.status == "SUCCEEDED"
        and response.reason_code is None
        and isinstance(response.consumed_observation_hash, str)
        and _DIGEST.fullmatch(response.consumed_observation_hash)
        and response.speaker_role == "USER"
    ):
        return fail("SIMULATOR_RESPONSE_AUTHORITY_INVALID")
    projected = {
        "disposition": response.disposition,
        "user_utterance": response.user_utterance,
        "stop_reason_code": response.stop_reason_code,
    }
    if proposal != projected:
        return fail("SIMULATOR_RESPONSE_PROJECTION_MISMATCH")
    if response.disposition not in {"EMIT", "STOP"}:
        return fail("SIMULATOR_DISPOSITION_INVALID")
    if response.disposition == "EMIT" and not (
        _text(response.user_utterance) and response.stop_reason_code is None
    ):
        return fail("SIMULATOR_EMIT_FIELDS_INVALID")
    if response.disposition == "STOP" and not (
        response.user_utterance is None and _text(response.stop_reason_code)
    ):
        return fail("SIMULATOR_STOP_FIELDS_INVALID")
    return None, None


def semantic_codes(
    response: SimulatorResponse, request: JsonObject, context: JsonObject
) -> list[str]:
    codes: set[str] = set()
    utterance = response.user_utterance or ""
    allowed_actions = request.get(
        "allowed_action_ids", context["user_turn_policy"]["allowed_action_ids"]
    )
    allowed_stops = request.get(
        "allowed_stop_reason_codes",
        [item["stop_reason_code"] for item in context["stop_registry"]],
    )
    if response.disposition == "STOP" and (
        response.stop_reason_code not in allowed_stops
    ):
        codes.add("STOP_NOT_ALLOWED")
    if utterance:
        codes |= _echo_codes(utterance, request["transcript"])
        if _match(utterance, context["assistant_only_literal_matchers"]):
            codes.add("ROLE_INVERSION")
        if any(
            _match(utterance, fact["literal_matchers"])
            for fact in context["hidden_facts"]
        ):
            codes.add("HIDDEN_FACT_LEAK")
        if _match(utterance, context["fixed_fact_conflict_literal_matchers"]):
            codes.add("FIXED_FACT_CONFLICT")
        for action in context["action_registry"]:
            if (
                _match(utterance, action["literal_matchers"])
                and action["action_id"] not in allowed_actions
            ):
                codes.add("UNAUTHORIZED_ACTION")
    return sorted(codes)


def transition(context: JsonObject, response: SimulatorResponse) -> dict[str, Any]:
    reaction = next(
        (
            item
            for item in context["reaction_registry"]
            if item["reaction_id"] == response.reaction_id
        ),
        None,
    )
    if reaction is None or not _valid_state(reaction["state_transition"]):
        raise AdaptiveRunFailure("SIMULATOR_CONTEXT_INVALID", 4)
    return cast(dict[str, Any], json.loads(_canonical(reaction["state_transition"])))


def _teacher_request(item: JsonObject, context: JsonObject) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL,
        "episode_id": f"teacher-{item['item_id']}",
        "turn_index": item["turn_index"],
        "case_context": case_projection(context, item["allowed_reaction_ids"]),
        "interaction_state": item["interaction_state"],
        "transcript": item["transcript"],
        "latest_observation": item["latest_observation"],
        "remaining_turns": item["remaining_turns"],
        "allowed_action_ids": item["allowed_action_ids"],
        "allowed_stop_reason_codes": item["allowed_stop_reason_codes"],
    }


def evaluate_teacher_forced(
    context_bundle: Path,
    *,
    simulator: SimulatorTransport,
    context_loader: SimulatorContextLoader | None = None,
) -> Mapping[str, bytes]:
    bundle = load_bundle(context_bundle, context_loader)
    contexts = {context["context_id"]: context for context in bundle.contexts}
    attempts: list[dict[str, Any]] = []
    for ordinal, item in enumerate(bundle.teacher_forced_items, 1):
        context = contexts[item["context_id"]]
        request = _teacher_request(item, context)
        reason: str | None = None
        details: list[str] = []
        diagnostic: dict[str, Any] | None = None
        try:
            response = simulator.complete(request)
        except (OSError, TimeoutError):
            response = SimulatorResponse(
                "FAILED",
                _canonical(request),
                None,
                reason_code="SIMULATOR_PROVIDER_ERROR",
            )
            reason = "SIMULATOR_PROVIDER_ERROR"
        if not isinstance(response, SimulatorResponse):
            response = SimulatorResponse("INVALID", _canonical(request), None)
            reason = "SIMULATOR_INVALID_RESPONSE"
        if reason is None:
            reason, diagnostic = response_structure_diagnostic(response)
            if diagnostic is not None:
                details = [cast(str, diagnostic["stage"])]
        if (
            reason is None
            and response.consumed_observation_hash
            != item["latest_observation"]["observation_hash"]
        ):
            reason = "ADAPTATION_BINDING_MISMATCH"
        if reason is None:
            details = semantic_codes(response, request, context)
            if details:
                reason = "SIMULATOR_SEMANTIC_INVALID"
        outcome = (
            "REJECTED"
            if reason
            else ("STOPPED" if response.disposition == "STOP" else "EMITTED")
        )
        attempts.append(
            {
                "ordinal": ordinal,
                "item_id": item["item_id"],
                "stratum": item["stratum"],
                "context_id": item["context_id"],
                "outcome": outcome,
                "reason_code": reason,
                "detail_codes": details,
                "diagnostic": diagnostic,
                "request_hash": _hash(response.request_bytes or _canonical(request)),
                "response_hash": _hash(response.response_bytes)
                if response.response_bytes is not None
                else None,
                "proposal": {
                    "speaker_role": response.speaker_role,
                    "disposition": response.disposition,
                    "reaction_id": response.reaction_id,
                    "action_ids": response.action_ids,
                    "user_utterance": response.user_utterance,
                    "stop_reason_code": response.stop_reason_code,
                },
                "provider_http_exchange_count": response.provider_http_exchange_count
                if type(response.provider_http_exchange_count) is int
                and response.provider_http_exchange_count >= 0
                else 0,
                "input_tokens": response.input_tokens
                if type(response.input_tokens) is int and response.input_tokens >= 0
                else 0,
                "output_tokens": response.output_tokens
                if type(response.output_tokens) is int and response.output_tokens >= 0
                else 0,
            }
        )
    attempts_bytes = b"".join(_canonical(item, lf=True) for item in attempts)
    panel_hash = _hash(
        _canonical([item["item_id"] for item in bundle.teacher_forced_items])
    )
    review = {
        "artifact_kind": "labs06_human_fidelity_review",
        "schema_version": 1,
        "protocol_version": PROTOCOL,
        "rubric_version": RUBRIC,
        "bundle_hash": bundle.bundle_hash,
        "panel_identity_hash": panel_hash,
        "review_state": "PENDING",
        "denominator": 30,
        "required_accepted": 24,
        "critical_failure_codes": list(CRITICAL_CODES),
        "stratum_counts": dict(sorted(_STRATA.items())),
        "review_items": [
            {
                "item_id": item["item_id"],
                "stratum": item["stratum"],
                "attempt_outcome": attempt["outcome"],
                "human_accepted": None,
                "human_notes": None,
            }
            for item, attempt in zip(bundle.teacher_forced_items, attempts, strict=True)
        ],
    }
    review_bytes = _canonical(review, lf=True)
    manifest = {
        "artifact_kind": "labs06_fidelity_manifest",
        "schema_version": 1,
        "protocol_version": PROTOCOL,
        "bundle_hash": bundle.bundle_hash,
        "panel_identity_hash": panel_hash,
        "attempt_count": 30,
        "emitted_count": sum(item["outcome"] == "EMITTED" for item in attempts),
        "stopped_count": sum(item["outcome"] == "STOPPED" for item in attempts),
        "rejected_count": sum(item["outcome"] == "REJECTED" for item in attempts),
        "simulator_http_exchange_count": sum(
            item["provider_http_exchange_count"] for item in attempts
        ),
        "simulator_input_tokens": sum(item["input_tokens"] for item in attempts),
        "simulator_output_tokens": sum(item["output_tokens"] for item in attempts),
        "artifacts": {
            "fidelity_attempts.jsonl": _hash(attempts_bytes),
            "human_fidelity_review.json": _hash(review_bytes),
        },
    }
    return {
        "fidelity_attempts.jsonl": attempts_bytes,
        "human_fidelity_review.json": review_bytes,
        "fidelity_manifest.json": _canonical(manifest, lf=True),
    }
