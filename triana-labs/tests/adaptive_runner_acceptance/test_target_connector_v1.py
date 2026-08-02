"""Black-box acceptance for the owner-approved LABS-05 Target Connector V1."""

from __future__ import annotations

import ast
import http.client
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    CapturePublisher,
    Clock,
    FixtureLoader,
    Simulator,
    SourceVerifier,
    api,
    config_value,
    executable_config_value,
    jsonl,
    write_inputs,
)

TARGET_SECRET = "PRIVATE_TARGET_CONNECTOR_SECRET"


def _fake_module() -> Any:
    path = (
        Path(__file__).resolve().parents[1]
        / "adaptive_runner_fixtures"
        / "fake_http_target.py"
    )
    spec = importlib.util.spec_from_file_location("labs05_fake_http_target", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _operation(
    method: str,
    path_template: str,
    constant_json: dict[str, Any],
    assignments: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    assignments = assignments or []
    return {
        "assignments": [
            {"pointer": pointer, "source": source} for source, pointer in assignments
        ],
        "constant_json": constant_json,
        "method": method,
        "path_template": path_template,
    }


def _http_config(
    base_url: str,
    *,
    stateless: bool = False,
    include_tools: bool = True,
    include_usage: bool = False,
    auth: bool = False,
) -> dict[str, Any]:
    value = config_value()
    if stateless:
        session = {"mode": "STATELESS_TRANSCRIPT"}
        turn = {
            "operation": _operation(
                "POST",
                "/v2/respond",
                {"payload": {"dialog": [], "latest": ""}},
                [("transcript", "/payload/dialog"), ("user_turn", "/payload/latest")],
            ),
            "response_mapping": {
                "assistant_content_pointer": "/result/agent/text",
                "error_pointer": None,
                "internal_usage": {
                    "http_exchanges_pointer": "/meter/calls",
                    "input_tokens_pointer": "/meter/in",
                    "output_tokens_pointer": "/meter/out",
                }
                if include_usage
                else None,
                "target_status_pointer": None,
                "termination_pointer": "/result/ended",
                "tool_events": {
                    "arguments_pointer": "/arguments",
                    "list_pointer": "/result/events",
                    "name_pointer": "/tool",
                    "status_pointer": "/status",
                }
                if include_tools
                else None,
            },
        }
        state = "STATELESS_TRANSCRIPT"
        target_http = 9
    else:
        session = {
            "close": _operation("DELETE", "/sessions/{session_id}", {}),
            "create": _operation(
                "POST", "/sessions", {"client_id": "synthetic-client-techcorp"}
            ),
            "mode": "REMOTE_SESSION",
            "session_id_pointer": "/session_id",
        }
        response_mapping: dict[str, Any] = {
            "assistant_content_pointer": "/response",
            "error_pointer": "/error",
            "internal_usage": {
                "cost_usd_pointer": "/usage/cost_usd",
                "http_exchanges_pointer": "/usage/http_exchanges",
                "input_tokens_pointer": "/usage/input_tokens",
                "model_exchanges_pointer": "/usage/model_exchanges",
                "output_tokens_pointer": "/usage/output_tokens",
            }
            if include_usage
            else None,
            "target_status_pointer": None,
            "termination_pointer": None,
            "tool_events": {
                "arguments_pointer": "/args",
                "list_pointer": "/tool_calls",
                "name_pointer": "/name",
                "status_pointer": None,
            }
            if include_tools
            else None,
        }
        turn = {
            "operation": _operation(
                "POST",
                "/sessions/{session_id}/chat",
                {"client_id": "synthetic-client-techcorp", "message": ""},
                [("user_turn", "/message")],
            ),
            "response_mapping": response_mapping,
        }
        state = "TARGET_GLOBAL_STATE_UNKNOWN"
        target_http = 15
    value["target"] = {
        "auth": {
            "env_name": "LABS05_TARGET_API_KEY",
            "header_name": "X-Synthetic-Target-Key",
            "kind": "HEADER_ENV",
        }
        if auth
        else {"kind": "NONE"},
        "allowed_host": "127.0.0.1",
        "base_url": base_url,
        "connector_id": "synthetic-hrai-http-v1"
        if not stateless
        else "synthetic-stateless-v1",
        "connector_kind": "HTTP_JSON_V1",
        "data_class": "SYNTHETIC_LOCAL_TARGET",
        "session": session,
        "state_isolation": state,
        "target_identity": {
            "agent_id": "HRAI_RECRUITER_CHAT_REACT"
            if not stateless
            else "SYNTHETIC_TRANSCRIPT_AGENT",
            "model": None,
            "prompt": None,
            "protocol": "HRAI_FASTAPI_SESSIONS_V1"
            if not stateless
            else "STATELESS_DIALOG_V2",
            "tools": None,
            "version": "728f6c5058efe40a16e2aecc9b528b3353f4df4f"
            if not stateless
            else "2",
        },
        "timeout_seconds": 5,
        "turn": turn,
    }
    value.pop("world", None)
    value["budget"] = {
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
    return value


def _executable_config() -> dict[str, Any]:
    return executable_config_value()


class _MustNotStart:
    def __init__(self) -> None:
        self.launches: list[Any] = []

    def start(self, launch: Any) -> Any:
        self.launches.append(launch)
        raise AssertionError(
            "invalid connector config must refuse before target egress"
        )


class _RecordingSession:
    def __init__(self, session: Any) -> None:
        self.session = session
        self.responses: list[dict[str, Any]] = []

    def exchange(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self.session.exchange(request)
        self.responses.append(response)
        return response

    def terminate(self) -> None:
        self.session.terminate()


class _RecordingFactory:
    def __init__(self, factory: Any) -> None:
        self.factory = factory
        self.sessions: list[_RecordingSession] = []

    def start(self, launch: Any) -> _RecordingSession:
        session = _RecordingSession(self.factory.start(launch))
        self.sessions.append(session)
        return session


def _run_http(
    tmp_path: Path,
    config: dict[str, Any],
    *,
    auth: bool = False,
    factory: Any = None,
) -> Any:
    module = api()
    inputs = write_inputs(tmp_path, config=config)
    simulator = Simulator(module)
    publisher = CapturePublisher()
    verifier = SourceVerifier(module)
    active_factory = factory or module.HttpJsonTargetFactory()
    environ = {**ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"}
    if auth:
        environ["LABS05_TARGET_API_KEY"] = TARGET_SECRET
    result = module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        simulator=simulator,
        target_factory=active_factory,
        clock=Clock(),
        environ=environ,
        publisher=publisher,
        source_verifier=verifier,
        case_loader=FixtureLoader(module),
    )
    return SimpleNamespace(
        factory=active_factory,
        inputs=inputs,
        module=module,
        publisher=publisher,
        result=result,
        simulator=simulator,
        verifier=verifier,
    )


def _gaps(run: Any) -> set[str]:
    return {
        item["reason_code"] for item in jsonl(run.publisher.artifacts["gaps.jsonl"])
    }


def test_local_http_fake_exposes_hrai_and_non_hrai_surfaces() -> None:
    fake = _fake_module()
    with fake.serve() as server:
        connection = http.client.HTTPConnection(
            "127.0.0.1", int(server.base_url.rsplit(":", 1)[1]), timeout=2
        )
        connection.request(
            "POST",
            "/sessions",
            body=b'{"client_id":"synthetic-client"}',
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        assert response.status == 201
        assert json.loads(response.read())["session_id"] == "synthetic-session-1"
        connection.close()
    assert [(item["method"], item["path"]) for item in server.requests] == [
        ("POST", "/sessions")
    ]


def test_hrai_http_remote_sessions_preserve_continuity_and_close_once(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        run = _run_http(tmp_path, _http_config(server.base_url))
    creates = [item for item in server.requests if item["path"] == "/sessions"]
    chats = [item for item in server.requests if item["path"].endswith("/chat")]
    closes = [item for item in server.requests if item["method"] == "DELETE"]
    assert (len(creates), len(chats), len(closes)) == (3, 9, 3)
    for ordinal in range(1, 4):
        session = f"synthetic-session-{ordinal}"
        assert sum(f"/sessions/{session}/chat" == item["path"] for item in chats) == 3
        assert sum(f"/sessions/{session}" == item["path"] for item in closes) == 1
    assert run.result.target_http_exchange_count == 15
    assert run.result.all_http_exchange_count == 21
    assert not run.verifier.calls


def test_non_hrai_stateless_connector_replays_complete_transcript(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        run = _run_http(tmp_path, _http_config(server.base_url, stateless=True))
    assert {(item["method"], item["path"]) for item in server.requests} == {
        ("POST", "/v2/respond")
    }
    lengths = [len(item["body"]["payload"]["dialog"]) for item in server.requests]
    assert lengths == [1, 3, 5, 1, 3, 5, 1, 3, 5]
    assert run.result.target_http_exchange_count == 9
    assert run.result.all_http_exchange_count == 15
    assert "TARGET_STATE_ISOLATION_UNAVAILABLE" not in _gaps(run)


@pytest.mark.parametrize(
    ("mode", "expected_gap"),
    [
        ("fail_first_chat", "TARGET_HTTP_ERROR"),
        ("close_failure", "TARGET_SESSION_CLOSE_FAILED"),
    ],
)
def test_remote_session_partial_failure_still_closes_once_and_continues(
    tmp_path: Path, mode: str, expected_gap: str
) -> None:
    fake = _fake_module()
    with fake.serve(mode=mode) as server:
        run = _run_http(tmp_path, _http_config(server.base_url))
    creates = [item for item in server.requests if item["path"] == "/sessions"]
    closes = [item for item in server.requests if item["method"] == "DELETE"]
    assert len(creates) == len(closes) == 3
    assert len({item["path"] for item in closes}) == 3
    if mode == "fail_first_chat":
        assert (
            sum(
                item["path"] == "/sessions/synthetic-session-1/chat"
                for item in server.requests
            )
            == 1
        )
    assert expected_gap in _gaps(run)
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    assert attempts[0]["status"] == "PARTIAL"
    assert [item["status"] for item in attempts[1:]] == ["VALID", "VALID"]


@pytest.mark.parametrize(
    "mode", ["create_non_2xx", "create_non_json_500", "create_missing_id"]
)
def test_failed_session_create_is_counted_without_closing_an_unopened_session(
    tmp_path: Path, mode: str
) -> None:
    fake = _fake_module()
    with fake.serve(mode=mode) as server:
        run = _run_http(tmp_path, _http_config(server.base_url))
    creates = [item for item in server.requests if item["path"] == "/sessions"]
    closes = [item for item in server.requests if item["method"] == "DELETE"]
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    assert len(creates) == 3
    assert not any(
        item["path"] == "/sessions/synthetic-session-1/chat" for item in server.requests
    )
    assert [item["path"] for item in closes] == [
        "/sessions/synthetic-session-2",
        "/sessions/synthetic-session-3",
    ]
    assert attempts[0]["target_http_exchange_count"] == 1
    assert attempts[0]["termination_reason"] == "TARGET_SESSION_CREATE_FAILED"
    assert attempts[0]["gap_codes"] == ["TARGET_SESSION_CREATE_FAILED"]
    assert [item["status"] for item in attempts[1:]] == ["VALID", "VALID"]
    assert [item["target_http_exchange_count"] for item in attempts] == [1, 5, 5]
    assert run.result.target_http_exchange_count == 11
    assert run.result.all_http_exchange_count == 15
    assert "TARGET_PROTOCOL_ERROR" not in _gaps(run)


def test_failed_chat_and_successful_close_share_exact_observed_http_custody(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    module = api()
    factory = _RecordingFactory(module.HttpJsonTargetFactory())
    with fake.serve(mode="fail_first_chat") as server:
        run = _run_http(tmp_path, _http_config(server.base_url), factory=factory)
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    first_close = next(
        response
        for response in factory.sessions[0].responses
        if response["kind"] == "closed"
    )
    assert first_close["close_http_exchange_count"] == 1
    assert first_close["provider_http_exchange_count"] == 3
    assert attempts[0]["target_http_exchange_count"] == 3
    assert attempts[0]["termination_reason"] == "TARGET_HTTP_ERROR"
    assert "TARGET_PROTOCOL_ERROR" not in attempts[0]["gap_codes"]
    assert [item["target_http_exchange_count"] for item in attempts] == [3, 5, 5]
    assert run.result.target_http_exchange_count == 13
    assert run.result.all_http_exchange_count == 17
    assert "TARGET_PROTOCOL_ERROR" not in _gaps(run)


def test_http_connector_never_injects_a_prompt_or_target_tool_contract(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        _run_http(tmp_path, _http_config(server.base_url))
    payload = json.dumps(server.requests, sort_keys=True).casefold()
    assert "system_prompt" not in payload
    assert "prompt_version" not in payload
    assert "allowed_tools" not in payload
    assert "get_candidate_by_email" not in payload
    assert all(
        set(item["body"]) == {"client_id", "message"}
        for item in server.requests
        if item["path"].endswith("/chat")
    )


def test_production_connector_source_has_no_legacy_hrai_tool_reconstruction() -> None:
    labs = Path(__file__).resolve().parents[2]
    source_paths = [
        *sorted((labs / "src" / "triana_labs" / "adaptive_runner").glob("*.py")),
        labs / "src" / "triana_labs" / "cli.py",
    ]
    example_root = labs / "examples" / "target_connectors"
    if example_root.exists():
        source_paths.extend(sorted(example_root.rglob("*.py")))
    forbidden_tools = {
        "get_candidate_by_email",
        "get_existing_evaluation",
        "get_hiring_rubric",
        "query_database",
    }
    offenders: list[str] = []
    for path in source_paths:
        tree = ast.parse(path.read_text())
        values = {
            node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)
        }
        if values & forbidden_tools:
            offenders.append(str(path.relative_to(labs)))
    assert not offenders, offenders


@pytest.mark.parametrize(
    ("field", "invalid", "auth"),
    [
        ("model", {"unsafe": "shape"}, False),
        ("prompt", ["unsafe-shape"], False),
        ("tools", TARGET_SECRET, True),
    ],
)
def test_optional_target_identity_is_null_or_safe_declared_text_pre_egress(
    tmp_path: Path, field: str, invalid: Any, auth: bool
) -> None:
    config = _http_config("http://127.0.0.1:1", auth=auth)
    config["target"]["target_identity"][field] = invalid
    factory = _MustNotStart()
    with pytest.raises(Exception) as caught:
        _run_http(tmp_path, config, auth=auth, factory=factory)
    assert caught.value.__class__.__name__ == "AdaptiveRunFailure"
    assert caught.value.reason_code == "TARGET_CONNECTOR_CONFIG_INVALID"
    assert not factory.launches


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["target"].update(base_url="http://example.com"),
        lambda value: value["target"].update(base_url="http://127.0.0.1@evil.invalid"),
        lambda value: value["target"].update(allowed_host="localhost"),
        lambda value: value["target"]["turn"]["operation"].update(
            path_template="https://evil.invalid/chat"
        ),
        lambda value: value["target"]["turn"]["operation"].update(
            path_template="/../chat"
        ),
        lambda value: value["target"]["turn"]["operation"].update(
            path_template="/chat?unsafe=true"
        ),
        lambda value: value["target"]["turn"]["operation"].update(
            path_template="/chat#unsafe"
        ),
        lambda value: value["target"].update(fallback={"kind": "HTTP_JSON_V1"}),
    ],
)
def test_unsafe_endpoint_path_and_fallback_config_refuse_before_egress(
    tmp_path: Path, mutation: Any
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        config = _http_config(server.base_url)
        mutation(config)
        with pytest.raises(Exception) as caught:
            factory = _MustNotStart()
            _run_http(tmp_path, config, factory=factory)
    assert caught.value.__class__.__name__ == "AdaptiveRunFailure"
    assert caught.value.reason_code in {
        "TARGET_CONNECTOR_CONFIG_INVALID",
        "TARGET_ENDPOINT_REFUSED",
    }
    assert not server.requests
    assert not factory.launches


@pytest.mark.parametrize(
    "assignments",
    [
        [("unknown", "/message")],
        [("user_turn", "/message"), ("episode_id", "/message")],
        [("user_turn", "/missing/child")],
        [("transcript", "/message")],
    ],
)
def test_pointer_assignments_are_closed_nonoverlapping_and_typed(
    tmp_path: Path, assignments: list[tuple[str, str]]
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        config = _http_config(server.base_url)
        config["target"]["turn"]["operation"]["assignments"] = [
            {"pointer": pointer, "source": source} for source, pointer in assignments
        ]
        with pytest.raises(Exception) as caught:
            factory = _MustNotStart()
            _run_http(tmp_path, config, factory=factory)
    assert caught.value.__class__.__name__ == "AdaptiveRunFailure"
    assert caught.value.reason_code == "TARGET_CONNECTOR_CONFIG_INVALID"
    assert not server.requests
    assert not factory.launches


def test_redirect_retry_proxy_and_auth_secret_are_all_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        config = _http_config(server.base_url, auth=True)
        config["target"]["turn"]["operation"]["path_template"] = "/redirect"
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
        monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
        monkeypatch.delenv("NO_PROXY", raising=False)
        run = _run_http(tmp_path, config, auth=True)
    redirect = [item for item in server.requests if item["path"] == "/redirect"]
    assert len(redirect) == 3
    assert not any(item["path"] == "/sink" for item in server.requests)
    assert redirect[0]["headers"]["x-synthetic-target-key"] == TARGET_SECRET
    assert all("cookie" not in item["headers"] for item in server.requests)
    assert all("proxy-authorization" not in item["headers"] for item in server.requests)
    assert "TARGET_HTTP_ERROR" in _gaps(run)
    assert TARGET_SECRET.encode() not in b"".join(run.publisher.artifacts.values())


@pytest.mark.parametrize(
    ("mode", "tools", "usage", "gap"),
    [
        ("success", False, False, "TARGET_TOOL_TRACE_UNAVAILABLE"),
        ("success", True, False, "TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE"),
        ("malformed_tools", True, False, "TARGET_RESPONSE_INVALID"),
        ("malformed_usage", True, True, "TARGET_RESPONSE_INVALID"),
    ],
)
def test_optional_telemetry_is_present_unavailable_or_invalid_not_zero(
    tmp_path: Path, mode: str, tools: bool, usage: bool, gap: str
) -> None:
    fake = _fake_module()
    with fake.serve(mode=mode) as server:
        run = _run_http(
            tmp_path,
            _http_config(server.base_url, include_tools=tools, include_usage=usage),
        )
    assert gap in _gaps(run)
    if gap.endswith("UNAVAILABLE"):
        transcripts = jsonl(run.publisher.artifacts["transcripts.jsonl"])
        assert any(item["role"] == "ASSISTANT" for item in transcripts)


def test_tool_order_duplicates_and_reported_internal_usage_remain_separate(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    with fake.serve(mode="usage_present") as server:
        run = _run_http(
            tmp_path,
            _http_config(server.base_url, include_tools=True, include_usage=True),
        )
    tools = jsonl(run.publisher.artifacts["target_tool_events.jsonl"])
    assert [item["name"] for item in tools[:2]] == [
        "opaque_target_tool",
        "opaque_target_tool",
    ]
    manifest = json.loads(run.publisher.artifacts["manifest.json"])
    assert manifest["target_http_exchange_count"] == 15
    assert manifest["all_http_exchange_count"] == 21
    assert manifest["target_reported_internal_http_exchange_count"] == 36
    assert manifest["target_reported_internal_input_tokens"] == 909
    assert manifest["target_reported_internal_output_tokens"] == 207
    assert manifest["target_reported_internal_cost_usd"] == "1.125000"
    assert manifest["all_http_exchange_count"] != (
        manifest["simulator_http_exchange_count"]
        + manifest["target_http_exchange_count"]
        + manifest["target_reported_internal_http_exchange_count"]
    )


def test_remote_global_state_and_internal_budget_uncertainty_are_typed(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    with fake.serve() as server:
        run = _run_http(tmp_path, _http_config(server.base_url))
    assert {
        "TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE",
        "TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED",
        "TARGET_STATE_ISOLATION_UNAVAILABLE",
    } <= _gaps(run)
    assert run.result.outcome == "COMPLETED_WITH_GAPS"


def test_target_secret_reflection_stops_episode_and_never_enters_custody(
    tmp_path: Path,
) -> None:
    fake = _fake_module()
    with fake.serve(mode="secret_reflection", secret=TARGET_SECRET) as server:
        run = _run_http(tmp_path, _http_config(server.base_url, auth=True), auth=True)
    assert "TARGET_RESPONSE_INVALID" in _gaps(run)
    assert TARGET_SECRET.encode() not in b"".join(run.publisher.artifacts.values())


def test_strict_executable_bridge_has_no_hrai_world_prompt_or_tool_injection(
    tmp_path: Path,
) -> None:
    module = api()
    inputs = write_inputs(tmp_path, config=_executable_config())
    simulator = Simulator(module)
    publisher = CapturePublisher()
    result = module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        simulator=simulator,
        target_factory=module.JsonlTargetProcessFactory(),
        clock=Clock(),
        environ={**ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"},
        publisher=publisher,
        source_verifier=SourceVerifier(module),
        case_loader=FixtureLoader(module),
    )
    target_payload = json.dumps(
        json.loads(inputs.config.read_bytes())["target"], sort_keys=True
    ).casefold()
    assert "hrai" not in target_payload
    assert "allowed_tools" not in target_payload
    assert "world" not in target_payload
    assert "prompt_version" not in target_payload
    assert result.target_http_exchange_count == 0
    assert {
        "TARGET_TOOL_TRACE_UNAVAILABLE",
        "TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE",
        "TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED",
    } <= {item["reason_code"] for item in jsonl(publisher.artifacts["gaps.jsonl"])}
