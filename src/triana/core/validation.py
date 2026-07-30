"""Structural, invariant, identity, and integrity validation."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Never, cast
from urllib.parse import urlsplit

from pydantic import ValidationError

from triana.contracts.models import DOCUMENT_MODELS
from triana.core.canonical import SET_KEYS, domain_hash, set_sort_key, without_field
from triana.core.errors import TrianaError
from triana.core.parser import NonIntegerNumber

KINDS = frozenset(DOCUMENT_MODELS)
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
DIGEST_FIELDS = {
    "content_hash",
    "source_export_hash",
    "runtime_hash",
    "command_hash",
    "fixture_fingerprint",
    "configuration_fingerprint",
    "reset_policy_hash",
    "execution_contract_hash",
    "candidate_fingerprint",
    "baseline_fingerprint",
    "trace_hash",
    "case_version",
    "evaluator_version",
    "expected_hash",
    "schema_hash",
    "trial_id",
    "policy_hash",
    "input_evidence_hash",
    "protected_case_version",
    "previous_record_hash",
    "supersedes_record_hash",
    "current_record_hash",
    "record_hash",
    "head_record_hash",
    "chain_hash",
    "release_record_hash",
    "attestation_hash",
    "fingerprint",
}


def _escape_pointer(part: str | int) -> str:
    return str(part).replace("~", "~0").replace("/", "~1")


def pointer(path: tuple[str | int, ...] | list[str | int]) -> str:
    return "".join(f"/{_escape_pointer(part)}" for part in path)


def _clean_location(
    data: Any, location: tuple[Any, ...], error_type: str
) -> tuple[str | int, ...]:
    clean: list[str | int] = []
    current = data
    for part in location:
        if isinstance(part, (str, int)):
            if isinstance(current, dict) and isinstance(part, str) and part in current:
                clean.append(part)
                current = current[part]
            elif isinstance(current, list) and isinstance(part, int):
                clean.append(part)
                current = current[part] if part < len(current) else None
            elif isinstance(part, str):
                # Pydantic inserts a union variant label into locations. Skip
                # labels that are not actual wire keys, but retain missing keys.
                if isinstance(current, dict) and part in current.values():
                    continue
                clean.append(part)
                current = None
    if error_type == "union_tag_not_found":
        discriminator_by_parent = {
            "events": "event_kind",
            "locator": "locator_kind",
            "handoff_requirement": "handoff_kind",
            "qualification": "qualification_state",
            "evidence_requirements": "requirement_kind",
            "assertion": "assertion_kind",
            "matcher": "matcher_kind",
            "baseline": "baseline_kind",
            "execution_contracts": "execution_binding_kind",
            "randomization_policy": "randomization_policy_kind",
            "randomization": "randomization_kind",
            "scope": "scope_kind",
            "chain_link": "link_kind",
        }
        parent = clean[-1] if clean else None
        if isinstance(parent, int) and len(clean) >= 2:
            parent = clean[-2]
        discriminator = discriminator_by_parent.get(str(parent))
        if discriminator is not None:
            clean.append(discriminator)
    return tuple(clean)


def _schema_error(path: tuple[str | int, ...], message: str) -> dict[str, str]:
    return {
        "code": "SCHEMA_VALIDATION_FAILED",
        "json_pointer": pointer(path),
        "safe_message": message,
    }


def _sensitive_child(parent: dict[str, Any], key: str, opaque: bool) -> bool:
    return (
        opaque
        or (key == "arguments" and parent.get("event_kind") == "TOOL_CALL")
        or (
            key == "result"
            and parent.get("event_kind") == "TOOL_RESULT"
            and parent.get("result_state") == "SUCCEEDED"
        )
    )


def _object_key_errors(
    value: Any, path: tuple[str | int, ...] = ()
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            try:
                size = len(key.encode("utf-8"))
            except UnicodeEncodeError:
                size = 0
            if not 1 <= size <= 256:
                # Never place a rejected customer-owned key in a public pointer.
                errors.append(
                    _schema_error(path, "An object key violates its UTF-8 byte domain.")
                )
            else:
                errors.extend(_object_key_errors(item, (*path, key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_object_key_errors(item, (*path, index)))
    return errors


def _walk_non_integer(
    value: Any, path: tuple[str | int, ...] = ()
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if isinstance(value, NonIntegerNumber):
        errors.append(
            _schema_error(path, "A strict integer or canonical string is required.")
        )
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_walk_non_integer(item, (*path, key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_walk_non_integer(item, (*path, index)))
    return errors


def _structural_conditions(
    value: Any, path: tuple[str | int, ...] = (), *, opaque: bool = False
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if isinstance(value, dict):
        if opaque:
            for key, item in value.items():
                errors.extend(_structural_conditions(item, (*path, key), opaque=True))
            return errors
        locator_kind = value.get("locator_kind")
        if locator_kind == "HTTPS" and isinstance(value.get("url"), str):
            url = urlsplit(value["url"])
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username is not None
                or url.password is not None
                or url.query
                or url.fragment
            ):
                errors.append(_schema_error((*path, "url"), "HTTPS locator is unsafe."))

        event_kind = value.get("event_kind")
        if event_kind == "MODEL_OBSERVATION":
            present = {"cost_amount", "cost_currency"} & value.keys()
            if len(present) == 1:
                missing = "cost_currency" if "cost_amount" in present else "cost_amount"
                errors.append(
                    _schema_error((*path, missing), "Cost fields appear together.")
                )
            amount = value.get("cost_amount")
            if isinstance(amount, str) and amount.startswith("-"):
                errors.append(
                    _schema_error((*path, "cost_amount"), "Cost is non-negative.")
                )
        if event_kind == "TOOL_RESULT":
            state = value.get("result_state")
            if state == "SUCCEEDED":
                if "result" not in value:
                    errors.append(
                        _schema_error((*path, "result"), "Result is required.")
                    )
                for field in ("error_code", "error_message"):
                    if field in value:
                        errors.append(
                            _schema_error((*path, field), "Field is forbidden.")
                        )
            elif state == "ERROR":
                for field in ("error_code", "error_message"):
                    if field not in value:
                        errors.append(
                            _schema_error((*path, field), "Field is required.")
                        )
                if "result" in value:
                    errors.append(
                        _schema_error((*path, "result"), "Field is forbidden.")
                    )
        if event_kind == "TERMINAL":
            if value.get("terminal_state") == "SUCCESS" and "reason_code" in value:
                errors.append(
                    _schema_error((*path, "reason_code"), "Field is forbidden.")
                )
            if (
                value.get("terminal_state") in {"ERROR", "ABORTED"}
                and "reason_code" not in value
            ):
                errors.append(
                    _schema_error((*path, "reason_code"), "Field is required.")
                )

        if "component_kind" in value and "candidate_fingerprint" in value:
            state = value.get("declared_state")
            if state == "UNKNOWN" and "difference_reference_id" not in value:
                errors.append(
                    _schema_error(
                        (*path, "difference_reference_id"), "Field is required."
                    )
                )
            if state in {"CHANGED", "UNCHANGED"} and "difference_reference_id" in value:
                errors.append(
                    _schema_error(
                        (*path, "difference_reference_id"), "Field is forbidden."
                    )
                )

        if (
            value.get("qualification_state") == "NOT_YET"
            and value.get("reason_code") == "FIXTURE_REQUIRED"
        ):
            errors.append(
                _schema_error(
                    (*path, "reason_code"), "Reason is reserved for NEEDS_FIXTURE."
                )
            )

        if value.get("assertion_kind") == "tool_called_before" and value.get(
            "before_tool_name"
        ) == value.get("after_tool_name"):
            errors.append(
                _schema_error((*path, "after_tool_name"), "Tool names must differ.")
            )

        if value.get("regex_engine") == "PYTHON_RE_3_13":
            regex_field = "pattern" if "pattern" in value else "output_pattern"
            pattern_value = value.get(regex_field)
            if isinstance(pattern_value, str):
                try:
                    compiled = re.compile(pattern_value)
                except re.error:
                    errors.append(
                        _schema_error((*path, regex_field), "Regex does not compile.")
                    )
                else:
                    if value.get("assertion_kind") == "no_unbacked_claim" and (
                        compiled.groupindex != {"claim": 1} or compiled.groups != 1
                    ):
                        errors.append(
                            _schema_error(
                                (*path, regex_field),
                                "Regex must contain exactly the claim group.",
                            )
                        )

        if value.get("seal_state") == "SEALED" and "current_record_hash" not in value:
            errors.append(
                _schema_error((*path, "current_record_hash"), "Field is required.")
            )
        if value.get("seal_state") == "UNSIGNED" and "current_record_hash" in value:
            errors.append(
                _schema_error((*path, "current_record_hash"), "Field is forbidden.")
            )

        comparison_status = value.get("comparison_status")
        if comparison_status == "COMPARABLE":
            for field in ("baseline", "movement"):
                if field not in value:
                    errors.append(_schema_error((*path, field), "Field is required."))
        if comparison_status == "MOVED" and "baseline" not in value:
            errors.append(_schema_error((*path, "baseline"), "Field is required."))

        if (
            value.get("link_kind") == "APPEND"
            and "position" in value
            and "previous_record_hash" not in value
        ):
            errors.append(
                _schema_error((*path, "previous_record_hash"), "Field is required.")
            )

        if value.get("decision_type") == "APPROVE_WITH_EXCEPTION":
            if "exception_rationale_reference" not in value:
                errors.append(
                    _schema_error(
                        (*path, "exception_rationale_reference"), "Field is required."
                    )
                )
        elif "decision_type" in value and "exception_rationale_reference" in value:
            errors.append(
                _schema_error(
                    (*path, "exception_rationale_reference"), "Field is forbidden."
                )
            )

        if "baseline" in value and "components" in value:
            baseline = value.get("baseline")
            baseline_kind = (
                baseline.get("baseline_kind") if isinstance(baseline, dict) else None
            )
            for index, component in enumerate(value.get("components", [])):
                if not isinstance(component, dict):
                    continue
                if (
                    baseline_kind == "APPROVED"
                    and "baseline_fingerprint" not in component
                ):
                    errors.append(
                        _schema_error(
                            (*path, "components", index, "baseline_fingerprint"),
                            "Field is required.",
                        )
                    )
                if baseline_kind == "MISSING" and "baseline_fingerprint" in component:
                    errors.append(
                        _schema_error(
                            (*path, "components", index, "baseline_fingerprint"),
                            "Field is forbidden.",
                        )
                    )

        for key, item in value.items():
            errors.extend(
                _structural_conditions(
                    item,
                    (*path, key),
                    opaque=_sensitive_child(value, key, opaque),
                )
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_structural_conditions(item, (*path, index), opaque=opaque))
    return errors


def _raise_schema(
    errors: list[dict[str, str]], kind: str | None, version: int | None
) -> None:
    if not errors:
        return
    errors.sort(key=lambda item: (item["json_pointer"].encode("utf-8"), item["code"]))
    if len(errors) > 99:
        errors = errors[:99] + [
            {
                "code": "VALIDATION_ERROR_LIMIT_REACHED",
                "json_pointer": "",
                "safe_message": "Additional validation errors were omitted.",
            }
        ]
    raise TrianaError(
        "SCHEMA_VALIDATION_FAILED",
        "Document does not satisfy the closed schema.",
        errors[0]["json_pointer"],
        kind,
        version,
        errors,
    )


def _validate_digest_formats(
    value: Any, path: tuple[str | int, ...] = (), *, opaque: bool = False
) -> None:
    if isinstance(value, dict):
        if opaque:
            return
        for key, item in value.items():
            if key in DIGEST_FIELDS and (
                not isinstance(item, str) or DIGEST_PATTERN.fullmatch(item) is None
            ):
                raise TrianaError(
                    "HASH_FORMAT_INVALID",
                    "A hash field has an invalid format.",
                    pointer((*path, key)),
                )
            _validate_digest_formats(
                item,
                (*path, key),
                opaque=_sensitive_child(value, key, opaque),
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_digest_formats(item, (*path, index), opaque=opaque)


def _ensure_unique_sets(
    value: Any,
    path: tuple[str | int, ...] = (),
    field: str | None = None,
    *,
    opaque: bool = False,
) -> None:
    if isinstance(value, dict):
        if opaque:
            return
        for key, item in value.items():
            _ensure_unique_sets(
                item,
                (*path, key),
                key,
                opaque=_sensitive_child(value, key, opaque),
            )
    elif isinstance(value, list):
        if not opaque and field in SET_KEYS:
            seen: set[Any] = set()
            for item in value:
                key = set_sort_key(field, item)
                if key in seen:
                    raise TrianaError(
                        "IMPOSSIBLE_STATE",
                        "A set-like collection contains a duplicate stable key.",
                        pointer(path),
                    )
                seen.add(key)
        for index, item in enumerate(value):
            _ensure_unique_sets(item, (*path, index), opaque=opaque)


def _identity_error(path: tuple[str | int, ...], message: str) -> Never:
    raise TrianaError("IDENTITY_MISMATCH", message, pointer(path))


def _validate_derived(
    value: Any, path: tuple[str | int, ...] = (), *, opaque: bool = False
) -> None:
    if isinstance(value, dict):
        if opaque:
            return
        if "runtime_hash" in value and "components" in value:
            expected = domain_hash(
                "runtime_fingerprint", without_field(value, "runtime_hash")
            )
            if value["runtime_hash"] != expected:
                _identity_error(
                    (*path, "runtime_hash"), "Runtime identity does not match."
                )
        if "execution_contract_hash" in value and "contract_version" in value:
            expected = domain_hash(
                "execution_contract", without_field(value, "execution_contract_hash")
            )
            if value["execution_contract_hash"] != expected:
                _identity_error(
                    (*path, "execution_contract_hash"),
                    "Execution-contract identity does not match.",
                )
        for key, item in value.items():
            _validate_derived(
                item,
                (*path, key),
                opaque=_sensitive_child(value, key, opaque),
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_derived(item, (*path, index), opaque=opaque)


def _fixed_rate(passes: int, evaluable: int) -> str:
    if evaluable == 0:
        return "0.000000"
    return str(
        (Decimal(passes) / Decimal(evaluable)).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN
        )
    )


def _impossible(path: tuple[str | int, ...], message: str) -> Never:
    raise TrianaError("IMPOSSIBLE_STATE", message, pointer(path))


def _validate_trace(value: dict[str, Any]) -> None:
    events = value["events"]
    capabilities = set(value["observation_scope"]["capabilities"])
    seen: dict[str, tuple[int, str]] = {}
    terminal_count = 0
    final_count = 0
    for index, event in enumerate(events):
        if event["sequence"] != index:
            _impossible(
                ("events", index, "sequence"), "Trace sequence is not contiguous."
            )
        event_id = event["event_id"]
        if event_id in seen:
            _impossible(
                ("events", index, "event_id"), "Trace event identity is duplicated."
            )
        parent = event.get("parent_event_id")
        if parent is not None and parent not in seen:
            _impossible(
                ("events", index, "parent_event_id"), "Trace parent is not earlier."
            )
        kind = event["event_kind"]
        if kind == "TOOL_RESULT":
            call = seen.get(event["tool_call_event_id"])
            if call is None or call[1] != "TOOL_CALL":
                _impossible(
                    ("events", index, "tool_call_event_id"),
                    "Tool result does not reference an earlier tool call.",
                )
        if kind == "TERMINAL":
            terminal_count += 1
            if index != len(events) - 1 or terminal_count > 1:
                _impossible(("events", index), "Terminal event placement is invalid.")
        if kind == "ASSISTANT_MESSAGE" and event["is_final"]:
            final_count += 1
            if final_count > 1:
                _impossible(
                    ("events", index, "is_final"), "Final message is duplicated."
                )
        requirements = {
            "USER_MESSAGE": {"CONVERSATION_TURNS"},
            "ASSISTANT_MESSAGE": {"CONVERSATION_TURNS"},
            "SYSTEM_VISIBLE_MESSAGE": {"CONVERSATION_TURNS"},
            "MODEL_OBSERVATION": {"MODEL_OUTPUT"},
            "TOOL_CALL": {"TOOL_DISPATCH", "TOOL_ARGUMENTS"},
            "TOOL_RESULT": {"TOOL_RESULTS"},
            "HANDOFF": {"ESCALATION_HANDOFF"},
            "TERMINAL": {"TERMINAL_STATE"},
        }[kind]
        if not requirements <= capabilities:
            _impossible(
                ("observation_scope", "capabilities"),
                "Observation scope does not cover trace events.",
            )
        if "latency_ms" in event and "TIMING" not in capabilities:
            _impossible(
                ("observation_scope", "capabilities"), "Timing is not observed."
            )
        if "cost_amount" in event and "COST" not in capabilities:
            _impossible(("observation_scope", "capabilities"), "Cost is not observed.")
        seen[event_id] = (index, kind)


def _validate_obligation(
    obligation: dict[str, Any], path: tuple[str | int, ...]
) -> None:
    statements = [obligation["obligation_statement"]]
    for field in (
        "applicability_conditions",
        "expected_behavior",
        "prohibited_behavior",
        "allowed_alternatives",
    ):
        statements.extend(obligation[field])
    ids = [item["statement_id"] for item in statements]
    if len(ids) != len(set(ids)):
        _impossible(path, "Behavior statement identity is duplicated.")


def _requirements_index(
    requirements: list[dict[str, Any]], path: tuple[str | int, ...]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    assertions: set[str] = set()
    for index, requirement in enumerate(requirements):
        requirement_id = requirement["requirement_id"]
        if requirement_id in result:
            _impossible((*path, index, "requirement_id"), "Requirement is duplicated.")
        result[requirement_id] = requirement
        if requirement["requirement_kind"] == "TRIANA_ASSERTION":
            assertion_id = requirement["assertion"]["assertion_id"]
            if assertion_id in assertions:
                _impossible((*path, index, "assertion"), "Assertion is duplicated.")
            assertions.add(assertion_id)
    return result


def _validate_case(value: dict[str, Any]) -> None:
    messages = value["replay_input"]["messages"]
    ids = [message["message_id"] for message in messages]
    if len(ids) != len(set(ids)):
        _impossible(
            ("replay_input", "messages"), "Replay message identity is duplicated."
        )
    _validate_obligation(value["release_obligation"], ("release_obligation",))
    _requirements_index(value["evidence_requirements"], ("evidence_requirements",))
    references = {item["reference_id"] for item in value.get("source_evidence", [])}
    del references


def _bound_contract(binding: dict[str, Any], side: str) -> dict[str, Any]:
    kind = binding["execution_binding_kind"]
    if kind == "MATCHED":
        return cast(dict[str, Any], binding["execution_contract"])
    if kind == "CANDIDATE_ONLY":
        return cast(dict[str, Any], binding["candidate_execution_contract"])
    return cast(
        dict[str, Any],
        binding["baseline_execution_contract"]
        if side == "BASELINE"
        else binding["candidate_execution_contract"],
    )


def _validate_summary(summary: dict[str, Any], path: tuple[str | int, ...]) -> None:
    if (
        not summary["pass_count"]
        <= summary["evaluable_count"]
        <= summary["trial_count"]
    ):
        _impossible(path, "Summary counts exceed their denominators.")
    if summary["pass_rate"] != _fixed_rate(
        summary["pass_count"], summary["evaluable_count"]
    ):
        _impossible((*path, "pass_rate"), "Stored pass rate does not match counts.")


def _validate_comparison(comparison: dict[str, Any]) -> None:
    status = comparison["comparison_status"]
    baseline = comparison.get("baseline")
    movement = comparison.get("movement")
    reasons = set(comparison["reason_codes"])
    _validate_summary(comparison["candidate"], ("comparison", "candidate"))
    if baseline is not None:
        _validate_summary(baseline, ("comparison", "baseline"))
    if status == "COMPARABLE":
        if (
            baseline is None
            or movement is None
            or {
                "MISSING_APPROVED_BASELINE",
                "EXECUTION_CONTRACT_MISMATCH",
            }
            & reasons
        ):
            _impossible(("comparison",), "Comparable fields are inconsistent.")
        exact = Decimal(comparison["candidate"]["pass_rate"]) - Decimal(
            baseline["pass_rate"]
        )
        expected = str(exact.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))
        if movement != expected:
            _impossible(("comparison", "movement"), "Movement does not match rates.")
    elif status == "FIRST_OBSERVATION":
        if (
            baseline is not None
            or movement is not None
            or "MISSING_APPROVED_BASELINE" not in reasons
        ):
            _impossible(("comparison",), "First-observation fields are inconsistent.")
    elif status == "MOVED":
        if (
            baseline is None
            or movement is not None
            or "EXECUTION_CONTRACT_MISMATCH" not in reasons
        ):
            _impossible(("comparison",), "Moved fields are inconsistent.")
    elif movement is not None or not reasons:
        _impossible(("comparison",), "Insufficient-evidence fields are inconsistent.")


def _validate_record(value: dict[str, Any]) -> None:
    _validate_obligation(value["release_obligation"], ("release_obligation",))
    requirements = _requirements_index(
        value["evidence_requirements"], ("evidence_requirements",)
    )
    binding = value["execution_contracts"]
    binding_kind = binding["execution_binding_kind"]
    baseline = value["release_change"]["baseline"]
    comparison = value["comparison"]
    if value["recommendation"] != value["policy_evaluation"]["recommendation"]:
        _impossible(("recommendation",), "Recommendation differs from policy snapshot.")
    if binding_kind == "CANDIDATE_ONLY":
        if (
            baseline["baseline_kind"] != "MISSING"
            or comparison["comparison_status"] != "FIRST_OBSERVATION"
        ):
            _impossible(
                ("execution_contracts",), "Candidate-only binding is inconsistent."
            )
    elif binding_kind == "MISMATCHED":
        if (
            baseline["baseline_kind"] != "APPROVED"
            or comparison["comparison_status"] != "MOVED"
        ):
            _impossible(("execution_contracts",), "Mismatched binding is inconsistent.")
        if (
            binding["baseline_execution_contract"]["execution_contract_hash"]
            == binding["candidate_execution_contract"]["execution_contract_hash"]
        ):
            _impossible(("execution_contracts",), "Mismatched contracts are identical.")
    else:
        if baseline["baseline_kind"] != "APPROVED" or comparison[
            "comparison_status"
        ] not in {
            "COMPARABLE",
            "INSUFFICIENT_EVIDENCE",
        }:
            _impossible(("execution_contracts",), "Matched binding is inconsistent.")

    unresolved_ids = {
        item["reference_id"]
        for item in value["release_change"]["unresolved_difference_references"]
    }
    for index, component in enumerate(value["release_change"]["components"]):
        reference_id = component.get("difference_reference_id")
        if reference_id is not None and reference_id not in unresolved_ids:
            _impossible(
                ("release_change", "components", index, "difference_reference_id"),
                "Difference reference does not resolve.",
            )

    sides: dict[str, list[dict[str, Any]]] = {"BASELINE": [], "CANDIDATE": []}
    seen_results: set[str] = set()
    for index, trial in enumerate(value["trials"]):
        trial_path = ("trials", index)
        sides[trial["side"]].append(trial)
        if trial["run_id"] != value["run_id"]:
            _impossible((*trial_path, "run_id"), "Trial run differs from record.")
        if trial["case_version"] != value["protected_case_version"]:
            _identity_error(
                (*trial_path, "case_version"), "Trial case differs from record."
            )
        if trial["side"] == "BASELINE":
            if baseline["baseline_kind"] != "APPROVED":
                _impossible(
                    (*trial_path, "side"), "Baseline trial has no approved baseline."
                )
            expected_ref = baseline["code_ref"]
        else:
            expected_ref = value["release_change"]["candidate_code_ref"]
        if trial["code_ref"] != expected_ref:
            _impossible((*trial_path, "code_ref"), "Trial code reference differs.")
        contract = _bound_contract(binding, trial["side"])
        if trial["execution_contract_hash"] != contract["execution_contract_hash"]:
            _identity_error(
                (*trial_path, "execution_contract_hash"),
                "Trial execution contract differs.",
            )
        projection = {
            key: trial[key]
            for key in (
                "run_id",
                "case_version",
                "side",
                "trial_index",
                "code_ref",
                "execution_contract_hash",
            )
        }
        if trial["trial_id"] != domain_hash("trial_identity", projection):
            _identity_error((*trial_path, "trial_id"), "Trial identity does not match.")
        if trial["execution_status"] == "COMPLETED" and "trace_reference" not in trial:
            _impossible(
                (*trial_path, "trace_reference"), "Completed trial lacks trace."
            )
        if (
            trial["execution_status"] != "COMPLETED"
            and trial["end_to_end_status"] == "PASS"
        ):
            _impossible(
                (*trial_path, "end_to_end_status"), "Incomplete trial cannot pass."
            )
        policy = contract["randomization_policy"]
        randomization = trial["randomization"]
        if policy["randomization_policy_kind"] == "NONE":
            if randomization["randomization_kind"] != "NONE":
                _impossible((*trial_path, "randomization"), "Randomization differs.")
        elif (
            randomization["randomization_kind"] != "SEEDED"
            or randomization["generator"] != policy["generator"]
            or randomization["generator_version"] != policy["generator_version"]
        ):
            _impossible((*trial_path, "randomization"), "Randomization differs.")
        gap_ids = {gap["gap_id"] for gap in trial["gaps"]}
        execution_indices = [
            result["execution_index"] for result in trial["assertion_results"]
        ]
        if execution_indices != list(range(len(execution_indices))):
            _impossible((*trial_path, "assertion_results"), "Execution indices differ.")
        for result_field in ("assertion_results", "customer_evaluator_results"):
            for result_index, result in enumerate(trial[result_field]):
                result_path = (*trial_path, result_field, result_index)
                if result["result_id"] in seen_results:
                    _impossible(
                        (*result_path, "result_id"), "Result identity is duplicated."
                    )
                seen_results.add(result["result_id"])
                requirement = requirements.get(result["requirement_id"])
                if requirement is None:
                    _impossible(
                        (*result_path, "requirement_id"),
                        "Requirement does not resolve.",
                    )
                if result_field == "assertion_results":
                    if (
                        requirement["requirement_kind"] != "TRIANA_ASSERTION"
                        or result["assertion_id"]
                        != requirement["assertion"]["assertion_id"]
                        or result["assertion_version"]
                        != requirement["assertion"]["assertion_version"]
                    ):
                        _impossible(result_path, "Assertion result identity differs.")
                elif (
                    requirement["requirement_kind"] != "CUSTOMER_EVALUATOR"
                    or result["evaluator_id"] != requirement["evaluator_id"]
                    or result["evaluator_version"] != requirement["evaluator_version"]
                    or result["check_id"] != requirement["check_id"]
                ):
                    _impossible(result_path, "Evaluator result identity differs.")
                if result["status"] == "PASS" and result["gap_ids"]:
                    _impossible((*result_path, "gap_ids"), "PASS result carries a gap.")
                if result["status"] == "UNEVALUABLE" and not result["gap_ids"]:
                    _impossible(
                        (*result_path, "gap_ids"), "UNEVALUABLE result lacks a gap."
                    )
                if not set(result["gap_ids"]) <= gap_ids:
                    _impossible(
                        (*result_path, "gap_ids"), "Result gap does not resolve."
                    )

    for side, trials in sides.items():
        indices = sorted(trial["trial_index"] for trial in trials)
        if indices != list(range(len(indices))):
            _impossible(("trials",), f"{side} trial indices are not contiguous.")
        if trials:
            declared = _bound_contract(binding, side)["declared_trial_count"]
            if len(trials) > declared:
                _impossible(("trials",), "Trial count exceeds execution contract.")

    if binding_kind in {"MATCHED", "MISMATCHED"}:
        must_pair = binding_kind == "MATCHED" or (
            binding["baseline_execution_contract"]["randomization_policy"]
            == binding["candidate_execution_contract"]["randomization_policy"]
        )
        if must_pair:
            baseline_by_index = {
                trial["trial_index"]: trial for trial in sides["BASELINE"]
            }
            candidate_by_index = {
                trial["trial_index"]: trial for trial in sides["CANDIDATE"]
            }
            for trial_index in baseline_by_index.keys() & candidate_by_index.keys():
                if (
                    baseline_by_index[trial_index]["randomization"]
                    != candidate_by_index[trial_index]["randomization"]
                ):
                    candidate_position = value["trials"].index(
                        candidate_by_index[trial_index]
                    )
                    _impossible(
                        ("trials", candidate_position, "randomization"),
                        "Paired trial randomization differs.",
                    )

    for index, gap in enumerate(value["record_gaps"]):
        if gap["scope"]["scope_kind"] != "RECORD":
            _impossible(
                ("record_gaps", index, "scope"),
                "A record gap must have record scope.",
            )

    chain_link = value["chain_link"]
    if chain_link["link_kind"] == "APPEND":
        supersedes = chain_link.get("supersedes_record_hash")
        if supersedes is not None and supersedes in {
            chain_link["previous_record_hash"],
            value.get("current_record_hash"),
        }:
            _impossible(
                ("chain_link", "supersedes_record_hash"),
                "A superseded record must be distinct.",
            )

    _validate_comparison(comparison)
    for side_name, key in (("CANDIDATE", "candidate"), ("BASELINE", "baseline")):
        summary = comparison.get(key)
        if summary is None:
            continue
        trials = sides[side_name]
        evaluable = sum(t["end_to_end_status"] in {"PASS", "FAIL"} for t in trials)
        passes = sum(t["end_to_end_status"] == "PASS" for t in trials)
        if (
            summary["trial_count"] != len(trials)
            or summary["evaluable_count"] != evaluable
            or summary["pass_count"] != passes
        ):
            _impossible(("comparison", key), "Comparison counts differ from trials.")


def _validate_chain(value: dict[str, Any]) -> None:
    hashes: set[str] = set()
    for index, entry in enumerate(value["entries"]):
        if entry["position"] != index:
            _impossible(
                ("entries", index, "position"), "Chain positions are not contiguous."
            )
        if entry["record_hash"] in hashes:
            _impossible(("entries", index, "record_hash"), "Record hash is duplicated.")
        hashes.add(entry["record_hash"])
        if index == 0:
            if (
                entry["link_kind"] != "GENESIS"
                or "previous_record_hash" in entry
                or "supersedes_record_hash" in entry
            ):
                _impossible(("entries", index), "Genesis entry is invalid.")
        else:
            if (
                entry["link_kind"] != "APPEND"
                or entry.get("previous_record_hash")
                != value["entries"][index - 1]["record_hash"]
            ):
                _impossible(("entries", index), "Append entry is invalid.")
            supersedes = entry.get("supersedes_record_hash")
            if supersedes is not None and supersedes in {
                entry["previous_record_hash"],
                entry["record_hash"],
            }:
                _impossible(
                    ("entries", index, "supersedes_record_hash"),
                    "A superseded record must be distinct.",
                )
    if value["head_record_hash"] != value["entries"][-1]["record_hash"]:
        _impossible(("head_record_hash",), "Chain head differs from final entry.")


def _validate_self_hash(value: dict[str, Any]) -> None:
    kind = value["contract_kind"]
    mapping = {
        "normalized_trace": ("trace_hash", "normalized_trace", "IDENTITY_MISMATCH"),
        "protected_case": ("case_version", "protected_case", "IDENTITY_MISMATCH"),
        "release_evidence_record": (
            "current_record_hash",
            "release_evidence_record",
            "HASH_MISMATCH",
        ),
        "record_chain": ("chain_hash", "record_chain", "HASH_MISMATCH"),
        "decision_attestation": (
            "attestation_hash",
            "decision_attestation",
            "HASH_MISMATCH",
        ),
    }
    field, identity_kind, error_code = mapping[kind]
    if kind == "release_evidence_record" and value["seal_state"] == "UNSIGNED":
        return
    expected = domain_hash(identity_kind, without_field(value, field))
    if value[field] != expected:
        raise TrianaError(
            error_code,
            "Stored identity does not match canonical content.",
            f"/{field}",
            kind,
            value["schema_version"],
        )


def validate_document(raw_value: Any) -> dict[str, Any]:
    """Validate one public document and return a normalized plain object."""
    if not isinstance(raw_value, dict) or not isinstance(
        raw_value.get("contract_kind"), str
    ):
        raise TrianaError(
            "SCHEMA_VALIDATION_FAILED",
            "contract_kind must be a registered string.",
            "/contract_kind",
        )
    kind = raw_value["contract_kind"]
    if kind not in KINDS:
        raise TrianaError(
            "UNKNOWN_CONTRACT_KIND",
            "contract_kind is not registered.",
            "/contract_kind",
        )
    version = raw_value.get("schema_version")
    if type(version) is not int:
        raise TrianaError(
            "SCHEMA_VALIDATION_FAILED",
            "schema_version must be a strict integer.",
            "/schema_version",
            kind,
        )
    if version != 1:
        raise TrianaError(
            "UNSUPPORTED_SCHEMA_VERSION",
            "schema_version is not supported.",
            "/schema_version",
            kind,
            version,
        )

    schema_errors = _walk_non_integer(raw_value)
    schema_errors.extend(_object_key_errors(raw_value))
    try:
        model = DOCUMENT_MODELS[kind].model_validate(raw_value)
    except ValidationError as error:
        for item in error.errors(
            include_url=False, include_context=False, include_input=False
        ):
            location = _clean_location(raw_value, item["loc"], item["type"])
            schema_errors.append(_schema_error(location, "Field violates its schema."))
    schema_errors.extend(_structural_conditions(raw_value))
    _raise_schema(schema_errors, kind, version)

    normalized = model.model_dump(mode="python", exclude_unset=True)
    _validate_digest_formats(normalized)
    _ensure_unique_sets(normalized)
    _validate_derived(normalized)
    if kind == "normalized_trace":
        _validate_trace(normalized)
    elif kind == "protected_case":
        _validate_case(normalized)
    elif kind == "release_evidence_record":
        _validate_record(normalized)
    elif kind == "record_chain":
        _validate_chain(normalized)
    _validate_self_hash(normalized)
    return normalized
