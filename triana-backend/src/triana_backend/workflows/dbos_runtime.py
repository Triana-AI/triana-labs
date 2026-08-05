"""Initial DBOS workflow with explicit durable, replay-safe steps.

Execution is foreground from the caller's perspective: the executor starts the
durable workflow using a deterministic ID, then waits for its result. It does
not enqueue work or claim a separate worker fleet.
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Mapping

from dbos import DBOS, SetWorkflowID

from .contracts import ImportRunRequest, WorkflowReceipt, WorkflowServices
from .identity import workflow_id_for


_services: WorkflowServices | None = None
_services_lock = Lock()


def configure_workflow_services(services: WorkflowServices) -> None:
    """Install process-local ports before DBOS launch.

    Durable arguments contain only identifiers. Infrastructure dependencies
    are resolved locally and therefore never serialized into DBOS history.
    """

    global _services
    with _services_lock:
        if _services is not None and _services is not services:
            raise RuntimeError("workflow services are already configured")
        _services = services


def _configured_services() -> WorkflowServices:
    if _services is None:
        raise RuntimeError("workflow services are not configured")
    return _services


def _reference(value: Mapping[str, Any], key: str) -> dict[str, str]:
    """Reduce a port result to one opaque identifier safe for DBOS history."""

    if set(value) != {key} or not isinstance(value[key], str) or not value[key]:
        raise RuntimeError(f"workflow port must return exactly one nonempty {key}")
    return {key: value[key]}


def _receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and reduce the terminal result to the public safe receipt."""

    receipt = WorkflowReceipt.from_mapping(value)
    return {
        "workflow_id": receipt.workflow_id,
        "run_id": receipt.run_id,
        "report_id": receipt.report_id,
        "attempt_number": receipt.attempt_number,
        "status": receipt.status,
    }


@DBOS.step(name="labs08.record-run-started")
def record_run_started(
    workflow_id: str, request: Mapping[str, Any]
) -> Mapping[str, Any]:
    return _reference(
        _configured_services().mark_running(workflow_id, request), "run_id"
    )


@DBOS.step(name="labs08.execute-labs-analysis")
def execute_labs_analysis(run_id: str) -> Mapping[str, Any]:
    return _reference(
        _configured_services().execute_labs_analysis(run_id), "analysis_result_id"
    )


@DBOS.step(name="labs08.persist-labs-result")
def persist_labs_result(
    run_id: str, analysis_result_ref: Mapping[str, Any]
) -> Mapping[str, Any]:
    return _reference(
        _configured_services().persist_labs_result(run_id, analysis_result_ref),
        "fact_set_id",
    )


@DBOS.step(name="labs08.project-stored-report")
def project_stored_report(
    run_id: str, persisted_fact_set_ref: Mapping[str, Any]
) -> Mapping[str, Any]:
    return _reference(
        _configured_services().project_stored_report(run_id, persisted_fact_set_ref),
        "report_id",
    )


@DBOS.step(name="labs08.complete-run")
def complete_run(run_id: str, report_ref: Mapping[str, Any]) -> Mapping[str, Any]:
    return _receipt(_configured_services().complete_run(run_id, report_ref))


@DBOS.workflow(name="labs08.import-analyze-project")
def import_analyze_project_workflow(
    workflow_id: str, request: Mapping[str, Any]
) -> Mapping[str, Any]:
    run = record_run_started(workflow_id, request)
    run_id = str(run["run_id"])
    analysis_ref = execute_labs_analysis(run_id)
    fact_set_ref = persist_labs_result(run_id, analysis_ref)
    report_ref = project_stored_report(run_id, fact_set_ref)
    receipt = complete_run(run_id, report_ref)
    if receipt["workflow_id"] != workflow_id:
        raise RuntimeError("completed receipt workflow identity mismatch")
    if receipt["run_id"] != run_id:
        raise RuntimeError("completed receipt run identity mismatch")
    if receipt["report_id"] != report_ref["report_id"]:
        raise RuntimeError("completed receipt report identity mismatch")
    return receipt


class DBOSForegroundExecutor:
    """Start-or-get a deterministic DBOS workflow and wait truthfully."""

    def start_or_get(self, request: ImportRunRequest) -> WorkflowReceipt:
        workflow_id = workflow_id_for(request)
        with SetWorkflowID(workflow_id):
            handle = DBOS.start_workflow(
                import_analyze_project_workflow,
                workflow_id,
                request.as_history_payload(),
            )
        result = handle.get_result()
        return WorkflowReceipt.from_mapping(result)
