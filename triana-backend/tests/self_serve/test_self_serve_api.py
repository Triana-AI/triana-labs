"""Black-box acceptance contract for the minimal self-serve HTTP loop."""

# ruff: noqa: S101 - assertions are the acceptance-test contract.

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from triana_backend.api.app import create_app
from triana_backend.api.contracts import ResourceNotFound

OWNER_ONE = "test-owner-one-token"
OWNER_TWO = "test-owner-two-token"


class _UnusedPort:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"legacy port unexpectedly used: {name}")


class _InMemorySelfServePort:
    """Purpose-built double for the HTTP contract, not a production adapter."""

    def __init__(self) -> None:
        self.workspaces: dict[str, str] = {}
        self.agents: dict[str, dict[str, Any]] = {}
        self.imports: dict[str, dict[str, Any]] = {}
        self.conversations: dict[str, dict[str, Any]] = {}

    def get_or_create_me(self, owner_subject: str) -> dict[str, Any]:
        workspace_id = self.workspaces.setdefault(owner_subject, f"ws-{uuid4()}")
        return {
            "owner_subject": owner_subject,
            "workspace": {"workspace_id": workspace_id},
        }

    def create_agent(self, owner_subject: str, display_name: str) -> dict[str, Any]:
        self.get_or_create_me(owner_subject)
        agent_id = f"agent-{uuid4()}"
        agent = {
            "agent_id": agent_id,
            "owner_subject": owner_subject,
            "display_name": display_name,
            "default_version": {"version_key": "default"},
        }
        self.agents[agent_id] = agent
        return dict(agent)

    def list_agents(self, owner_subject: str) -> list[dict[str, Any]]:
        return [
            _public(row)
            for row in self.agents.values()
            if row["owner_subject"] == owner_subject
        ]

    def get_agent(self, owner_subject: str, agent_id: str) -> dict[str, Any]:
        return _public(self._owned(self.agents, owner_subject, agent_id, "agent"))

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
        del filename, content_type, owner_attested, idempotency_key
        self._owned(self.agents, owner_subject, agent_id, "agent")
        import_id = f"import-{uuid4()}"
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(payload.splitlines(), start=1):
            try:
                trace = json.loads(raw_line)
            except json.JSONDecodeError:
                rejected.append(
                    {
                        "line_number": line_number,
                        "code": "MALFORMED_JSON",
                        "json_pointer": "",
                        "safe_message": "Input line is not valid JSON.",
                    }
                )
                continue
            conversation_id = f"conversation-{uuid4()}"
            conversation = {
                "conversation_id": conversation_id,
                "owner_subject": owner_subject,
                "import_id": import_id,
                "trace_id": trace["trace_id"],
                "events": trace["events"],
            }
            self.conversations[conversation_id] = conversation
            accepted.append(conversation)
        status = "COMPLETED" if not rejected else "COMPLETED_WITH_REJECTIONS"
        imported = {
            "import_id": import_id,
            "owner_subject": owner_subject,
            "agent_id": agent_id,
            "status": status,
            "physical_record_count": len(accepted) + len(rejected),
            "accepted_conversation_count": len(accepted),
            "rejected_record_count": len(rejected),
            "rejections": rejected,
        }
        self.imports[import_id] = imported
        return _public(imported)

    def list_agent_imports(
        self, owner_subject: str, agent_id: str
    ) -> list[dict[str, Any]]:
        self._owned(self.agents, owner_subject, agent_id, "agent")
        return [
            _public(row) for row in self.imports.values() if row["agent_id"] == agent_id
        ]

    def get_import(self, owner_subject: str, import_id: str) -> dict[str, Any]:
        return _public(self._owned(self.imports, owner_subject, import_id, "import"))

    def list_import_conversations(
        self, owner_subject: str, import_id: str
    ) -> list[dict[str, Any]]:
        self._owned(self.imports, owner_subject, import_id, "import")
        return [
            _public(row)
            for row in self.conversations.values()
            if row["import_id"] == import_id
        ]

    def list_import_rejections(
        self, owner_subject: str, import_id: str
    ) -> list[dict[str, Any]]:
        row = self._owned(self.imports, owner_subject, import_id, "import")
        return list(row["rejections"])

    def get_conversation(
        self, owner_subject: str, conversation_id: str
    ) -> dict[str, Any]:
        row = self._owned(
            self.conversations, owner_subject, conversation_id, "conversation"
        )
        return _public(row)

    @staticmethod
    def _owned(
        rows: dict[str, dict[str, Any]],
        owner_subject: str,
        resource_id: str,
        resource_kind: str,
    ) -> dict[str, Any]:
        row = rows.get(resource_id)
        if row is None or row["owner_subject"] != owner_subject:
            raise ResourceNotFound(resource_kind, resource_id)
        return row


def _public(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "owner_subject"}


def _authenticate(bearer_token: str | None) -> str | None:
    return {
        OWNER_ONE: "oidc|owner-one",
        OWNER_TWO: "oidc|owner-two",
    }.get(bearer_token or "")


@pytest.fixture
def client() -> TestClient:
    unused = _UnusedPort()
    app = create_app(
        reads=unused,
        imports=unused,
        runs=unused,
        readiness=lambda: True,
        self_serve=_InMemorySelfServePort(),
        authenticate=_authenticate,
    )
    with TestClient(app) as test_client:
        yield test_client


def _headers(token: str, *, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def _trace(trace_id: str, question: str, answer: str) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "CUSTOMER_AUTHORIZED_TRACE_DATA",
        "trace_id": trace_id,
        "source_trace_id": f"source-{trace_id}",
        "events": [
            {
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": question,
            },
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": answer,
                "is_final": True,
            },
        ],
    }


def _jsonl(*records: dict[str, Any]) -> bytes:
    return b"".join(
        json.dumps(record, separators=(",", ":"), sort_keys=True).encode() + b"\n"
        for record in records
    )


def _create_agent(client: TestClient, token: str, name: str = "Support agent") -> str:
    response = client.post(
        "/api/v1/agents",
        headers=_headers(token),
        json={"display_name": name},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["display_name"] == name
    assert body["default_version"]["version_key"] == "default"
    return str(body["agent_id"])


def _upload(
    client: TestClient,
    token: str,
    agent_id: str,
    payload: bytes,
    *,
    idempotency_key: str,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/agents/{agent_id}/imports",
        headers=_headers(token, idempotency_key=idempotency_key),
        data={"owner_attested": "true"},
        files={"file": ("traces.jsonl", payload, "application/x-ndjson")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["import_id"]
    return body


def test_owner_creates_agent_uploads_and_reads_two_conversations(
    client: TestClient,
) -> None:
    me = client.get("/api/v1/me", headers=_headers(OWNER_ONE))
    assert me.status_code == 200
    assert me.json()["workspace"]["workspace_id"]

    agent_id = _create_agent(client, OWNER_ONE)
    summary = _upload(
        client,
        OWNER_ONE,
        agent_id,
        _jsonl(
            _trace("conversation-one", "Where is order 1?", "It has shipped."),
            _trace("conversation-two", "Where is order 2?", "It is processing."),
        ),
        idempotency_key="upload-two-valid",
    )

    assert summary["status"] == "COMPLETED"
    assert summary["physical_record_count"] == 2
    assert summary["accepted_conversation_count"] == 2
    assert summary["rejected_record_count"] == 0

    listed = client.get(
        f"/api/v1/imports/{summary['import_id']}/conversations",
        headers=_headers(OWNER_ONE),
    )
    assert listed.status_code == 200, listed.text
    conversations = listed.json()["conversations"]
    assert [item["trace_id"] for item in conversations] == [
        "conversation-one",
        "conversation-two",
    ]

    projected = [
        client.get(
            f"/api/v1/conversations/{item['conversation_id']}",
            headers=_headers(OWNER_ONE),
        )
        for item in conversations
    ]
    assert all(response.status_code == 200 for response in projected)
    assert [response.json()["trace_id"] for response in projected] == [
        "conversation-one",
        "conversation-two",
    ]
    assert projected[0].json()["events"][0] == {
        "sequence": 0,
        "event_kind": "USER_MESSAGE",
        "content": "Where is order 1?",
    }


def test_mixed_upload_has_exact_safe_line_accounting(client: TestClient) -> None:
    agent_id = _create_agent(client, OWNER_ONE)
    rejected_content = "do-not-return-this-rejected-content"
    payload = _jsonl(_trace("accepted", "Valid question", "Valid answer"))
    payload += f'{{"private_value":"{rejected_content}"\n'.encode()

    summary = _upload(
        client,
        OWNER_ONE,
        agent_id,
        payload,
        idempotency_key="upload-mixed",
    )

    assert summary["status"] == "COMPLETED_WITH_REJECTIONS"
    assert summary["physical_record_count"] == 2
    assert summary["accepted_conversation_count"] == 1
    assert summary["rejected_record_count"] == 1

    response = client.get(
        f"/api/v1/imports/{summary['import_id']}/rejections",
        headers=_headers(OWNER_ONE),
    )
    assert response.status_code == 200, response.text
    assert response.json()["rejections"] == [
        {
            "line_number": 2,
            "code": "MALFORMED_JSON",
            "json_pointer": "",
            "safe_message": "Input line is not valid JSON.",
        }
    ]
    assert rejected_content not in response.text
    assert rejected_content not in json.dumps(summary)


def test_second_owner_cannot_discover_or_read_first_owners_resources(
    client: TestClient,
) -> None:
    agent_id = _create_agent(client, OWNER_ONE, "Private agent")
    summary = _upload(
        client,
        OWNER_ONE,
        agent_id,
        _jsonl(_trace("private-conversation", "Private question", "Private answer")),
        idempotency_key="upload-private",
    )
    owner_list = client.get(
        f"/api/v1/imports/{summary['import_id']}/conversations",
        headers=_headers(OWNER_ONE),
    )
    conversation_id = owner_list.json()["conversations"][0]["conversation_id"]

    listed = client.get("/api/v1/agents", headers=_headers(OWNER_TWO))
    assert listed.status_code == 200
    assert listed.json()["agents"] == []

    protected_paths = (
        f"/api/v1/agents/{agent_id}",
        f"/api/v1/agents/{agent_id}/imports",
        f"/api/v1/imports/{summary['import_id']}",
        f"/api/v1/imports/{summary['import_id']}/conversations",
        f"/api/v1/imports/{summary['import_id']}/rejections",
        f"/api/v1/conversations/{conversation_id}",
    )
    for path in protected_paths:
        response = client.get(path, headers=_headers(OWNER_TWO))
        assert response.status_code == 404, (path, response.text)

    assert client.get("/api/v1/me").status_code == 401
