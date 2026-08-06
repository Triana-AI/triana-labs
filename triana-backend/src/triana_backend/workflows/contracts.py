"""JSON-safe workflow contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ImportRunRequest:
    import_id: str
    request_identity: str
    attempt_number: int
    labs_version: str
    config_identity: str
    provider_identity: str | None = None

    def as_history_payload(self) -> dict[str, Any]:
        """Return only identifiers/version metadata safe for DBOS history."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class WorkflowReceipt:
    workflow_id: str
    run_id: str
    report_id: str
    attempt_number: int
    status: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> WorkflowReceipt:
        receipt = cls(
            workflow_id=str(value["workflow_id"]),
            run_id=str(value["run_id"]),
            report_id=str(value["report_id"]),
            attempt_number=int(value["attempt_number"]),
            status=str(value["status"]),
        )
        if not receipt.workflow_id or not receipt.run_id or not receipt.report_id:
            raise ValueError("workflow receipt identities must be nonempty")
        if receipt.attempt_number < 1:
            raise ValueError("workflow receipt attempt_number must be positive")
        if receipt.status not in {"COMPLETED", "COMPLETED_WITH_GAPS"}:
            raise ValueError("workflow receipt is not a completed state")
        return receipt


class WorkflowServices(Protocol):
    """Replay-safe effects used by named DBOS steps.

    Implementations must converge on unique keys. Methods accept identifiers,
    never source bytes, conversation bodies, provider responses, or secrets.
    """

    def mark_running(
        self, workflow_id: str, request: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def execute_labs_analysis(self, run_id: str) -> Mapping[str, Any]: ...

    def persist_labs_result(
        self, run_id: str, analysis_result_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def project_stored_report(
        self, run_id: str, persisted_fact_set_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def complete_run(
        self, run_id: str, report_ref: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...
