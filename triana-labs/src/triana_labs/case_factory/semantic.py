"""Table-driven conversion, grounding checks, and deterministic diversity."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Any, cast

from triana_labs.case_factory.primitives import (
    LOCAL_KEY,
    SAFE_CODE,
    SAFE_ID,
    Invalid,
    Json,
    bounded_text,
    canonical,
    compact_id,
    domain_hash,
)

ASSETS = {
    "persona": (
        "persona_key",
        "persona_id",
        "persona_proposal",
        ("behavioral_traits", "communication_tendencies", "constraints"),
    ),
    "intent": (
        "intent_key",
        "intent_id",
        "intent_proposal",
        (
            "known_constraints",
            "observed_success_signals",
            "observed_failure_or_abandonment_signals",
        ),
    ),
    "turn-policy": (
        "turn_policy_key",
        "turn_policy_id",
        "turn_policy_proposal",
        (
            "information_reveal_policy",
            "reaction_rules",
            "clarification_behavior",
            "escalation_tendencies",
            "stop_conditions",
            "forbidden_inventions",
        ),
    ),
}
CASE_ARRAYS = (
    "known_facts",
    "private_user_facts",
    "unknowns",
    "allowed_user_actions",
    "tool_world_constraints",
    "termination_conditions",
)
ASSET_IDS = ("persona_id", "intent_id", "turn_policy_id")
LOCAL_ASSET_KEYS = ("persona_key", "intent_key", "turn_policy_key")
FORBIDDEN = tuple(
    item.split()
    for item in (
        "race",
        "ethnicity",
        "religion",
        "pregnant",
        "pregnancy",
        "disability",
        "disabled",
        "medical condition",
        "sexual orientation",
        "gender identity",
        "citizenship",
        "nationality",
    )
)


@dataclass
class Lane:
    personas: list[Json]
    intents: list[Json]
    policies: list[Json]
    cases: list[Json]
    positions: dict[str, int]
    invalid: int = 0
    valid_refs: int = 0
    invalid_refs: int = 0


class CaseInvalid(Invalid):
    def __init__(self, valid_refs: int = 0, invalid_refs: int = 0) -> None:
        self.valid_refs = valid_refs
        self.invalid_refs = invalid_refs


def diagnose(draft: Json, citations: list[Json]) -> list[Json]:
    """Return the closed repair defects needed by the recovery contract."""

    citation_map = {item["citation_id"]: item for item in citations}
    defects: list[Json] = []
    for group_name in ("personas", "intents", "turn_policies", "cases"):
        for item_index, item in enumerate(draft[group_name]):
            for claim_index, claim in enumerate(item["grounding_claims"]):
                if claim["support_state"] != "SUPPORTED":
                    continue
                resolving = sorted(
                    {value for value in claim["citation_ids"] if value in citation_map}
                )
                traces = {citation_map[value]["trace_id"] for value in resolving}
                if len(traces) < 2:
                    defects.append(
                        {
                            "code": "SUPPORT_CARDINALITY_MISMATCH",
                            "path": f"/{group_name}/{item_index}/grounding_claims/{claim_index}",
                            "message": "SUPPORTED requires citations from at least two traces",
                            "related_ids": resolving,
                            "repairable": True,
                        }
                    )
    for index, policy in enumerate(draft["turn_policies"]):
        if not policy["reaction_rules"]:
            defects.append(
                {
                    "code": "EMPTY_REACTION_RULES",
                    "path": f"/turn_policies/{index}/reaction_rules",
                    "message": "reaction_rules must contain at least one item",
                    "related_ids": [],
                    "repairable": True,
                }
            )
    for index, case in enumerate(draft["cases"]):
        claim_keys = {
            claim["claim_key"]
            for claim in case["grounding_claims"]
            if claim["citation_ids"]
        }
        if not _has_observed_anchor(case, claim_keys):
            defects.append(
                {
                    "code": "MISSING_OBSERVED_ANCHOR",
                    "path": f"/cases/{index}",
                    "message": "case must contain at least one case-local OBSERVED item",
                    "related_ids": [],
                    "repairable": True,
                }
            )
    return sorted(
        defects,
        key=lambda item: (
            item["code"],
            item["path"],
            canonical(item["related_ids"]),
        ),
    )


def _has_observed_anchor(value: Any, claim_keys: set[str]) -> bool:
    if isinstance(value, dict):
        if value.get("basis") == "OBSERVED":
            keys = value.get("claim_keys")
            if isinstance(keys, list) and any(item in claim_keys for item in keys):
                return True
        return any(_has_observed_anchor(item, claim_keys) for item in value.values())
    if isinstance(value, list):
        return any(_has_observed_anchor(item, claim_keys) for item in value)
    return False


def convert_lane(
    draft: Json,
    citations: list[Json],
    lineage: Json,
    input_hash: str,
    intelligence_hash: str,
    *,
    privacy_class: str = "SYNTHETIC",
    strict_cases: bool,
    expected_case_count: int = 5,
) -> Lane:
    if (
        not all(
            1 <= len(draft[name]) <= 10
            for name in ("personas", "intents", "turn_policies")
        )
        or len(draft["cases"]) != expected_case_count
    ):
        raise Invalid
    citation_map = {item["citation_id"]: item for item in citations}
    common = {
        "schema_version": 1,
        "proposal_state": "PROPOSED",
        "fidelity": (
            "OWNER_AUTHORIZED_REAL_DATA_GROUNDED"
            if privacy_class == "OWNER_AUTHORIZED_REAL_DATA_CANARY"
            else "SYNTHETIC_CORPUS_GROUNDED"
        ),
        "input_manifest_hash": input_hash,
        "intelligence_manifest_hash": intelligence_hash,
        "lineage": lineage,
    }
    groups: list[list[Json]] = []
    local_maps: list[dict[str, str]] = []
    for values, kind in zip(
        (draft["personas"], draft["intents"], draft["turn_policies"]),
        ASSETS,
        strict=True,
    ):
        records, local = _assets(values, kind, common, citation_map)
        groups.append(records)
        local_maps.append(local)
    if any(not item["reaction_rules"] for item in groups[2]):
        raise Invalid
    cases: list[Json] = []
    positions: dict[str, int] = {}
    invalid = valid_refs = invalid_refs = 0
    for position, value in enumerate(draft["cases"]):
        try:
            case, refs = _case(value, common, citation_map, local_maps)
            cases.append(case)
            positions[case["case_id"]] = position
            valid_refs += refs
        except CaseInvalid as error:
            invalid += 1
            valid_refs += error.valid_refs
            invalid_refs += error.invalid_refs
    if strict_cases and invalid:
        raise Invalid
    return Lane(
        personas=sorted(groups[0], key=_record_id),
        intents=sorted(groups[1], key=_record_id),
        policies=sorted(groups[2], key=_record_id),
        cases=sorted(cases, key=lambda item: item["case_id"]),
        positions=positions,
        invalid=invalid,
        valid_refs=valid_refs + _references(groups),
        invalid_refs=invalid_refs,
    )


def _assets(
    values: list[Json], kind: str, common: Json, citations: dict[str, Json]
) -> tuple[list[Json], dict[str, str]]:
    records: list[Json] = []
    local: dict[str, str] = {}
    local_field, id_field, artifact_kind, arrays = ASSETS[kind]
    for value in values:
        key = value[local_field]
        if not _local(key) or key in local:
            raise Invalid
        claims, claim_keys = _claims(value["grounding_claims"], citations)
        used: set[str] = set()
        record = {**common, "artifact_kind": artifact_kind, "grounding_claims": claims}
        record.update({name: _texts(value[name], claim_keys, used) for name in arrays})
        if kind == "persona":
            if not bounded_text(value["label"], 256):
                raise Invalid
            record["label"] = value["label"]
        elif kind == "intent":
            record["goal"] = _text(value["goal"], claim_keys, used)
        if used != set(claim_keys) or _forbidden(record):
            raise Invalid
        record[id_field] = compact_id(kind, record)
        local[key] = record[id_field]
        records.append(record)
    return records, local


def _case(
    value: Json,
    common: Json,
    citations: dict[str, Json],
    assets: list[dict[str, str]],
) -> tuple[Json, int]:
    try:
        references = tuple(
            group[value[key]]
            for key, group in zip(LOCAL_ASSET_KEYS, assets, strict=True)
        )
    except KeyError as error:
        raise CaseInvalid from error
    try:
        claims, claim_keys = _claims(value["grounding_claims"], citations, case=True)
        used: set[str] = set()
        source = value["scenario"]
        scenario: Json = {
            "opening_user_turn": _text(
                source["opening_user_turn"], claim_keys, used, 16_384
            )
        }
        scenario.update(
            {name: _texts(source[name], claim_keys, used) for name in CASE_ARRAYS}
        )
        tools, stressors = source["expected_tool_names"], source["stressor_codes"]
        if (
            not _unique(tools, SAFE_ID)
            or not _unique(stressors, SAFE_CODE, sorted_values=True)
            or len(stressors) > 20
        ):
            raise CaseInvalid
        scenario.update(expected_tool_names=tools, stressor_codes=stressors)
        closure = all(
            name in value for name in ("goal", "done_when", "required_world_keys")
        )
        goal = done_when = None
        required_world_keys: Json | None = None
        source_trace_ids: list[str] = []
        case_origin: str | None = None
        if closure:
            goal = _text(value["goal"], claim_keys, used)
            done_when = _text(value["done_when"], claim_keys, used)
            required_world_keys = _world_keys(value["required_world_keys"])
            anchors = (scenario["opening_user_turn"], goal, done_when)
            if any(item["basis"] != "OBSERVED" for item in anchors):
                raise CaseInvalid
            anchor_claims = {
                claim_id for item in anchors for claim_id in item["claim_ids"]
            }
            source_trace_ids = sorted(
                {
                    citations[citation_id]["trace_id"]
                    for claim in claims
                    if claim["claim_id"] in anchor_claims
                    for citation_id in claim["citation_ids"]
                }
            )
            if not source_trace_ids:
                raise CaseInvalid
            case_origin = (
                "OBSERVED_PRODUCTION_CASE"
                if len(source_trace_ids) == 1
                else "GROUNDED_EXPANDED_CASE"
            )
        evaluation = {
            name: _texts(value["proposed_evaluation"][name], claim_keys, used)
            for name in ("criteria", "abstain_conditions")
        }
        if not all(evaluation.values()) or used != set(claim_keys):
            raise CaseInvalid
        gaps = value["gaps"]
        allowed = {
            "MODEL_DECLARED_AMBIGUITY",
            "WORLD_CONTRACT_UNCLEAR",
            "EVALUATION_SEMANTICS_UNCERTAIN",
        }
        if gaps != sorted(set(gaps)) or not set(gaps) <= allowed:
            raise CaseInvalid
        record = {
            **common,
            "artifact_kind": "simulation_case_candidate",
            "persona_id": references[0],
            "intent_id": references[1],
            "turn_policy_id": references[2],
            "scenario": scenario,
            "grounding_claims": claims,
            "proposed_evaluation": evaluation,
            "gaps": gaps,
        }
        if closure:
            record.update(
                goal=goal,
                done_when=done_when,
                required_world_keys=required_world_keys,
                source_trace_ids=source_trace_ids,
                case_origin=case_origin,
            )
        if not any(
            item["basis"] == "OBSERVED" for item in _supported(record)
        ) or _forbidden(record):
            raise CaseInvalid
        record["case_id"] = compact_id("case", record)
        record["novelty"] = {
            "slot_key": "",
            "exact_duplicate_of": None,
            "duplicate_cluster_id": None,
        }
        return record, sum(len(item["citation_ids"]) for item in claims)
    except CaseInvalid:
        raise
    except Invalid as error:
        raise CaseInvalid from error


def _world_keys(value: Any) -> Json:
    if (
        not isinstance(value, dict)
        or not 1 <= len(value) <= 8
        or any(
            not isinstance(name, str) or not SAFE_ID.fullmatch(name) for name in value
        )
    ):
        raise Invalid
    result: Json = {}
    for name, identifiers in value.items():
        if (
            not isinstance(identifiers, list)
            or not 1 <= len(identifiers) <= 16
            or identifiers != sorted(set(identifiers))
            or any(
                not isinstance(item, str) or not SAFE_ID.fullmatch(item)
                for item in identifiers
            )
        ):
            raise Invalid
        result[name] = identifiers
    return {name: result[name] for name in sorted(result)}


def _claims(
    values: list[Json], citations: dict[str, Json], *, case: bool = False
) -> tuple[list[Json], dict[str, str]]:
    if len(values) > 100:
        raise CaseInvalid if case else Invalid
    result: list[Json] = []
    keys: dict[str, str] = {}
    for value in values:
        key, ids, state = (
            value["claim_key"],
            value["citation_ids"],
            value["support_state"],
        )
        if (
            not _local(key)
            or key in keys
            or not _unique(ids, SAFE_ID, sorted_values=True)
            or not ids
            or not bounded_text(value["claim"], 4096)
        ):
            raise CaseInvalid if case else Invalid
        missing = sum(item not in citations for item in ids)
        if missing:
            if case:
                raise CaseInvalid(len(ids) - missing, missing)
            raise Invalid
        count = len({citations[item]["trace_id"] for item in ids})
        if state == "SINGLE_OBSERVATION":
            valid = count == 1
        else:
            valid = state in {"SUPPORTED", "CONFLICTED"} and count >= 2
        if not valid:
            raise CaseInvalid if case else Invalid
        preimage = {
            "claim": value["claim"],
            "support_state": state,
            "citation_ids": ids,
        }
        claim_id = compact_id("claim", preimage)
        result.append({"claim_id": claim_id, **preimage})
        keys[key] = claim_id
    return result, keys


def _text(
    value: Json, claims: dict[str, str], used: set[str], maximum: int = 4096
) -> Json:
    keys = value["claim_keys"]
    if (
        not bounded_text(value["text"], maximum)
        or len(keys) != len(set(keys))
        or len(keys) > 100
    ):
        raise Invalid
    if value["basis"] == "OBSERVED" and keys and all(item in claims for item in keys):
        used.update(keys)
        ids = sorted(claims[item] for item in keys)
    elif value["basis"] == "GENERATED_VARIATION" and not keys:
        ids = []
    else:
        raise Invalid
    return {"text": value["text"], "basis": value["basis"], "claim_ids": ids}


def _texts(values: list[Json], claims: dict[str, str], used: set[str]) -> list[Json]:
    if len(values) > 20:
        raise Invalid
    return [_text(item, claims, used) for item in values]


def apply_diversity(lane: Lane, citations: list[Json]) -> list[Json]:
    citation_cluster = {
        item["citation_id"]: item["structural_cluster_id"] for item in citations
    }
    assets = _asset_map(lane)
    for case in lane.cases:
        related = (
            case,
            assets[case["persona_id"]],
            assets[case["intent_id"]],
            assets[case["turn_policy_id"]],
        )
        clusters = sorted(
            {
                citation_cluster[citation]
                for record in related
                for claim in record["grounding_claims"]
                for citation in claim["citation_ids"]
            }
        )
        case["novelty"]["slot_key"] = domain_hash(
            "case-slot",
            {
                "persona_id": case["persona_id"],
                "intent_id": case["intent_id"],
                "turn_policy_id": case["turn_policy_id"],
                "structural_cluster_ids": clusters,
                "stressor_codes": case["scenario"]["stressor_codes"],
                "expected_tool_names": case["scenario"]["expected_tool_names"],
            },
        )
    edges: dict[tuple[str, str], set[str]] = {}
    for index, left in enumerate(lane.cases):
        for right in lane.cases[index + 1 :]:
            labels: set[str] = set()
            if left["novelty"]["slot_key"] == right["novelty"]["slot_key"]:
                labels.add("EXACT_SLOT")
            if left["scenario"]["expected_tool_names"] == right["scenario"][
                "expected_tool_names"
            ] and _near(left, right, assets):
                labels.add("NEAR_TEXT")
            if labels:
                edges[(left["case_id"], right["case_id"])] = labels
    return _components(lane.cases, edges)


def _components(
    cases: list[Json], edges: dict[tuple[str, str], set[str]]
) -> list[Json]:
    by_id = {item["case_id"]: item for item in cases}
    adjacency: dict[str, set[str]] = {case_id: set() for case_id in by_id}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    pending = set(by_id)
    result: list[Json] = []
    while pending:
        component = {pending.pop()}
        frontier = set(component)
        while frontier:
            neighbors = set(chain.from_iterable(adjacency[item] for item in frontier))
            frontier = neighbors & pending
            component.update(frontier)
            pending.difference_update(frontier)
        if len(component) < 2:
            continue
        members = sorted(component)
        labels = set(
            chain.from_iterable(
                value for edge, value in edges.items() if set(edge) <= component
            )
        )
        cluster_id = compact_id("duplicate-cluster", members)
        exact_edges = [
            set(edge) for edge, value in edges.items() if "EXACT_SLOT" in value
        ]
        for case_id in members:
            earlier = [
                item
                for item in members
                if item < case_id and {item, case_id} in exact_edges
            ]
            by_id[case_id]["novelty"].update(
                duplicate_cluster_id=cluster_id,
                exact_duplicate_of=min(earlier) if earlier else None,
            )
        result.append(
            {
                "duplicate_cluster_id": cluster_id,
                "representative_case_id": members[0],
                "member_case_ids": members,
                "similarity_basis": next(iter(labels)) if len(labels) == 1 else "MIXED",
            }
        )
    return sorted(result, key=lambda item: item["duplicate_cluster_id"])


def _near(left: Json, right: Json, assets: dict[str, Json]) -> bool:
    def tokens(case: Json) -> set[str]:
        texts = [
            case["scenario"]["opening_user_turn"]["text"],
            assets[case["intent_id"]]["goal"]["text"],
        ]
        texts.extend(
            item["text"] for item in assets[case["turn_policy_id"]]["reaction_rules"]
        )
        return set("\n".join(texts).casefold().split())

    a, b = tokens(left), tokens(right)
    return 100 * len(a & b) >= 85 * len(a | b)


def _supported(value: Any) -> list[Json]:
    if isinstance(value, dict):
        if set(value) == {"text", "basis", "claim_ids"}:
            return [value]
        return list(chain.from_iterable(_supported(item) for item in value.values()))
    if isinstance(value, list):
        return list(chain.from_iterable(_supported(item) for item in value))
    return []


def _forbidden(value: Any) -> bool:
    for text in _strings(value):
        words = "".join(
            char if char.isalnum() else " " for char in text.casefold()
        ).split()
        if any(
            list(needle) == words[index : index + len(needle)]
            for needle in FORBIDDEN
            for index in range(len(words))
        ):
            return True
    return False


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return list(chain.from_iterable(_strings(item) for item in value.values()))
    if isinstance(value, list):
        return list(chain.from_iterable(_strings(item) for item in value))
    return []


def render_tiered_cases(cases: list[Json]) -> bytes:
    """Render a deterministic non-authoritative view without active markup data."""

    def text_block(label: str, value: str) -> list[str]:
        content = value.splitlines() or [""]
        return [f"{label}:", "", *(f"    {line}" for line in content)]

    lines = [
        "# LABS-04 tiered cases",
        "",
        "Non-authoritative review view. Machine JSON remains authoritative.",
    ]
    groups = (
        ("Observed production cases", "OBSERVED_PRODUCTION_CASE"),
        ("Grounded expanded cases", "GROUNDED_EXPANDED_CASE"),
    )
    for heading, origin in groups:
        lines.extend(["", f"## {heading}"])
        selected = sorted(
            (item for item in cases if item.get("case_origin") == origin),
            key=lambda item: item["case_id"],
        )
        if not selected:
            lines.extend(["", "    none"])
        for case in selected:
            lines.extend(
                [
                    "",
                    f"### `{case['case_id']}`",
                    "",
                    f"- Origin: `{origin}`",
                    "- Source traces: "
                    + ", ".join(f"`{item}`" for item in case["source_trace_ids"]),
                    "- Workflow stratum: "
                    + f"`{case.get('workflow_stratum', 'UNDECLARED')}`",
                    "- Gaps: "
                    + (
                        ", ".join(f"`{item}`" for item in case["gaps"])
                        if case["gaps"]
                        else "none"
                    ),
                    "- Owner accepted: not recorded",
                    "",
                    *text_block("Goal", case["goal"]["text"]),
                    "",
                    *text_block("Done when", case["done_when"]["text"]),
                    "",
                    *text_block(
                        "Opening user turn",
                        case["scenario"]["opening_user_turn"]["text"],
                    ),
                    "",
                    "Required world data:",
                ]
            )
            for namespace, identifiers in case["required_world_keys"].items():
                lines.append(
                    f"- `{namespace}`: "
                    + ", ".join(f"`{item}`" for item in identifiers)
                )
    lines.extend(["", "## Invalid or unavailable evidence", "", "    none", ""])
    return "\n".join(lines).encode("utf-8")


def _references(groups: list[list[Json]]) -> int:
    return sum(
        len(claim["citation_ids"])
        for record in chain.from_iterable(groups)
        for claim in record["grounding_claims"]
    )


def _record_id(value: Json) -> str:
    return cast(str, next(value[key] for key in ASSET_IDS if key in value))


def _asset_map(lane: Lane) -> dict[str, Json]:
    return {
        _record_id(item): item
        for item in chain(lane.personas, lane.intents, lane.policies)
    }


def _local(value: Any) -> bool:
    return isinstance(value, str) and LOCAL_KEY.fullmatch(value) is not None


def _unique(value: Any, pattern: Any, *, sorted_values: bool = False) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(set(value))
        and (not sorted_values or value == sorted(value))
        and all(isinstance(item, str) and pattern.fullmatch(item) for item in value)
    )
