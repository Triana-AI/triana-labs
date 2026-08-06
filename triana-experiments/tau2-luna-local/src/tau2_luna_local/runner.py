from __future__ import annotations

import importlib.metadata
import inspect
import json
import time
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

from .capture import CompletionCapture, redact
from .config import Config
from .constants import (
    COMPLETENESS_SCHEMA,
    HASHED_ARTIFACTS,
    MANIFEST_SCHEMA,
    REQUIRED_TELEMETRY,
    UPSTREAM_COMMIT,
    UPSTREAM_RELEASE,
    UPSTREAM_REPOSITORY,
)
from .journal import EventJournal
from .serde import artifact_identity, write_canonical_json
from .verify import verify_bundle


class RunRefused(RuntimeError):
    """Raised before provider egress when a run boundary cannot be proven safe."""


def prepare_run_directory(run_dir: Path) -> Path:
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RunRefused(f"run directory already exists: {run_dir}") from exc
    if not run_dir.is_dir():
        raise RunRefused(f"could not create run directory: {run_dir}")
    return run_dir


def verify_tau2_distribution() -> dict[str, str]:
    try:
        distribution = importlib.metadata.distribution("tau2")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RunRefused("the exact pinned tau2 distribution is not installed") from exc
    raw = distribution.read_text("direct_url.json")
    if raw is None:
        raise RunRefused("tau2 has no PEP 610 direct_url.json; exact upstream commit is unproven")
    try:
        direct_url = json.loads(raw)
        vcs = direct_url["vcs_info"]
        commit = vcs["commit_id"]
        url = direct_url["url"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RunRefused("tau2 PEP 610 provenance is malformed") from exc
    if commit != UPSTREAM_COMMIT:
        raise RunRefused(f"tau2 commit mismatch: expected {UPSTREAM_COMMIT}, observed {commit}")
    if not str(url).rstrip("/").endswith("sierra-research/tau2-bench.git"):
        raise RunRefused(f"tau2 repository mismatch: {url}")
    return {"distribution_version": distribution.version, "commit": commit, "url": str(url)}


def _classification(state: str, source: str, reason: str | None = None) -> dict[str, str]:
    result = {"state": state, "source": source}
    if reason is not None:
        result["reason"] = reason
    return result


def _read_events(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def _has_nested(mapping: Any, *path: str) -> bool:
    current = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current or current[key] is None:
            return False
        current = current[key]
    return True


def build_completeness(run_dir: Path, *, benchmark_succeeded: bool) -> dict[str, Any]:
    events = _read_events(run_dir / "events.jsonl")
    responses = [event["payload"] for event in events if event.get("event_name") == "model.response"]
    terminals = responses + [event["payload"] for event in events if event.get("event_name") == "model.error"]
    requests = [event["payload"] for event in events if event.get("event_name") == "model.request"]
    telemetry = {
        field: _classification("UNAVAILABLE", "local-capture", "no observable value was found")
        for field in REQUIRED_TELEMETRY
    }
    attempt_fields = {
        "attempt.call_id",
        "attempt.role_lane",
        "attempt.start_time",
        "attempt.end_time",
        "attempt.duration",
        "attempt.number",
        "attempt.outcome",
    }
    request_fields = {
        "request.model",
        "request.endpoint_host",
        "request.api_version",
        "request.kwargs",
        "request.messages",
        "request.tools",
        "request.tool_choice",
        "request.retry_setting",
    }
    if requests and terminals:
        for field in attempt_fields:
            telemetry[field] = _classification("CAPTURED", "events.jsonl")
    if requests:
        for field in request_fields:
            telemetry[field] = _classification("CAPTURED", "events.jsonl")

    response_paths: dict[str, tuple[str, ...]] = {
        "response.mapping": ("response",),
        "response.choices": ("response", "choices"),
        "response.content": ("response", "choices"),
        "response.tool_calls": ("response", "choices"),
        "response.finish_reason": ("response", "choices"),
        "response.identifiers": ("response", "id"),
        "response.created": ("response", "created"),
        "response.usage": ("response", "usage"),
        "response.usage.prompt_tokens": ("response", "usage", "prompt_tokens"),
        "response.usage.completion_tokens": ("response", "usage", "completion_tokens"),
        "response.usage.total_tokens": ("response", "usage", "total_tokens"),
        "response.usage.cached_tokens": ("response", "usage", "prompt_tokens_details", "cached_tokens"),
        "response.usage.reasoning_tokens": (
            "response",
            "usage",
            "completion_tokens_details",
            "reasoning_tokens",
        ),
        "response.cost": ("cost",),
        "response.headers": ("response_headers",),
        "response.hidden_metadata": ("hidden_metadata",),
        "response.raw_class": ("raw_response_class",),
    }
    for field, path in response_paths.items():
        if responses and all(_has_nested(response, *path) for response in responses):
            telemetry[field] = _classification("CAPTURED", "events.jsonl")
        else:
            telemetry[field] = _classification(
                "NOT_RETURNED", "azure/litellm", f"observable {field} was not returned"
            )
    reasoning_returned = any(
        "reasoning_content" in json.dumps(response.get("response", {})) for response in responses
    )
    telemetry["response.reasoning"] = _classification(
        "CAPTURED" if reasoning_returned else "NOT_RETURNED",
        "azure/litellm",
        None if reasoning_returned else "no reasoning summary or reasoning_content was returned",
    )
    telemetry["provider_private_chain_of_thought"] = _classification(
        "NOT_RETURNED", "azure", "provider-private chain-of-thought is not an observable API field"
    )

    tau_fields = (
        "tau2.messages",
        "tau2.tool_calls",
        "tau2.tool_results",
        "tau2.costs",
        "tau2.usage",
        "tau2.raw_message_data",
        "tau2.termination_reason",
        "tau2.reward",
        "tau2.reward_breakdown",
        "tau2.evaluator_checks",
        "tau2.task_trial_seed",
        "tau2.run_config",
    )
    for field in tau_fields:
        telemetry[field] = _classification(
            "CAPTURED" if benchmark_succeeded else "UNAVAILABLE",
            "tau2-results.json" if benchmark_succeeded else "tau2",
            None if benchmark_succeeded else "benchmark did not publish a Results artifact",
        )
    telemetry["bundle.hashes"] = _classification("CAPTURED", "manifest.json")
    telemetry["verification.hashes"] = _classification("CAPTURED", "deterministic verifier")
    preliminary_valid = all(
        value["state"] == "CAPTURED"
        for key, value in telemetry.items()
        if key not in {
            "response.created",
            "response.hidden_metadata",
            "response.reasoning",
            "provider_private_chain_of_thought",
        }
    )
    return {"schema_version": COMPLETENESS_SCHEMA, "valid": preliminary_valid, "telemetry": telemetry}


def _write_manifest(run_dir: Path, *, run_id: str, config: Config, provenance: dict[str, str]) -> None:
    artifacts = {
        name: artifact_identity(run_dir / name) for name in HASHED_ARTIFACTS if (run_dir / name).is_file()
    }
    projection = config.safe_projection()
    environment_presence = projection.pop("environment_presence")
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "run_id": run_id,
        "upstream": {
            "repository": UPSTREAM_REPOSITORY,
            "commit": UPSTREAM_COMMIT,
            "release": UPSTREAM_RELEASE,
            **provenance,
        },
        "config": projection,
        "environment_presence": environment_presence,
        "artifacts": artifacts,
    }
    write_canonical_json(run_dir / "manifest.json", manifest)


def _tau2_modules() -> tuple[ModuleType, ModuleType]:
    # Import the completion-owning module only after local sinks and custody exist.
    import tau2.run as tau_run
    import tau2.utils.llm_utils as llm_utils

    return tau_run, llm_utils


def _tau2_role_modules() -> dict[str, Any]:
    import tau2.agent.llm_agent as agent_boundary
    import tau2.evaluator.evaluator_nl_assertions as evaluator_boundary
    import tau2.user.user_simulator as user_boundary

    return {"agent": agent_boundary, "user": user_boundary, "evaluator": evaluator_boundary}


def _role_lane_resolver(boundaries: Mapping[str, Any]) -> Callable[[Any, Any], str | None]:
    code_lane_candidates: dict[Any, set[str]] = {}
    module_lanes: dict[str, str] = {}
    for lane, boundary in boundaries.items():
        module_name = getattr(boundary, "__name__", None)
        if isinstance(module_name, str):
            module_lanes[module_name] = lane
        for value in vars(boundary).values():
            code = getattr(value, "__code__", None)
            if code is not None:
                code_lane_candidates.setdefault(code, set()).add(lane)
    code_lanes = {
        code: next(iter(lanes)) for code, lanes in code_lane_candidates.items() if len(lanes) == 1
    }

    def resolve(_args: Any, _kwargs: Any) -> str | None:
        frame = inspect.currentframe()
        try:
            frame = frame.f_back if frame is not None else None
            while frame is not None:
                if frame.f_code in code_lanes:
                    return code_lanes[frame.f_code]
                frame_module = frame.f_globals.get("__name__")
                if isinstance(frame_module, str):
                    for module_name, lane in module_lanes.items():
                        if frame_module == module_name or frame_module.startswith(f"{module_name}."):
                            return lane
                frame = frame.f_back
        finally:
            del frame
        return None

    return resolve


def run_experiment(
    config: Config,
    *,
    run_id: str | None = None,
    remote_append: Callable[[str, bytes, str], None] | None = None,
    remote_prefix: str | None = None,
    completion_guard: Callable[[Callable[..., Any], Any], Any] | None = None,
    nl_assertions_config: Mapping[str, str] | None = None,
) -> Path:
    from .otel import LocalTelemetry

    if (remote_append is None) != (remote_prefix is None):
        raise RunRefused("remote append and prefix must be configured together")
    luna_api_key = "" if nl_assertions_config is None else nl_assertions_config.get("api_key", "")
    secrets = tuple(secret for secret in (config.api_key, luna_api_key) if secret)

    provenance = verify_tau2_distribution()
    identity = run_id or f"run-{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    run_dir = prepare_run_directory(config.trace_root / identity)
    results_path = run_dir / "tau2-results.json"
    benchmark_succeeded = False
    caught: BaseException | None = None

    with (
        EventJournal(run_dir / "events.jsonl") as journal,
        LocalTelemetry(
            run_dir / "spans.jsonl",
            run_id=identity,
            secrets=secrets,
            remote_append=remote_append,
            remote_object_name=f"{remote_prefix}spans.jsonl" if remote_prefix else None,
        ) as telemetry,
    ):
        event_append: Callable[[str, dict[str, Any]], Any] = journal.append
        if remote_append is not None and remote_prefix is not None:
            from .cloud_smoke import DurableEventSink

            event_append = DurableEventSink(
                local_append=journal.append,
                remote_append=remote_append,
                object_name=f"{remote_prefix}events.jsonl",
                secrets=secrets,
            )

        def append_with_local_fallback(event_name: str, payload: dict[str, Any]) -> Any:
            try:
                return event_append(event_name, payload)
            except BaseException:
                if remote_append is None:
                    raise
                return journal.append(event_name, payload)

        event_append("run.started", {"run_id": identity, "config": config.safe_projection()})
        try:
            tau_run, llm_utils = _tau2_modules()
            from .terra_smoke import (
                TERRA_DEPLOYMENT,
                luna_response_cost_fallback,
                terra_response_cost_fallback,
            )

            llm_args = {
                "api_base": config.api_base,
                "api_version": config.api_version,
                "api_key": config.api_key,
                "caching": False,
                "num_retries": 0,
            }
            task_ids = [config.task_id] if config.task_id else None
            tasks = tau_run.get_tasks(config.domain, task_ids=task_ids, num_tasks=config.task_count)
            boundaries = _tau2_role_modules()
            evaluator_boundary = boundaries.get("evaluator")
            evaluator_originals: tuple[Any, Any] | None = None
            cost_fallbacks = {config.model: terra_response_cost_fallback}
            if nl_assertions_config is not None:
                luna_model = nl_assertions_config.get("model")
                luna_base = nl_assertions_config.get("api_base")
                luna_version = nl_assertions_config.get("api_version")
                if (
                    luna_model != "azure/tau2-luna-smoke-20260805"
                    or not luna_base
                    or not luna_version
                    or not luna_api_key
                    or evaluator_boundary is None
                ):
                    raise RunRefused("exact Luna NL-assertion configuration is required")
                evaluator_originals = (
                    evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS,
                    evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS_ARGS,
                )
                evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS = luna_model
                evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS_ARGS = {
                    "api_base": luna_base,
                    "api_version": luna_version,
                    "api_key": luna_api_key,
                    "caching": False,
                    "num_retries": 0,
                }
                cost_fallbacks[luna_model] = luna_response_cost_fallback
            llm_boundary: Any = llm_utils
            original_completion = llm_boundary.completion
            if completion_guard is not None:
                llm_boundary.completion = lambda *args, **kwargs: completion_guard(
                    original_completion, *args, **kwargs
                )
            try:
                capture = CompletionCapture(
                    target=llm_utils,
                    event_sink=event_append,
                    span_sink=telemetry.record_model_span,
                    secrets=secrets,
                    role_lane_resolver=_role_lane_resolver(boundaries),
                    response_cost_fallbacks=(
                        cost_fallbacks if config.deployment == TERRA_DEPLOYMENT else {}
                    ),
                )
                with (
                    telemetry.boundary("benchmark", {"tau2.domain": config.domain}),
                    capture,
                ):
                    results = tau_run.run_tasks(
                        domain=config.domain,
                        tasks=tasks,
                        agent="llm_agent",
                        user="user_simulator",
                        llm_agent=config.model,
                        llm_args_agent=llm_args,
                        llm_user=config.model,
                        llm_args_user=llm_args,
                        num_trials=config.trial_count,
                        max_steps=config.max_steps,
                        max_errors=config.max_errors,
                        save_to=None,
                        console_display=False,
                        max_concurrency=config.concurrency,
                        seed=config.seed,
                        log_level="INFO",
                    )
            finally:
                llm_boundary.completion = original_completion
                if evaluator_originals is not None:
                    assert evaluator_boundary is not None
                    (
                        evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS,
                        evaluator_boundary.DEFAULT_LLM_NL_ASSERTIONS_ARGS,
                    ) = evaluator_originals
            safe_results = redact(results.model_dump(mode="json"), secrets=secrets)
            write_canonical_json(results_path, safe_results)
            benchmark_succeeded = True
            event_append("benchmark.finished", {"run_id": identity, "result_published": True})
        except BaseException as exc:
            caught = exc
            append_with_local_fallback(
                "benchmark.error",
                {
                    "run_id": identity,
                    "exception_class": type(exc).__name__,
                    "message": redact(str(exc), secrets=secrets),
                    "result_published": False,
                },
            )
        finally:
            append_with_local_fallback(
                "run.finished", {"run_id": identity, "benchmark_succeeded": benchmark_succeeded}
            )

    completeness = build_completeness(run_dir, benchmark_succeeded=benchmark_succeeded)
    write_canonical_json(run_dir / "completeness.json", completeness)
    _write_manifest(run_dir, run_id=identity, config=config, provenance=provenance)
    report = verify_bundle(run_dir, secret_values=secrets)
    if caught is not None:
        raise RunRefused(
            f"benchmark failed; partial evidence retained at {run_dir}: {type(caught).__name__}"
        ) from caught
    if not report["valid"]:
        raise RunRefused(f"benchmark completed but trace bundle is incomplete at {run_dir}")
    return run_dir
