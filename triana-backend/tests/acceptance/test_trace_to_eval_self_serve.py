"""Black-box contract for authenticated trace upload through durable review."""

# ruff: noqa: S101 - assertions are the acceptance-test contract.

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from triana_backend.api.app import create_app
from triana_backend.api.contracts import ResourceNotFound

OWNER_ONE = "trace-analysis-owner-one"
OWNER_TWO = "trace-analysis-owner-two"
SUBJECT_ONE = "oidc|analysis-owner-one"
SUBJECT_TWO = "oidc|analysis-owner-two"


class _UnusedPort:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"unrelated port unexpectedly used: {name}")


class _SelfServeAnalysisPlatform:
    """Stateful boundary double; HTTP routes remain the system under test."""

    def __init__(self) -> None:
        self.workspaces: dict[str, str] = {}
        self.agents: dict[str, dict[str, Any]] = {}
        self.imports: dict[str, dict[str, Any]] = {}
        self.conversations: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.reports: dict[str, dict[str, Any]] = {}
        self.report_conversations: dict[tuple[str, str], dict[str, Any]] = {}
        self.queues: dict[str, dict[str, Any]] = {}
        self.rulings: dict[str, list[dict[str, Any]]] = {}
        self.analysis_feature_states = {
            SUBJECT_ONE: "AVAILABLE",
            SUBJECT_TWO: "AVAILABLE",
        }
        self._imports_by_key: dict[tuple[str, str, str], str] = {}
        self._runs_by_import: dict[str, str] = {}
        self._counter = 0

    def _id(self, kind: str) -> str:
        self._counter += 1
        return f"{kind}-synthetic-{self._counter}"

    def get_or_create_me(self, owner_subject: str) -> dict[str, Any]:
        workspace_id = self.workspaces.setdefault(owner_subject, self._id("workspace"))
        return {
            "owner_subject": owner_subject,
            "workspace": {"workspace_id": workspace_id},
        }

    def create_agent(self, owner_subject: str, display_name: str) -> dict[str, Any]:
        workspace_id = self.get_or_create_me(owner_subject)["workspace"]["workspace_id"]
        agent_id = self._id("agent")
        agent = {
            "agent_id": agent_id,
            "workspace_id": workspace_id,
            "owner_subject": owner_subject,
            "display_name": display_name,
            "default_version": {"version_key": "default"},
        }
        self.agents[agent_id] = agent
        return self._public(agent)

    def list_agents(self, owner_subject: str) -> list[dict[str, Any]]:
        return [
            self._public(agent)
            for agent in self.agents.values()
            if agent["owner_subject"] == owner_subject
        ]

    def get_agent(self, owner_subject: str, agent_id: str) -> dict[str, Any]:
        return self._public(self._owned(self.agents, owner_subject, agent_id, "agent"))

    def create_import(
        self,
        owner_subject: str,
        agent_id: str,
        *,
        filename: str,
        content_type: str,
        payload: bytes,
        owner_attested: bool,
        idempotency_key: str,
    ) -> dict[str, Any]:
        del filename, content_type
        assert owner_attested is True
        agent = self._owned(self.agents, owner_subject, agent_id, "agent")
        idempotency_scope = (owner_subject, agent_id, idempotency_key)
        prior_import_id = self._imports_by_key.get(idempotency_scope)
        if prior_import_id is not None:
            return self._public(self.imports[prior_import_id])
        records = [json.loads(line) for line in payload.splitlines()]
        import_id = self._id("import")
        conversation_ids: list[str] = []
        for record in records:
            conversation_id = self._id("conversation")
            conversation = {
                "conversation_id": conversation_id,
                "owner_subject": owner_subject,
                "workspace_id": agent["workspace_id"],
                "agent_id": agent_id,
                "import_id": import_id,
                "trace_id": record["trace_id"],
                "events": record["events"],
            }
            self.conversations[conversation_id] = conversation
            conversation_ids.append(conversation_id)
        imported = {
            "import_id": import_id,
            "owner_subject": owner_subject,
            "workspace_id": agent["workspace_id"],
            "agent_id": agent_id,
            "status": "COMPLETED",
            "physical_record_count": len(records),
            "accepted_conversation_count": len(records),
            "rejected_record_count": 0,
            "records": records,
            "conversation_ids": conversation_ids,
        }
        self.imports[import_id] = imported
        self._imports_by_key[idempotency_scope] = import_id
        return self._public(imported)

    def start_analysis_for_import(
        self, owner_subject: str, agent_id: str, import_id: str
    ) -> dict[str, Any]:
        imported = self._owned(self.imports, owner_subject, import_id, "import")
        if imported["agent_id"] != agent_id:
            raise ResourceNotFound("import", import_id)
        prior_run_id = self._runs_by_import.get(import_id)
        if prior_run_id is not None:
            return self._public(self.runs[prior_run_id])
        run_id = self._id("analysis-run")
        identity = {
            "workspace_id": imported["workspace_id"],
            "agent_id": agent_id,
            "import_id": import_id,
            "run_id": run_id,
        }
        report_id = (
            "sha256:"
            + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        )
        proposal_id = self._id("proposal")
        item_id = self._id("review-item")
        item_hash = "sha256:" + hashlib.sha256(item_id.encode()).hexdigest()
        report = {
            "artifact_kind": "trace_to_eval_report_v0",
            "schema_version": 0,
            "report_id": report_id,
            **identity,
            "accounting": {
                "physical_record_count": imported["physical_record_count"],
                "accepted_conversation_count": imported["accepted_conversation_count"],
                "rejected_record_count": imported["rejected_record_count"],
            },
            "eval_proposals": [
                {
                    "proposal_id": proposal_id,
                    "proposal_state": "PROPOSED",
                    "name": "Synthetic grounded proposal",
                }
            ],
            "judgment": {
                "state": "JUDGMENT_REQUIRED",
                "required_review_item_count": 1,
                "verdict": "NOT_ESTABLISHED",
            },
        }
        queue = {
            "artifact_kind": "review_queue_v0",
            "schema_version": 0,
            "report_id": report_id,
            "items": [
                {
                    "item_id": item_id,
                    "item_hash": item_hash,
                    "item_kind": "EVAL_PROPOSAL",
                    "proposal_id": proposal_id,
                    "allowed_decisions": ["TRACK", "EDIT", "DEFER"],
                }
            ],
        }
        run = {
            **identity,
            "owner_subject": owner_subject,
            "report_id": report_id,
            "state": "COMPLETED",
            "judgment_state": "JUDGMENT_REQUIRED",
        }
        self.runs[run_id] = run
        self.reports[report_id] = {**report, "owner_subject": owner_subject}
        self.queues[report_id] = queue
        self.rulings[report_id] = []
        self._runs_by_import[import_id] = run_id
        for conversation_id in imported["conversation_ids"]:
            conversation = self.conversations[conversation_id]
            self.report_conversations[(report_id, conversation["trace_id"])] = {
                **conversation,
                "report_id": report_id,
                "run_id": run_id,
                "evidence_state": "OBSERVED",
            }
        return self._public(run)

    def list_features(self, owner_subject: str) -> list[dict[str, str]]:
        return [
            {"feature_key": "TRACE_INGESTION", "state": "AVAILABLE"},
            {"feature_key": "CONVERSATION_VIEWER", "state": "AVAILABLE"},
            {
                "feature_key": "ANALYSIS",
                "state": self.analysis_feature_states[owner_subject],
            },
        ]

    def request_feature_access(
        self, owner_subject: str, feature_key: str
    ) -> dict[str, str]:
        if feature_key != "ANALYSIS":
            raise AssertionError("only ANALYSIS is in this acceptance slice")
        self.analysis_feature_states[owner_subject] = "REQUESTED"
        return {"feature_key": feature_key, "state": "REQUESTED"}

    def list_agent_analysis_runs(
        self, owner_subject: str, agent_id: str
    ) -> list[dict[str, Any]]:
        self._owned(self.agents, owner_subject, agent_id, "agent")
        return [
            self._public(run)
            for run in self.runs.values()
            if run["owner_subject"] == owner_subject and run["agent_id"] == agent_id
        ]

    def get_owned_report(self, owner_subject: str, report_id: str) -> dict[str, Any]:
        return self._public(
            self._owned(self.reports, owner_subject, report_id, "report")
        )

    def get_owned_review_state(
        self, owner_subject: str, report_id: str
    ) -> dict[str, Any]:
        self._owned(self.reports, owner_subject, report_id, "report")
        current = self.rulings[report_id]
        return {
            "artifact_kind": "trace_to_eval_review_state_v0",
            "schema_version": 0,
            "report_id": report_id,
            "judgment_state": ("JUDGMENT_COMPLETE" if current else "JUDGMENT_REQUIRED"),
            "review_queue": self.queues[report_id],
            "current_rulings": list(current),
        }

    def append_owned_ruling(
        self, owner_subject: str, report_id: str, ruling: dict[str, Any]
    ) -> dict[str, Any]:
        self._owned(self.reports, owner_subject, report_id, "report")
        item = self.queues[report_id]["items"][0]
        if (
            ruling.get("item_id") != item["item_id"]
            or ruling.get("item_hash") != item["item_hash"]
        ):
            raise ValueError("stale or mismatched review item")
        accepted = {
            **ruling,
            "artifact_kind": "human_ruling_v0",
            "ruling_id": self._id("ruling"),
        }
        self.rulings[report_id].append(accepted)
        return accepted

    # Existing local TraceToEvalPort methods let the current routes expose why the
    # authenticated bridge is unsafe: no owner subject reaches this boundary.
    def run(self, *_: Any, **__: Any) -> dict[str, Any]:
        raise AssertionError("self-serve upload must drive the analysis bridge")

    def get_report(self, report_id: str) -> dict[str, Any]:
        return self._public(self.reports[report_id])

    def get_review_state(self, report_id: str) -> dict[str, Any]:
        owner = str(self.reports[report_id]["owner_subject"])
        return self.get_owned_review_state(owner, report_id)

    def append_ruling(self, report_id: str, ruling: dict[str, Any]) -> dict[str, Any]:
        owner = str(self.reports[report_id]["owner_subject"])
        return self.append_owned_ruling(owner, report_id, ruling)

    def get_owned_conversation(
        self, owner_subject: str, report_id: str, trace_id: str
    ) -> dict[str, Any]:
        self._owned(self.reports, owner_subject, report_id, "report")
        return self._public(self.report_conversations[(report_id, trace_id)])

    def get_conversation(self, first: str, second: str) -> dict[str, Any]:
        if first in self.reports:
            return self._public(self.report_conversations[(first, second)])
        return self._public(
            self._owned(self.conversations, first, second, "conversation")
        )

    def list_agent_imports(
        self, owner_subject: str, agent_id: str
    ) -> list[dict[str, Any]]:
        self._owned(self.agents, owner_subject, agent_id, "agent")
        return [
            self._public(imported)
            for imported in self.imports.values()
            if imported["owner_subject"] == owner_subject
            and imported["agent_id"] == agent_id
        ]

    def get_import(self, owner_subject: str, import_id: str) -> dict[str, Any]:
        return self._public(
            self._owned(self.imports, owner_subject, import_id, "import")
        )

    def list_import_conversations(self, *_: Any) -> list[dict[str, Any]]:
        return []

    def list_import_rejections(self, *_: Any) -> list[dict[str, Any]]:
        return []

    @staticmethod
    def _public(value: dict[str, Any]) -> dict[str, Any]:
        return {
            key: item
            for key, item in value.items()
            if key not in {"owner_subject", "records", "conversation_ids"}
        }

    @staticmethod
    def _owned(
        rows: dict[str, dict[str, Any]],
        owner_subject: str,
        resource_id: str,
        resource_kind: str,
    ) -> dict[str, Any]:
        value = rows.get(resource_id)
        if value is None or value["owner_subject"] != owner_subject:
            raise ResourceNotFound(resource_kind, resource_id)
        return value


def _authenticate(token: str | None) -> str | None:
    return {
        OWNER_ONE: SUBJECT_ONE,
        OWNER_TWO: SUBJECT_TWO,
    }.get(token or "")


def _headers(owner: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {owner}"}


def _trace(trace_id: str) -> bytes:
    value = {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "CUSTOMER_AUTHORIZED_TRACE_DATA",
        "trace_id": trace_id,
        "source_trace_id": f"source-{trace_id}",
        "events": [
            {
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": "Synthetic request.",
            },
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "Synthetic answer.",
                "is_final": True,
            },
        ],
    }
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode() + b"\n"


@pytest.fixture
def platform_client() -> tuple[_SelfServeAnalysisPlatform, TestClient]:
    platform = _SelfServeAnalysisPlatform()
    unused = _UnusedPort()
    app = create_app(
        reads=unused,
        imports=unused,
        runs=unused,
        readiness=lambda: True,
        self_serve=platform,
        authenticate=_authenticate,
        feature_entitlements=platform,
        trace_to_eval=platform,
    )
    with TestClient(app) as client:
        yield platform, client


def _create_agent(client: TestClient, owner: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/agents", headers=_headers(owner), json={"display_name": name}
    )
    assert response.status_code == 201, response.text
    return response.json()


def _upload(
    client: TestClient,
    owner: str,
    agent_id: str,
    trace_id: str,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/agents/{agent_id}/imports",
        headers={
            **_headers(owner),
            "Idempotency-Key": idempotency_key or f"upload-{trace_id}",
        },
        data={"owner_attested": "true"},
        files={
            "file": (
                "traces.jsonl",
                _trace(trace_id),
                "application/x-ndjson",
            )
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_fresh_upload_automatically_returns_agent_bound_analysis_run(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    me = client.get("/api/v1/me", headers=_headers(OWNER_ONE)).json()
    agent = _create_agent(client, OWNER_ONE, "Synthetic support agent")
    uploaded = _upload(client, OWNER_ONE, agent["agent_id"], "fresh-trace")

    assert uploaded["workspace_id"] == me["workspace"]["workspace_id"]
    assert uploaded["agent_id"] == agent["agent_id"]
    assert uploaded["analysis"]["feature_state"] == "AVAILABLE"
    analysis = uploaded["analysis"]["run"]
    assert analysis["import_id"] == uploaded["import_id"]
    assert analysis["workspace_id"] == uploaded["workspace_id"]
    assert analysis["agent_id"] == agent["agent_id"]
    assert analysis["state"] == "COMPLETED"
    assert analysis["judgment_state"] == "JUDGMENT_REQUIRED"
    assert analysis["report_id"].startswith("sha256:")
    assert len(platform.runs) == 1


@pytest.mark.parametrize("feature_state", ["LOCKED", "REQUESTED"])
def test_upload_types_unavailable_analysis_without_starting_a_run(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
    feature_state: str,
) -> None:
    platform, client = platform_client
    platform.analysis_feature_states[SUBJECT_ONE] = feature_state
    agent = _create_agent(client, OWNER_ONE, "Gated analysis agent")

    uploaded = _upload(client, OWNER_ONE, agent["agent_id"], "gated-trace")

    assert uploaded["analysis"] == {"feature_state": feature_state, "run": None}
    assert platform.runs == {}


def test_same_upload_key_converges_on_one_import_and_one_analysis_run(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    agent = _create_agent(client, OWNER_ONE, "Replay-safe agent")

    first = _upload(
        client,
        OWNER_ONE,
        agent["agent_id"],
        "replayed-trace",
        idempotency_key="same-upload",
    )
    second = _upload(
        client,
        OWNER_ONE,
        agent["agent_id"],
        "replayed-trace",
        idempotency_key="same-upload",
    )

    assert second == first
    assert len(platform.imports) == 1
    assert len(platform.runs) == 1
    assert first["analysis"]["run"]["import_id"] == first["import_id"]


def test_same_upload_key_is_scoped_to_agent_and_never_cross_binds_imports(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    first_agent = _create_agent(client, OWNER_ONE, "First replay scope")
    second_agent = _create_agent(client, OWNER_ONE, "Second replay scope")

    first = _upload(
        client,
        OWNER_ONE,
        first_agent["agent_id"],
        "first-agent-trace",
        idempotency_key="shared-client-key",
    )
    second = _upload(
        client,
        OWNER_ONE,
        second_agent["agent_id"],
        "second-agent-trace",
        idempotency_key="shared-client-key",
    )

    assert first["import_id"] != second["import_id"]
    assert first["analysis"]["run"]["agent_id"] == first_agent["agent_id"]
    assert second["analysis"]["run"]["agent_id"] == second_agent["agent_id"]
    assert len(platform.runs) == 2


def test_analysis_history_is_agent_scoped_and_projects_canonical_report_identity(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    first = _create_agent(client, OWNER_ONE, "First agent")
    second = _create_agent(client, OWNER_ONE, "Second agent")
    first_import = platform.create_import(
        "oidc|analysis-owner-one",
        first["agent_id"],
        filename="first.jsonl",
        content_type="application/x-ndjson",
        payload=_trace("first-trace"),
        owner_attested=True,
        idempotency_key="first",
    )
    second_import = platform.create_import(
        "oidc|analysis-owner-one",
        second["agent_id"],
        filename="second.jsonl",
        content_type="application/x-ndjson",
        payload=_trace("second-trace"),
        owner_attested=True,
        idempotency_key="second",
    )
    first_run = platform.start_analysis_for_import(
        "oidc|analysis-owner-one", first["agent_id"], first_import["import_id"]
    )
    platform.start_analysis_for_import(
        "oidc|analysis-owner-one", second["agent_id"], second_import["import_id"]
    )

    response = client.get(
        f"/api/v1/agents/{first['agent_id']}/analysis-runs",
        headers=_headers(OWNER_ONE),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "schema_version": 1,
        "analysis_runs": [first_run],
    }
    report = client.get(
        f"/api/v1/trace-to-eval/reports/{first_run['report_id']}",
        headers=_headers(OWNER_ONE),
    )
    assert report.status_code == 200, report.text
    assert report.json()["report_id"] == first_run["report_id"]
    assert report.json()["run_id"] == first_run["run_id"]
    assert report.json()["agent_id"] == first["agent_id"]
    assert report.json()["judgment"] == {
        "state": "JUDGMENT_REQUIRED",
        "required_review_item_count": 1,
        "verdict": "NOT_ESTABLISHED",
    }


def test_review_ruling_persists_but_never_mutates_canonical_report(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    agent = _create_agent(client, OWNER_ONE, "Review agent")
    imported = platform.create_import(
        "oidc|analysis-owner-one",
        agent["agent_id"],
        filename="review.jsonl",
        content_type="application/x-ndjson",
        payload=_trace("review-trace"),
        owner_attested=True,
        idempotency_key="review",
    )
    run = platform.start_analysis_for_import(
        "oidc|analysis-owner-one", agent["agent_id"], imported["import_id"]
    )
    report_path = f"/api/v1/trace-to-eval/reports/{run['report_id']}"
    before = client.get(report_path, headers=_headers(OWNER_ONE)).json()
    review_path = f"{report_path}/review"
    pending = client.get(review_path, headers=_headers(OWNER_ONE))
    assert pending.status_code == 200, pending.text
    assert pending.json()["judgment_state"] == "JUDGMENT_REQUIRED"
    item = pending.json()["review_queue"]["items"][0]

    accepted = client.post(
        f"{report_path}/rulings",
        headers=_headers(OWNER_ONE),
        json={
            "artifact_kind": "human_ruling_v0",
            "schema_version": 0,
            "report_id": run["report_id"],
            "item_id": item["item_id"],
            "item_hash": item["item_hash"],
            "decision": "TRACK",
            "edited_text": None,
            "reviewer_id": "synthetic-owner",
            "ruled_at": "2026-08-07T03:00:00Z",
            "supersedes_ruling_id": None,
        },
    )
    assert accepted.status_code == 201, accepted.text
    refreshed = client.get(review_path, headers=_headers(OWNER_ONE))
    assert refreshed.json()["judgment_state"] == "JUDGMENT_COMPLETE"
    assert refreshed.json()["current_rulings"] == [accepted.json()]
    assert client.get(report_path, headers=_headers(OWNER_ONE)).json() == before


def test_stale_review_item_hash_is_rejected_without_appending_to_ledger(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    agent = _create_agent(client, OWNER_ONE, "Stale-ruling agent")
    imported = platform.create_import(
        SUBJECT_ONE,
        agent["agent_id"],
        filename="stale.jsonl",
        content_type="application/x-ndjson",
        payload=_trace("stale-trace"),
        owner_attested=True,
        idempotency_key="stale",
    )
    run = platform.start_analysis_for_import(
        SUBJECT_ONE, agent["agent_id"], imported["import_id"]
    )
    item = platform.queues[run["report_id"]]["items"][0]

    response = client.post(
        f"/api/v1/trace-to-eval/reports/{run['report_id']}/rulings",
        headers=_headers(OWNER_ONE),
        json={
            "report_id": run["report_id"],
            "item_id": item["item_id"],
            "item_hash": "sha256:stale-client-view",
            "decision": "TRACK",
        },
    )

    assert response.status_code == 422, response.text
    assert platform.rulings[run["report_id"]] == []


def test_analysis_conversation_evidence_is_report_bound_and_owner_isolated(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    agent = _create_agent(client, OWNER_ONE, "Evidence viewer agent")
    imported = platform.create_import(
        SUBJECT_ONE,
        agent["agent_id"],
        filename="evidence.jsonl",
        content_type="application/x-ndjson",
        payload=_trace("evidence-trace"),
        owner_attested=True,
        idempotency_key="evidence",
    )
    run = platform.start_analysis_for_import(
        SUBJECT_ONE, agent["agent_id"], imported["import_id"]
    )
    path = (
        f"/api/v1/trace-to-eval/reports/{run['report_id']}/conversations/evidence-trace"
    )

    evidence = client.get(path, headers=_headers(OWNER_ONE))
    assert evidence.status_code == 200, evidence.text
    assert evidence.json()["report_id"] == run["report_id"]
    assert evidence.json()["run_id"] == run["run_id"]
    assert evidence.json()["agent_id"] == agent["agent_id"]
    assert evidence.json()["import_id"] == imported["import_id"]
    assert evidence.json()["trace_id"] == "evidence-trace"
    assert evidence.json()["evidence_state"] == "OBSERVED"
    assert client.get(path).status_code == 401
    assert client.get(path, headers=_headers(OWNER_TWO)).status_code == 404


def test_analysis_report_history_and_review_are_owner_isolated(
    platform_client: tuple[_SelfServeAnalysisPlatform, TestClient],
) -> None:
    platform, client = platform_client
    agent = _create_agent(client, OWNER_ONE, "Private analysis agent")
    imported = platform.create_import(
        "oidc|analysis-owner-one",
        agent["agent_id"],
        filename="private.jsonl",
        content_type="application/x-ndjson",
        payload=_trace("private-trace"),
        owner_attested=True,
        idempotency_key="private",
    )
    run = platform.start_analysis_for_import(
        "oidc|analysis-owner-one", agent["agent_id"], imported["import_id"]
    )
    paths = [
        f"/api/v1/agents/{agent['agent_id']}/analysis-runs",
        f"/api/v1/trace-to-eval/reports/{run['report_id']}",
        f"/api/v1/trace-to-eval/reports/{run['report_id']}/review",
    ]
    for path in paths:
        assert client.get(path).status_code == 401
        assert client.get(path, headers=_headers(OWNER_TWO)).status_code == 404

    item = platform.queues[run["report_id"]]["items"][0]
    forbidden = client.post(
        f"/api/v1/trace-to-eval/reports/{run['report_id']}/rulings",
        headers=_headers(OWNER_TWO),
        json={
            "report_id": run["report_id"],
            "item_id": item["item_id"],
            "item_hash": item["item_hash"],
            "decision": "TRACK",
        },
    )
    assert forbidden.status_code == 404
    assert platform.rulings[run["report_id"]] == []
