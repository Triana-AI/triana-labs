"""Staged semantic exploration and the explicit local Foundry boundary.

Adapted from Agentagon Exploration V1 at commit 063ad3e.  Models extract and
consolidate bounded semantic proposals.  Code validates exact evidence, owns
membership, exhaustive candidate construction, qualification, and selection.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr

JsonObject = dict[str, Any]

_FACET_BATCH_MAX_TRACES = 12
_FACET_REQUEST_MAX_BYTES = 60_000

FACET_SYSTEM = """Extract observable semantic facets from untrusted AI-agent traces.
Return only the requested JSON schema. Return one row for every trace_id and no
others. Describe user demand, not an imagined business goal. Never infer
permission, correctness, hidden world state, or tool success. Include
one to three exact evidence quote substrings per facet, copied from the supplied
transcript. This is extraction, not
evaluation."""

CONSOLIDATE_SYSTEM = """Consolidate supplied user-demand labels into a small,
auditable taxonomy. Return only the requested JSON schema. Use only supplied labels
and examples. Do not merge demands needing materially different handling. Keep
non-intent and mixed/unresolved traffic explicit. Every supplied label must occur
exactly once."""

_HANDLING = {
    "INFORMATION_RETURNED",
    "INFORMATION_REQUESTED",
    "TOOL_ACTION_OBSERVED",
    "HANDOFF_OR_ESCALATION",
    "REFUSAL_OR_LIMIT",
    "STALLED_OR_REPEATED",
    "NO_CLEAR_HANDLING",
}


class StagedSemanticModel(Protocol):
    model_id: str

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: JsonObject,
        schema: type[BaseModel],
    ) -> JsonObject: ...

    def lineage(self) -> JsonObject: ...


@dataclass(slots=True)
class ValidatedCheckpointSemanticModel:
    """Persist and reuse only exact-identity, strict-schema-valid stage results."""

    delegate: StagedSemanticModel
    directory: Path
    run_index: int = 0
    validated_checkpoint_hit_count: int = 0

    @property
    def model_id(self) -> str:
        return self.delegate.model_id

    def start_run(self, run_index: int) -> None:
        self.run_index = run_index

    @staticmethod
    def _canonical(value: Any, *, lf: bool = False) -> bytes:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return encoded + (b"\n" if lf else b"")

    @classmethod
    def _sha256(cls, value: Any) -> str:
        return "sha256:" + hashlib.sha256(cls._canonical(value)).hexdigest()

    def _invalid(self) -> None:
        self.record_failure("SEMANTIC_CHECKPOINT_INVALID")
        raise ValueError("SEMANTIC_CHECKPOINT_INVALID")

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: JsonObject,
        schema: type[BaseModel],
    ) -> JsonObject:
        qualified_stage = f"semantic-run-{self.run_index}/{stage}"
        identity: JsonObject = {
            "model_id": self.model_id,
            "stage": qualified_stage,
            "system_sha256": self._sha256(system),
            "canonical_payload_sha256": self._sha256(payload),
            "requested_schema_sha256": self._sha256(schema.model_json_schema()),
        }
        checkpoint_id = self._sha256(identity).removeprefix("sha256:")
        path = self.directory / f"{checkpoint_id}.json"
        if path.exists():
            try:
                value = json.loads(path.read_bytes())
                if (
                    not isinstance(value, dict)
                    or set(value) != {
                        "artifact_kind",
                        "schema_version",
                        "identity",
                        "result",
                    }
                    or value.get("artifact_kind") != "semantic_checkpoint_v0"
                    or value.get("schema_version") != 0
                    or value.get("identity") != identity
                ):
                    self._invalid()
                cached = schema.model_validate(value["result"], strict=True)
            except (
                OSError,
                json.JSONDecodeError,
                UnicodeDecodeError,
                TypeError,
                ValueError,
            ):
                self._invalid()
            self.validated_checkpoint_hit_count += 1
            return cached.model_dump(mode="json")

        result = self.delegate.complete_json(
            stage=qualified_stage,
            system=system,
            payload=payload,
            schema=schema,
        )
        try:
            validated = schema.model_validate(result, strict=True)
        except (TypeError, ValueError):
            self._invalid()
        checkpoint: JsonObject = {
            "artifact_kind": "semantic_checkpoint_v0",
            "schema_version": 0,
            "identity": identity,
            "result": validated.model_dump(mode="json"),
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.directory, prefix=f".{checkpoint_id}.", suffix=".tmp"
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(self._canonical(checkpoint, lf=True))
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return validated.model_dump(mode="json")

    def lineage(self) -> JsonObject:
        return {
            **self.delegate.lineage(),
            "validated_checkpoint_hit_count": self.validated_checkpoint_hit_count,
            "resume_policy": "EXPLICIT_VALIDATED_CHECKPOINTS_ONLY",
        }

    def record_failure(self, code: str) -> None:
        record = getattr(self.delegate, "record_failure", None)
        if callable(record):
            record(code)


class _Facet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    demand_summary: str
    goal_label: str
    handling_mode: str
    claimed_action: str
    terminal_summary: str
    evidence_quotes: list[str] = Field(max_length=3)


class _FacetBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facets: list[_Facet]


class _Population(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    description: str
    kind: str
    member_labels: list[str]


class _PopulationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    populations: list[_Population] = Field(max_length=12)


@dataclass(slots=True)
class FoundryStructuredSemanticModel:
    """No-retry, no-fallback structured JSON model for the pinned Foundry host."""

    model_id: str
    endpoint: str
    api_key: str
    timeout_seconds: int = 120
    call_count: int = 0
    attempted_call_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    max_calls: int = 160
    max_request_bytes: int = 400_000
    max_output_tokens_per_call: int = 2_000
    max_reserved_usd: float = 25.0
    reservation_usd_per_call: float = 0.15
    last_failure_code: str | None = None

    @classmethod
    def from_environment(
        cls, environ: Mapping[str, str] | None = None
    ) -> FoundryStructuredSemanticModel | None:
        values = os.environ if environ is None else environ
        if (
            values.get("TRIANA_TRACE_TO_EVAL_SEMANTIC_PROVIDER")
            != "MICROSOFT_FOUNDRY_FIREWORKS"
        ):
            return None
        model_id = values.get("TRIANA_TRACE_TO_EVAL_MODEL_ID")
        endpoint = values.get("AZURE_OPENAI_BASE_URL") or values.get(
            "TRIANA_FOUNDRY_ENDPOINT"
        )
        api_key = values.get("TRIANA_FOUNDRY_API_KEY")
        if model_id != "FW-GLM-5.2" or not endpoint or not api_key:
            raise ValueError("TRACE_TO_EVAL_FOUNDRY_CONFIG_INVALID")
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "kairos-openai-1.openai.azure.com"
            or parsed.path.rstrip("/") != "/openai/v1"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("TRACE_TO_EVAL_FOUNDRY_CONFIG_INVALID")
        return cls(model_id=model_id, endpoint=endpoint.rstrip("/"), api_key=api_key)

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: JsonObject,
        schema: type[BaseModel],
    ) -> JsonObject:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        request_content = json.dumps(
            {"stage": stage, **payload},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        if (
            self.attempted_call_count >= self.max_calls
            or len(request_content.encode("utf-8")) > self.max_request_bytes
            or (self.attempted_call_count + 1) * self.reservation_usd_per_call
            > self.max_reserved_usd
        ):
            raise ValueError("SEMANTIC_BUDGET_EXCEEDED")
        self.attempted_call_count += 1
        model = ChatOpenAI(
            model=self.model_id,
            api_key=SecretStr(self.api_key),
            base_url=self.endpoint,
            max_retries=0,
            max_completion_tokens=self.max_output_tokens_per_call,
            temperature=0,
            timeout=self.timeout_seconds,
        )
        requested_schema = json.dumps(
            schema.model_json_schema(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        instruction = f"{system}\nRequested JSON schema:\n{requested_schema}"
        try:
            raw = model.bind(response_format={"type": "json_object"}).invoke(
                [
                    SystemMessage(content=instruction),
                    HumanMessage(content=request_content),
                ]
            )
        except Exception:  # noqa: BLE001 - redact the provider boundary.
            self.last_failure_code = "SEMANTIC_PROVIDER_CALL_FAILED"
            raise ValueError("SEMANTIC_PROVIDER_CALL_FAILED") from None

        usage = getattr(raw, "usage_metadata", None)
        if isinstance(usage, dict):
            self.input_tokens += int(usage.get("input_tokens", 0) or 0)
            self.output_tokens += int(usage.get("output_tokens", 0) or 0)
        content = getattr(raw, "content", None)
        if not isinstance(content, str) or not content.strip():
            self.last_failure_code = "SEMANTIC_RESPONSE_CONTENT_MISSING"
            raise ValueError("SEMANTIC_RESPONSE_CONTENT_MISSING")
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            self.last_failure_code = "SEMANTIC_RESPONSE_JSON_INVALID"
            raise ValueError("SEMANTIC_RESPONSE_JSON_INVALID") from None
        try:
            parsed = schema.model_validate(decoded, strict=True)
        except (TypeError, ValueError):
            self.last_failure_code = "SEMANTIC_SCHEMA_INVALID"
            raise ValueError("SEMANTIC_SCHEMA_INVALID") from None
        self.call_count += 1
        return parsed.model_dump(mode="json")

    def lineage(self) -> JsonObject:
        return {
            "provider": "MICROSOFT_FOUNDRY_FIREWORKS",
            "model_id": self.model_id,
            "call_count": self.call_count,
            "attempted_call_count": self.attempted_call_count,
            "successful_call_count": self.call_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": None,
            "actual_cost_state": "UNKNOWN_PROVIDER_PRICING",
            "budget": {
                "max_calls": self.max_calls,
                "max_request_bytes_per_call": self.max_request_bytes,
                "max_output_tokens_per_call": self.max_output_tokens_per_call,
                "max_reserved_usd": self.max_reserved_usd,
                "reservation_usd_per_call": self.reservation_usd_per_call,
                "reserved_usd": round(
                    self.attempted_call_count * self.reservation_usd_per_call, 2
                ),
                "reservation_method": "FIXED_PER_CALL_CONSERVATIVE_UPPER_BOUND",
            },
            "last_failure_code": self.last_failure_code,
            "retry_policy": "NONE",
            "fallback_policy": "NONE",
        }

    def record_failure(self, code: str) -> None:
        """Record one content-free provider boundary failure for lineage."""

        if self.last_failure_code is None:
            self.last_failure_code = code


def _transcript(trace: JsonObject) -> str:
    lines = []
    for event in cast(list[JsonObject], trace["events"]):
        kind = cast(str, event["event_kind"])
        if kind in {"USER_MESSAGE", "ASSISTANT_MESSAGE"}:
            lines.append(f"{kind}: {event.get('content', '')}")
        elif kind == "TOOL_CALL":
            lines.append(
                "TOOL_CALL: "
                + str(event.get("tool_name"))
                + " "
                + json.dumps(event.get("arguments"), sort_keys=True)
            )
        elif kind == "TOOL_RESULT":
            lines.append(
                "TOOL_RESULT: "
                + str(event.get("result_state"))
                + " "
                + json.dumps(
                    event.get("result", event.get("error_code")), sort_keys=True
                )
            )
        else:
            lines.append("TERMINAL: " + str(event.get("terminal_state")))
    return "\n".join(lines)[:14_000]


def _facet_units(traces: list[JsonObject]) -> list[JsonObject]:
    return [
        {
            "trace_id": trace["trace_id"],
            "transcript": _transcript(trace),
            "tool_observed": any(
                event["event_kind"] == "TOOL_CALL"
                for event in cast(list[JsonObject], trace["events"])
            ),
            "turn_count": sum(
                event["event_kind"] in {"USER_MESSAGE", "ASSISTANT_MESSAGE"}
                for event in cast(list[JsonObject], trace["events"])
            ),
        }
        for trace in traces
    ]


def _canonical_request_bytes(*, stage: str, payload: JsonObject) -> int:
    return len(
        json.dumps(
            {"stage": stage, **payload},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def _facet_batches(units: list[JsonObject]) -> list[list[JsonObject]]:
    """Partition complete trace units under deterministic count and byte ceilings."""

    batches: list[list[JsonObject]] = []
    current: list[JsonObject] = []
    for unit in units:
        stage = f"facets-{len(batches)}"
        candidate = [*current, unit]
        if (
            len(candidate) <= _FACET_BATCH_MAX_TRACES
            and _canonical_request_bytes(
                stage=stage, payload={"traces": candidate}
            )
            <= _FACET_REQUEST_MAX_BYTES
        ):
            current = candidate
            continue
        if current:
            batches.append(current)
            stage = f"facets-{len(batches)}"
        if (
            _canonical_request_bytes(stage=stage, payload={"traces": [unit]})
            > _FACET_REQUEST_MAX_BYTES
        ):
            raise ValueError("SEMANTIC_REQUEST_TOO_LARGE")
        current = [unit]
    if current:
        batches.append(current)
    return batches


def _extract_facets(
    model: StagedSemanticModel, units: list[JsonObject]
) -> tuple[list[JsonObject], int]:
    output: list[JsonObject] = []
    invalid = 0
    for batch_index, batch in enumerate(_facet_batches(units)):
        response = model.complete_json(
            stage=f"facets-{batch_index}",
            system=FACET_SYSTEM,
            payload={"traces": batch},
            schema=_FacetBatch,
        )
        supplied = {
            row.get("trace_id"): row
            for row in cast(list[JsonObject], response.get("facets", []))
            if isinstance(row, dict)
        }
        for unit in batch:
            row = supplied.get(unit["trace_id"])
            if row is None:
                invalid += 1
                continue
            quotes = row.get("evidence_quotes")
            valid_quotes = (
                [
                    quote
                    for quote in quotes
                    if isinstance(quote, str) and quote in unit["transcript"]
                ]
                if isinstance(quotes, list)
                else []
            )
            mode = row.get("handling_mode")
            label = row.get("goal_label")
            if (
                not valid_quotes
                or mode not in _HANDLING
                or not isinstance(label, str)
                or not label.strip()
            ):
                invalid += 1
                continue
            output.append(
                {
                    "trace_id": unit["trace_id"],
                    "demand_summary": str(row.get("demand_summary", ""))[:300],
                    "goal_label": " ".join(label.split())[:120],
                    "handling_mode": mode,
                    "claimed_action": row.get("claimed_action")
                    if row.get("claimed_action") in {"TRUE", "FALSE", "UNKNOWN"}
                    else "UNKNOWN",
                    "terminal_summary": str(row.get("terminal_summary", ""))[:300],
                    "evidence_quotes": valid_quotes[:3],
                    "tool_observed": unit["tool_observed"],
                    "turn_count": unit["turn_count"],
                }
            )
    return output, invalid


def _consolidate(
    model: StagedSemanticModel, facets: list[JsonObject]
) -> tuple[list[JsonObject], dict[str, str], int]:
    examples: dict[str, list[str]] = defaultdict(list)
    for facet in facets:
        examples[cast(str, facet["goal_label"])].append(
            cast(str, facet["demand_summary"])
        )
    labels = sorted(examples)
    if not labels:
        return [], {}, 0
    items = [
        {
            "key": label,
            "label": label,
            "examples": examples[label][:4],
            "original_labels": [label],
        }
        for label in labels
    ]
    level = 0
    while len(items) > 40:
        reduced: list[JsonObject] = []
        for offset in range(0, len(items), 40):
            batch = items[offset : offset + 40]
            response = model.complete_json(
                stage=f"population-consolidation-{level}-{offset // 40}",
                system=CONSOLIDATE_SYSTEM,
                payload={
                    "labels": [
                        {
                            "label": item["key"],
                            "display_label": item["label"],
                            "examples": item["examples"],
                        }
                        for item in batch
                    ]
                },
                schema=_PopulationBatch,
            )
            by_key = {cast(str, item["key"]): item for item in batch}
            used: set[str] = set()
            for row_index, row in enumerate(
                cast(list[JsonObject], response.get("populations", []))
            ):
                members = row.get("member_labels") if isinstance(row, dict) else None
                valid = (
                    [
                        member
                        for member in members
                        if member in by_key and member not in used
                    ]
                    if isinstance(members, list)
                    else []
                )
                if not valid:
                    continue
                used.update(valid)
                originals = sorted(
                    label
                    for member in valid
                    for label in cast(list[str], by_key[member]["original_labels"])
                )
                reduced.append(
                    {
                        "key": f"L{level}-{offset}-{row_index}",
                        "label": str(row.get("label", "Mixed or unresolved demand")),
                        "examples": [
                            example
                            for member in valid
                            for example in cast(list[str], by_key[member]["examples"])
                        ][:4],
                        "original_labels": originals,
                    }
                )
            for item in batch:
                if item["key"] not in used:
                    reduced.append(item)
        if len(reduced) >= len(items):
            return (
                [
                    {
                        "population_id": "P01",
                        "label": "Mixed or unresolved demand",
                        "description": "Hierarchical consolidation did not reduce the supplied labels.",
                        "kind": "MIXED_UNRESOLVED",
                        "member_labels": labels,
                    }
                ],
                {label: "P01" for label in labels},
                len(labels),
            )
        items = reduced
        level += 1
    response = model.complete_json(
        stage="population-consolidation-final",
        system=CONSOLIDATE_SYSTEM,
        payload={
            "labels": [
                {
                    "label": item["key"],
                    "display_label": item["label"],
                    "examples": item["examples"],
                }
                for item in items
            ]
        },
        schema=_PopulationBatch,
    )
    item_by_key = {cast(str, item["key"]): item for item in items}
    mapping: dict[str, str] = {}
    populations: list[JsonObject] = []
    invalid = 0
    for index, row in enumerate(
        cast(list[JsonObject], response.get("populations", [])), 1
    ):
        if not isinstance(row, dict):
            invalid += 1
            continue
        members = row.get("member_labels")
        if not isinstance(members, list):
            invalid += 1
            continue
        item_members = [
            member
            for member in members
            if isinstance(member, str) and member in item_by_key
        ]
        valid_members = sorted(
            label
            for member in item_members
            for label in cast(list[str], item_by_key[member]["original_labels"])
            if label not in mapping
        )
        if not valid_members:
            invalid += 1
            continue
        population_id = f"P{index:02d}"
        mapping.update({member: population_id for member in valid_members})
        populations.append(
            {
                "population_id": population_id,
                "label": " ".join(str(row.get("label", population_id)).split())[:120],
                "description": " ".join(str(row.get("description", "")).split())[:500],
                "kind": row.get("kind")
                if row.get("kind")
                in {
                    "PROPOSED_GOAL",
                    "NON_INTENT_TRAFFIC",
                    "MIXED_UNRESOLVED",
                }
                else "MIXED_UNRESOLVED",
                "member_labels": sorted(valid_members),
            }
        )
    missing = [label for label in labels if label not in mapping]
    if missing:
        invalid += len(missing)
        population_id = f"P{len(populations) + 1:02d}"
        populations.append(
            {
                "population_id": population_id,
                "label": "Mixed or unresolved demand",
                "description": "Semantic labels omitted by consolidation remain unresolved.",
                "kind": "MIXED_UNRESOLVED",
                "member_labels": missing,
            }
        )
        mapping.update({label: population_id for label in missing})
    return populations, mapping, invalid


def _qualifies(values: list[Any], kind: str) -> bool:
    if len(values) < 10:
        return False
    if kind == "CATEGORY":
        return sum(count >= 3 for count in Counter(values).values()) >= 2
    if kind == "BOOLEAN":
        counts = Counter(values)
        return counts[True] >= 3 and counts[False] >= 3
    return len(set(values)) >= 2


def _inventory(
    facets: list[JsonObject], populations: list[JsonObject], mapping: Mapping[str, str]
) -> tuple[list[JsonObject], list[JsonObject]]:
    by_population: dict[str, list[JsonObject]] = defaultdict(list)
    for facet in facets:
        by_population[mapping[cast(str, facet["goal_label"])]].append(facet)
    rendered_populations: list[JsonObject] = []
    candidates: list[JsonObject] = []
    labels = {row["population_id"]: row for row in populations}
    for population_id in sorted(by_population):
        rows = by_population[population_id]
        definition = labels[population_id]
        evidence_ids = sorted(cast(str, row["trace_id"]) for row in rows)
        rendered_populations.append(
            {
                "label": definition["label"],
                "description": definition["description"],
                "evidence_trace_ids": evidence_ids,
            }
        )
        signals = (
            (
                "HANDLING_MODE",
                "CATEGORY",
                [row["handling_mode"] for row in rows],
                f"Classify the observed handling for {definition['label']}.",
            ),
            (
                "CLAIM_WITHOUT_ACTION_EVIDENCE",
                "BOOLEAN",
                [
                    row["claimed_action"] == "TRUE" and not row["tool_observed"]
                    for row in rows
                    if row["claimed_action"] != "UNKNOWN"
                ],
                f"Identify explicit completion claims without matching visible action evidence for {definition['label']}.",
            ),
            (
                "TURN_COUNT",
                "NUMBER",
                [row["turn_count"] for row in rows],
                f"Measure interaction depth for {definition['label']}.",
            ),
        )
        for signal, value_type, values, criterion in signals:
            candidates.append(
                {
                    "name": f"{definition['label']} · {signal.lower().replace('_', ' ')}",
                    "criterion": criterion,
                    "evidence_trace_ids": evidence_ids,
                    "signal": signal,
                    "value_type": value_type,
                    "support": len(rows),
                    "evaluable": len(values),
                    "distribution": dict(sorted(Counter(map(str, values)).items())),
                    "qualification": "QUALIFIED"
                    if _qualifies(values, value_type)
                    else "OBSERVED_ONLY",
                }
            )
    return rendered_populations, candidates


def run_staged_analysis(
    model: StagedSemanticModel, traces: list[JsonObject]
) -> JsonObject:
    """Execute one full staged proposal run and return the aggregate engine shape."""

    units = _facet_units(traces)
    facets, invalid_facets = _extract_facets(model, units)
    populations, mapping, invalid_populations = _consolidate(model, facets)
    rendered_populations, inventory = _inventory(facets, populations, mapping)
    qualified = [row for row in inventory if row["qualification"] == "QUALIFIED"]
    qualified.sort(
        key=lambda row: (-cast(int, row["evaluable"]), cast(str, row["name"]))
    )
    return {
        "populations": rendered_populations,
        "eval_candidates": [
            {
                "name": row["name"],
                "criterion": row["criterion"],
                "evidence_trace_ids": row["evidence_trace_ids"],
            }
            for row in qualified
        ],
        "behavior_candidate_inventory": inventory,
        "semantic_gap_count": invalid_facets + invalid_populations,
    }


__all__ = [
    "FoundryStructuredSemanticModel",
    "StagedSemanticModel",
    "run_staged_analysis",
]
