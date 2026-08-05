"""Expose the local Trace Observer as a safe process boundary.

The CLI owns argument handling, presentation receipts, terminal logs, and exit codes.
The Observer owns corpus behavior, while ``contracts.traces`` owns individual trace
validation. External adapters produce JSONL and do not call this module.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import time
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Never
from urllib.parse import urlsplit

from triana_labs import __version__
from triana_labs.intelligence import DeriveFailure, derive
from triana_labs.observer import ObserveFailure, observe

_SERVICE = "triana-labs-cli"
_usage_command = "traces.observe"


class _SafeArgumentParser(argparse.ArgumentParser):
    """Replace value-echoing argparse failures with one safe terminal event."""

    def error(self, message: str) -> Never:
        """Emit the closed usage refusal without reproducing user arguments."""

        # argparse's default error echoes user arguments and usage text. Discarding the
        # message preserves the one-event log contract and prevents paths or values
        # from leaking before command execution begins.
        del message
        if _usage_command in ("cases.generate", "cases.resume"):
            event = _case_terminal_log(
                command=_usage_command,
                event_name=f"triana.{_usage_command}.rejected",
                severity="ERROR",
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            )
        elif _usage_command == "episodes.run":
            event = _episode_terminal_log(
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            )
        elif _usage_command == "corpus.derive":
            event = _corpus_terminal_log(
                event_name="triana.corpus.derive.rejected",
                severity="ERROR",
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            )
        else:
            event = _terminal_log(
                event_name="triana.traces.observe.rejected",
                severity="ERROR",
                outcome="REJECTED",
                reason_code="CLI_USAGE_ERROR",
                duration_ms=0,
            )
        _write_json(sys.stderr, event)
        raise SystemExit(2)


def _build_parser() -> _SafeArgumentParser:
    """Build the small command tree without executing corpus behavior."""

    parser = _SafeArgumentParser(
        prog="triana",
        description="Inspect conversational-agent behavior with local evidence.",
    )
    commands = parser.add_subparsers(dest="command")

    traces = commands.add_parser("traces", help="Work with trace corpora.")
    trace_commands = traces.add_subparsers(dest="trace_command")
    observe = trace_commands.add_parser(
        "observe",
        help="Validate and profile a local trace corpus.",
    )
    observe.add_argument("input", help="Path to a local JSONL trace corpus.")
    observe.add_argument(
        "--out",
        required=True,
        help="New directory for generated corpus artifacts.",
    )
    corpus = commands.add_parser("corpus", help="Derive intelligence from a corpus.")
    corpus_commands = corpus.add_subparsers(dest="corpus_command")
    derive_parser = corpus_commands.add_parser(
        "derive", help="Derive structural intelligence from an Observer bundle."
    )
    derive_parser.add_argument("manifest", help="Observer manifest.json path.")
    derive_parser.add_argument(
        "--out", required=True, help="New directory for intelligence artifacts."
    )
    cases = commands.add_parser("cases", help="Generate grounded case proposals.")
    case_commands = cases.add_subparsers(dest="case_command")
    generate_parser = case_commands.add_parser(
        "generate", help="Generate proposed simulation cases from synthetic evidence."
    )
    generate_parser.add_argument("observer_manifest")
    generate_parser.add_argument("--intelligence", required=True)
    generate_parser.add_argument("--config", required=True)
    generate_parser.add_argument(
        "--cache-dir",
        required=True,
        help="Private exact-response cache directory.",
    )
    generate_parser.add_argument("--out", required=True)
    generate_parser.add_argument("--world-inventory")
    resume_parser = case_commands.add_parser(
        "resume", help="Resume a restricted case run after human answers."
    )
    resume_parser.add_argument("pause_manifest")
    resume_parser.add_argument("--answers", required=True)
    resume_parser.add_argument("--config", required=True)
    resume_parser.add_argument(
        "--cache-dir",
        required=True,
        help="Private exact-response cache directory used by the paused run.",
    )
    resume_parser.add_argument("--out", required=True)
    episodes = commands.add_parser("episodes", help="Run bounded adaptive episodes.")
    episode_commands = episodes.add_subparsers(dest="episode_command")
    run_parser = episode_commands.add_parser(
        "run", help="Run the frozen LABS-05 synthetic episode panel."
    )
    run_parser.add_argument("manifest")
    run_parser.add_argument("--review", required=True)
    run_parser.add_argument("--config", required=True)
    run_parser.add_argument("--out", required=True)
    run_parser.add_argument("--world-inventory")
    return parser


def _write_json(stream: Any, value: dict[str, Any]) -> None:
    """Write one compact presentation JSON value and terminal LF."""

    # Receipts and logs are presentation channels, not portable artifact identities.
    # They still use a deterministic compact shape so automation has one clear form.
    stream.write(
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    )


def _run_backend_command(arguments: list[str]) -> int:
    """Delegate backend transport semantics to the installed backend package."""

    try:
        from triana_backend.cli import main as backend_main
    except ModuleNotFoundError as error:
        if error.name != "triana_backend":
            raise
        _write_json(
            sys.stderr,
            {
                "code": "BACKEND_CLI_UNAVAILABLE",
                "outcome": "REJECTED",
                "service": _SERVICE,
            },
        )
        return 69
    return backend_main(arguments)


def _terminal_log(
    *,
    event_name: str,
    severity: str,
    outcome: str,
    reason_code: str | None,
    duration_ms: int,
    input_count: int | None = None,
    accepted_count: int | None = None,
    rejected_count: int | None = None,
    eligible_count: int | None = None,
) -> dict[str, Any]:
    """Construct a log event through the closed safe-field seam."""

    # This constructor is the logging allowlist. Success includes corpus counts;
    # refusal omits them when no complete accounting exists. Paths, trace values,
    # tool names, exceptions, and artifact hashes have no parameter through this seam.
    event: dict[str, Any] = {
        "command": "traces.observe",
        "duration_ms": duration_ms,
        "event_name": event_name,
        "outcome": outcome,
        "reason_code": reason_code,
        "service": _SERVICE,
        "service_version": __version__,
        "severity": severity,
    }
    if input_count is not None:
        event.update(
            {
                "input_count": input_count,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "case_generation_eligible_count": eligible_count,
            }
        )
    return event


def main(argv: Sequence[str] | None = None) -> int:
    """Invoke the Observer once and translate its typed result to CLI channels."""

    global _usage_command
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    if raw_arguments[:1] == ["backend"]:
        return _run_backend_command(raw_arguments)
    if raw_arguments[:2] in (["cases", "generate"], ["cases", "resume"]):
        _usage_command = f"cases.{raw_arguments[1]}"
    elif raw_arguments[:2] == ["episodes", "run"]:
        _usage_command = "episodes.run"
    elif raw_arguments[:2] == ["corpus", "derive"]:
        _usage_command = "corpus.derive"
    else:
        _usage_command = "traces.observe"
    parser = _build_parser()
    arguments = parser.parse_args(raw_arguments)

    if arguments.command == "episodes" and arguments.episode_command == "run":
        return _run_episodes(arguments)

    if arguments.command == "traces" and arguments.trace_command == "observe":
        start = time.monotonic_ns()
        try:
            result = observe(Path(arguments.input), Path(arguments.out))
        except ObserveFailure as failure:
            # Typed Observer refusals preserve their contract-owned reason and exit.
            _write_json(
                sys.stderr,
                _terminal_log(
                    event_name="triana.traces.observe.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code=failure.reason_code,
                    duration_ms=_duration_ms(start),
                ),
            )
            return failure.exit_code
        except Exception:  # noqa: BLE001 - the CLI must redact unexpected failures.
            # The outermost boundary deliberately catches unexpected implementation
            # faults, emits no exception text, and refuses to mislabel them as evidence.
            _write_json(
                sys.stderr,
                _terminal_log(
                    event_name="triana.traces.observe.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code="INTERNAL_INVARIANT_FAILED",
                    duration_ms=_duration_ms(start),
                ),
            )
            return 70

        _write_json(
            sys.stdout,
            {
                "accepted_count": result.accepted_count,
                "case_generation_eligible_count": (
                    result.case_generation_eligible_count
                ),
                "manifest_path": f"{arguments.out}/manifest.json",
                "outcome": result.outcome,
                "rejected_count": result.rejected_count,
            },
        )
        event_name = (
            "triana.traces.observe.succeeded"
            if result.outcome == "COMPLETED"
            else "triana.traces.observe.completed_with_rejections"
        )
        _write_json(
            sys.stderr,
            _terminal_log(
                event_name=event_name,
                severity="INFO",
                outcome=result.outcome,
                reason_code=None,
                duration_ms=_duration_ms(start),
                input_count=result.input_count,
                accepted_count=result.accepted_count,
                rejected_count=result.rejected_count,
                eligible_count=result.case_generation_eligible_count,
            ),
        )
        return 0 if result.outcome == "COMPLETED" else 10

    if arguments.command == "corpus" and arguments.corpus_command == "derive":
        start = time.monotonic_ns()
        try:
            derive_result = derive(Path(arguments.manifest), Path(arguments.out))
        except DeriveFailure as failure:
            _write_json(
                sys.stderr,
                _corpus_terminal_log(
                    event_name="triana.corpus.derive.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code=failure.reason_code,
                    duration_ms=_duration_ms(start),
                ),
            )
            return failure.exit_code
        except Exception:  # noqa: BLE001 - redact unexpected failures at the CLI.
            _write_json(
                sys.stderr,
                _corpus_terminal_log(
                    event_name="triana.corpus.derive.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code="INTERNAL_INVARIANT_FAILED",
                    duration_ms=_duration_ms(start),
                ),
            )
            return 70
        _write_json(
            sys.stdout,
            {
                "cluster_count": derive_result.cluster_count,
                "gap_count": derive_result.gap_count,
                "manifest_path": f"{arguments.out}/manifest.json",
                "outcome": derive_result.outcome,
                "trace_count": derive_result.trace_count,
            },
        )
        _write_json(
            sys.stderr,
            _corpus_terminal_log(
                event_name="triana.corpus.derive.completed_with_gaps",
                severity="INFO",
                outcome=derive_result.outcome,
                reason_code=None,
                duration_ms=_duration_ms(start),
                cluster_count=derive_result.cluster_count,
                gap_count=derive_result.gap_count,
                trace_count=derive_result.trace_count,
            ),
        )
        return 10

    if arguments.command == "cases" and arguments.case_command == "generate":
        from triana_labs.case_factory import GenerateFailure, generate

        start = time.monotonic_ns()
        config_path = Path(arguments.config)
        try:
            config = _read_config(config_path)
            if config.get("artifact_kind") == "case_factory_config":
                generated = generate(
                    Path(arguments.observer_manifest),
                    Path(arguments.intelligence),
                    config_path,
                    Path(arguments.out),
                    cache_path=Path(arguments.cache_dir),
                )
                restricted = False
            elif config.get("artifact_kind") == "case_factory_restricted_config":
                from triana_labs.case_factory.generate import generate_restricted
                from triana_labs.case_factory.provider import SystemClock

                restricted_config, environ = _restricted_configuration(
                    config, os.environ
                )
                transport = _build_restricted_transport(restricted_config, environ)
                generated = generate_restricted(
                    Path(arguments.observer_manifest),
                    Path(arguments.intelligence),
                    config_path,
                    Path(arguments.out),
                    cache_path=Path(arguments.cache_dir),
                    transport=transport,
                    clock=SystemClock(),
                    environ=environ,
                    requested_case_count=restricted_config["generation"][
                        "candidate_count"
                    ],
                    world_inventory=(
                        Path(arguments.world_inventory)
                        if arguments.world_inventory
                        else None
                    ),
                )
                restricted = True
            else:
                raise _CliRefusal("CONFIG_INVALID", 2)
        except _CliRefusal as failure:
            _write_case_refusal("cases.generate", failure.reason_code, start)
            return failure.exit_code
        except GenerateFailure as failure:
            _write_json(
                sys.stderr,
                _case_terminal_log(
                    event_name="triana.cases.generate.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code=failure.reason_code,
                    duration_ms=_duration_ms(start),
                ),
            )
            return failure.exit_code
        except Exception:  # noqa: BLE001 - redact the outer process boundary.
            _write_json(
                sys.stderr,
                _case_terminal_log(
                    event_name="triana.cases.generate.rejected",
                    severity="ERROR",
                    outcome="REJECTED",
                    reason_code="INTERNAL_INVARIANT_FAILED",
                    duration_ms=_duration_ms(start),
                ),
            )
            return 70
        if restricted:
            return _write_restricted_result(generated, "cases.generate", start)
        _write_json(
            sys.stdout,
            {
                "outcome": generated.outcome,
                "manifest_path": str(generated.manifest_path),
                "valid_case_count": generated.valid_case_count,
                "distinct_case_count": generated.distinct_case_count,
                "provider_call_count": generated.provider_call_count,
                "conservative_cost_usd": generated.conservative_cost_usd,
            },
        )
        _write_json(
            sys.stderr,
            _case_terminal_log(
                event_name=(
                    "triana.cases.generate.completed"
                    if generated.outcome == "COMPLETED"
                    else "triana.cases.generate.completed_with_gaps"
                ),
                severity="INFO",
                outcome=generated.outcome,
                reason_code=generated.reason_code,
                duration_ms=_duration_ms(start),
                attempted_case_count=generated.attempted_case_count,
                valid_case_count=generated.valid_case_count,
                distinct_case_count=generated.distinct_case_count,
                provider_call_count=generated.provider_call_count,
                conservative_cost_usd=generated.conservative_cost_usd,
            ),
        )
        return 0 if generated.outcome == "COMPLETED" else 10

    if arguments.command == "cases" and arguments.case_command == "resume":
        from triana_labs.case_factory.generate import resume_restricted
        from triana_labs.case_factory.primitives import Invalid
        from triana_labs.case_factory.provider import SystemClock

        start = time.monotonic_ns()
        try:
            config_path = Path(arguments.config)
            config_bytes = _read_bytes(config_path, "CONFIG_INVALID")
            config = _parse_object(config_bytes, "CONFIG_INVALID")
            restricted_config, environ = _restricted_configuration(config, os.environ)
            pause_manifest = Path(arguments.pause_manifest)
            resume_state = _resume_state(pause_manifest)
            if _artifact_hash(config_bytes) != resume_state.get("config_hash"):
                raise _CliRefusal("CONFIG_INVALID", 2)
            answers = _resume_answers(Path(arguments.answers), resume_state)
            _require_private_resume_state(Path(arguments.cache_dir), resume_state)
            transport = _build_restricted_transport(restricted_config, environ)
            resumed = resume_restricted(
                pause_manifest,
                answers,
                Path(arguments.out),
                cache_path=Path(arguments.cache_dir),
                transport=transport,
                clock=SystemClock(),
            )
        except _CliRefusal as failure:
            _write_case_refusal("cases.resume", failure.reason_code, start)
            return failure.exit_code
        except (Invalid, OSError, KeyError, TypeError):
            _write_case_refusal("cases.resume", "RESUME_STATE_UNAVAILABLE", start)
            return 5
        except Exception:  # noqa: BLE001 - redact the outer process boundary.
            _write_case_refusal("cases.resume", "INTERNAL_INVARIANT_FAILED", start)
            return 70
        return _write_restricted_result(resumed, "cases.resume", start)

    parser.print_help()
    return 0


def _episode_terminal_log(
    *,
    outcome: str,
    reason_code: str | None,
    duration_ms: int,
    attempted: int | None = None,
    valid: int | None = None,
    effective: int | None = None,
    simulator_http: int | None = None,
    target_http: int | None = None,
    all_http: int | None = None,
    reserved: str | None = None,
    actual: str | None = None,
) -> dict[str, Any]:
    """Build the content-free LABS-05 terminal event."""

    event: dict[str, Any] = {
        "command": "episodes.run",
        "duration_ms": duration_ms,
        "outcome": outcome,
        "reason_code": reason_code,
        "service": _SERVICE,
        "service_version": __version__,
    }
    if attempted is not None:
        event.update(
            attempted_episode_count=attempted,
            valid_episode_count=valid,
            effective_trajectory_count=effective,
            simulator_http_exchange_count=simulator_http,
            target_http_exchange_count=target_http,
            all_http_exchange_count=all_http,
            reserved_cost_usd=reserved,
            actual_cost_usd=actual,
        )
    return event


def _run_episodes(arguments: argparse.Namespace) -> int:
    """Construct real boundaries and translate the typed LABS-05 result."""

    from triana_labs.adaptive_runner import (
        AdaptiveRunFailure,
        HttpJsonTargetFactory,
        JsonlTargetProcessFactory,
        run,
    )
    from triana_labs.adaptive_runner.boundaries import FoundrySimulatorTransport
    from triana_labs.case_factory.provider import SystemClock

    start = time.monotonic_ns()
    try:
        config_path = Path(arguments.config)
        config_bytes = _read_bytes(config_path, "CONFIG_INVALID")
        config = _parse_object(config_bytes, "CONFIG_INVALID")
        simulator_config = config.get("simulator")
        if not isinstance(simulator_config, dict):
            raise _CliRefusal("CONFIG_INVALID", 2)
        key_name = simulator_config.get("api_key_env")
        api_key = os.environ.get(key_name, "") if isinstance(key_name, str) else ""
        if _read_bytes(config_path, "CONFIG_INVALID") != config_bytes:
            raise _CliRefusal("CONFIG_INVALID", 2)
        target_config = config.get("target")
        connector_kind = (
            target_config.get("connector_kind")
            if isinstance(target_config, dict)
            else None
        )
        if connector_kind == "HTTP_JSON_V1":
            target_factory: Any = HttpJsonTargetFactory()
        elif connector_kind == "EXECUTABLE_JSONL_V1":
            target_factory = JsonlTargetProcessFactory()
        else:
            raise _CliRefusal("TARGET_CONNECTOR_CONFIG_INVALID", 2)
        result = run(
            Path(arguments.manifest),
            Path(arguments.review),
            config_path,
            Path(arguments.out),
            simulator=FoundrySimulatorTransport(simulator_config, api_key),
            target_factory=target_factory,
            clock=SystemClock(),
            environ=os.environ,
            world_inventory=(
                Path(arguments.world_inventory) if arguments.world_inventory else None
            ),
        )
    except _CliRefusal as failure:
        _write_json(
            sys.stderr,
            _episode_terminal_log(
                outcome="REJECTED",
                reason_code=failure.reason_code,
                duration_ms=_duration_ms(start),
            ),
        )
        return failure.exit_code
    except AdaptiveRunFailure as failure:
        _write_json(
            sys.stderr,
            _episode_terminal_log(
                outcome="REJECTED",
                reason_code=failure.reason_code,
                duration_ms=_duration_ms(start),
            ),
        )
        return failure.exit_code
    except Exception:  # noqa: BLE001 - redact the outer process boundary.
        _write_json(
            sys.stderr,
            _episode_terminal_log(
                outcome="REJECTED",
                reason_code="INTERNAL_INVARIANT_FAILED",
                duration_ms=_duration_ms(start),
            ),
        )
        return 70
    _write_json(
        sys.stdout,
        {
            "attempted_episode_count": result.attempted_episode_count,
            "effective_trajectory_count": result.effective_trajectory_count,
            "manifest_path": f"{arguments.out}/manifest.json",
            "outcome": result.outcome,
            "valid_episode_count": result.valid_episode_count,
        },
    )
    _write_json(
        sys.stderr,
        _episode_terminal_log(
            outcome=result.outcome,
            reason_code=result.reason_code,
            duration_ms=_duration_ms(start),
            attempted=result.attempted_episode_count,
            valid=result.valid_episode_count,
            effective=result.effective_trajectory_count,
            simulator_http=result.simulator_http_exchange_count,
            target_http=result.target_http_exchange_count,
            all_http=result.all_http_exchange_count,
            reserved=result.reserved_cost_usd,
            actual=result.actual_cost_usd,
        ),
    )
    return result.exit_code


def _duration_ms(start_ns: int) -> int:
    """Return nonnegative operational duration excluded from portable artifacts."""

    # Duration is operational log metadata only. Monotonic time cannot affect any
    # portable artifact, count, rejection, or future Corpus Intelligence input.
    return max(0, (time.monotonic_ns() - start_ns) // 1_000_000)


def _corpus_terminal_log(
    *,
    event_name: str,
    severity: str,
    outcome: str,
    reason_code: str | None,
    duration_ms: int,
    cluster_count: int | None = None,
    gap_count: int | None = None,
    trace_count: int | None = None,
) -> dict[str, Any]:
    """Construct the closed, content-free Corpus Intelligence log shape."""

    event: dict[str, Any] = {
        "command": "corpus.derive",
        "duration_ms": duration_ms,
        "event_name": event_name,
        "outcome": outcome,
        "reason_code": reason_code,
        "service": _SERVICE,
        "service_version": __version__,
        "severity": severity,
    }
    if cluster_count is not None:
        event.update(
            {
                "cluster_count": cluster_count,
                "gap_count": gap_count,
                "trace_count": trace_count,
            }
        )
    return event


def _case_terminal_log(
    *,
    event_name: str,
    severity: str,
    outcome: str,
    reason_code: str | None,
    duration_ms: int,
    attempted_case_count: int | None = None,
    valid_case_count: int | None = None,
    distinct_case_count: int | None = None,
    provider_call_count: int | None = None,
    provider_http_exchange_count: int | None = None,
    conservative_cost_usd: str | None = None,
    command: str = "cases.generate",
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "command": command,
        "duration_ms": duration_ms,
        "event_name": event_name,
        "outcome": outcome,
        "reason_code": reason_code,
        "service": _SERVICE,
        "service_version": __version__,
        "severity": severity,
    }
    if attempted_case_count is not None:
        event.update(
            attempted_case_count=attempted_case_count,
            valid_case_count=valid_case_count,
            distinct_case_count=distinct_case_count,
            provider_call_count=provider_call_count,
            conservative_cost_usd=conservative_cost_usd,
        )
        if provider_http_exchange_count is not None:
            event["provider_http_exchange_count"] = provider_http_exchange_count
    return event


class _CliRefusal(Exception):
    def __init__(self, reason_code: str, exit_code: int) -> None:
        self.reason_code = reason_code
        self.exit_code = exit_code


_ENVIRONMENT_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_RESTRICTED_KEYS = {
    "artifact_kind",
    "schema_version",
    "provider",
    "generation",
    "budget",
}
_PROVIDER_KEYS = {
    "provider_kind",
    "deployment",
    "model_version",
    "endpoint_env",
    "api_key_env",
    "secret_sentinel_envs",
    "request_timeout_seconds",
}


def _read_bytes(path: Path, reason: str) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise OSError
            return stream.read()
    except OSError as error:
        raise _CliRefusal(reason, 2) from error


def _parse_object(payload: bytes, reason: str, *, exit_code: int = 2) -> dict[str, Any]:
    from triana_labs.case_factory.primitives import Invalid, strict_json

    try:
        value = strict_json(payload)
    except Invalid as error:
        raise _CliRefusal(reason, exit_code) from error
    if not isinstance(value, dict):
        raise _CliRefusal(reason, exit_code)
    return value


def _read_config(path: Path) -> dict[str, Any]:
    return _parse_object(_read_bytes(path, "CONFIG_INVALID"), "CONFIG_INVALID")


def _restricted_configuration(
    config: dict[str, Any], environ: Mapping[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        provider = config["provider"]
        generation = config["generation"]
        budget = config["budget"]
        if (
            set(config)
            not in (_RESTRICTED_KEYS, _RESTRICTED_KEYS | {"protocol_version"})
            or config["artifact_kind"] != "case_factory_restricted_config"
            or type(config["schema_version"]) is not int
            or config["schema_version"] != 1
            or not isinstance(provider, dict)
            or set(provider) != _PROVIDER_KEYS
            or provider["provider_kind"] != "MICROSOFT_FOUNDRY_FIREWORKS"
            or provider["deployment"] != "FW-GLM-5.2"
            or provider["model_version"] != "1"
            or type(provider["request_timeout_seconds"]) is not int
            or not 1 <= provider["request_timeout_seconds"] <= 600
            or not isinstance(generation, dict)
            or set(generation)
            not in (
                {"candidate_count"},
                {"candidate_count", "evidence_byte_limit", "seed"},
            )
            or type(generation["candidate_count"]) is not int
            or generation["candidate_count"] not in {5, 12}
            or not isinstance(budget, dict)
            or set(budget) != {"max_usd", "reservation_usd_per_agent_call"}
        ):
            raise _CliRefusal("CONFIG_INVALID", 2)
        closure = config.get("protocol_version") == "LABS046_WORKFLOW_CLOSURE_V1"
        if (
            closure != (generation["candidate_count"] == 12)
            or closure
            and generation
            != {
                "candidate_count": 12,
                "evidence_byte_limit": 90_000,
                "seed": 2026080104,
            }
        ):
            raise _CliRefusal("CONFIG_INVALID", 2)
        names = [provider["endpoint_env"], provider["api_key_env"]]
        sentinels = provider["secret_sentinel_envs"]
        if (
            any(
                not isinstance(name, str) or not _ENVIRONMENT_NAME.fullmatch(name)
                for name in names
            )
            or not isinstance(sentinels, list)
            or any(
                not isinstance(name, str) or not _ENVIRONMENT_NAME.fullmatch(name)
                for name in sentinels
            )
            or len(sentinels) != len(set(sentinels))
        ):
            raise _CliRefusal("CONFIG_INVALID", 2)
        maximum = _money_decimal(budget["max_usd"])
        reservation = _money_decimal(budget["reservation_usd_per_agent_call"])
        if not Decimal(0) <= maximum <= Decimal(25) or reservation < 0:
            raise _CliRefusal("CONFIG_INVALID", 2)
    except (KeyError, TypeError, ValueError):
        raise _CliRefusal("CONFIG_INVALID", 2) from None

    endpoint = environ.get(provider["endpoint_env"])
    api_key = environ.get(provider["api_key_env"])
    if endpoint is None or api_key is None or not api_key.strip():
        raise _CliRefusal("PROVIDER_CONFIGURATION_MISSING", 2)
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise _CliRefusal("CONFIG_INVALID", 2)
    normalized = dict(environ)
    normalized[provider["endpoint_env"]] = endpoint.rstrip("/")
    return config, normalized


def _money_decimal(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise _CliRefusal("CONFIG_INVALID", 2)
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise _CliRefusal("CONFIG_INVALID", 2) from error
    if not result.is_finite():
        raise _CliRefusal("CONFIG_INVALID", 2)
    return result


def _build_restricted_transport(
    config: dict[str, Any], environ: Mapping[str, str]
) -> Any:
    from triana_labs.case_factory.restricted_runtime import (
        FoundryGLMRestrictedTransport,
    )

    provider = config["provider"]
    return FoundryGLMRestrictedTransport(
        environ[provider["endpoint_env"]],
        environ[provider["api_key_env"]],
        timeout_seconds=provider["request_timeout_seconds"],
    )


def _artifact_hash(payload: bytes) -> str:
    from triana_labs.case_factory.primitives import artifact_hash

    return artifact_hash(payload)


def _resume_state(pause_manifest: Path) -> dict[str, Any]:
    if not pause_manifest.is_file():
        raise _CliRefusal("RESUME_STATE_UNAVAILABLE", 5)
    state_path = pause_manifest.parent / "resume_state.json"
    try:
        state = _parse_object(
            state_path.read_bytes(), "RESUME_STATE_UNAVAILABLE", exit_code=5
        )
    except OSError as error:
        raise _CliRefusal("RESUME_STATE_UNAVAILABLE", 5) from error
    if not isinstance(state.get("question_ids"), list) or not isinstance(
        state.get("run_id"), str
    ):
        raise _CliRefusal("RESUME_STATE_UNAVAILABLE", 5)
    return state


def _resume_answers(path: Path, state: dict[str, Any]) -> dict[str, str]:
    from triana_labs.case_factory.primitives import bounded_text

    answers = _parse_object(
        _read_bytes(path, "RESUME_INPUT_INVALID"), "RESUME_INPUT_INVALID"
    )
    expected = state["question_ids"]
    if (
        any(not isinstance(item, str) for item in expected)
        or set(answers) != set(expected)
        or any(not bounded_text(value, 4096) for value in answers.values())
    ):
        raise _CliRefusal("RESUME_INPUT_INVALID", 2)
    return answers


def _require_private_resume_state(cache: Path, state: dict[str, Any]) -> None:
    run_id = state["run_id"]
    if not run_id.startswith("sha256:") or len(run_id) != 71:
        raise _CliRefusal("RESUME_STATE_UNAVAILABLE", 5)
    private = cache / "runs" / run_id.removeprefix("sha256:") / "resume-private.json"
    if not private.is_file():
        raise _CliRefusal("RESUME_STATE_UNAVAILABLE", 5)


def _write_case_refusal(command: str, reason: str, start: int) -> None:
    _write_json(
        sys.stderr,
        _case_terminal_log(
            command=command,
            event_name=f"triana.{command}.rejected",
            severity="ERROR",
            outcome="REJECTED",
            reason_code=reason,
            duration_ms=_duration_ms(start),
        ),
    )


def _write_restricted_result(result: Any, command: str, start: int) -> int:
    suffix = {
        "COMPLETED": "completed",
        "COMPLETED_WITH_GAPS": "completed_with_gaps",
        "NEEDS_INPUT": "needs_input",
        "REJECTED": "rejected",
    }[result.outcome]
    _write_json(
        sys.stdout,
        {
            "outcome": result.outcome,
            "reason_code": result.reason_code,
            "manifest_path": str(result.manifest_path),
            "questions_path": (
                str(result.manifest_path.parent / "questions.json")
                if result.outcome == "NEEDS_INPUT"
                else None
            ),
            "attempted_case_count": result.attempted_case_count,
            "valid_case_count": result.valid_case_count,
            "distinct_case_count": result.distinct_case_count,
            "provider_call_count": result.provider_call_count,
            "provider_http_exchange_count": result.provider_http_exchange_count,
            "conservative_cost_usd": result.conservative_cost_usd,
        },
    )
    _write_json(
        sys.stderr,
        _case_terminal_log(
            command=command,
            event_name=f"triana.{command}.{suffix}",
            severity="INFO",
            outcome=result.outcome,
            reason_code=result.reason_code,
            duration_ms=_duration_ms(start),
            attempted_case_count=result.attempted_case_count,
            valid_case_count=result.valid_case_count,
            distinct_case_count=result.distinct_case_count,
            provider_call_count=result.provider_call_count,
            provider_http_exchange_count=result.provider_http_exchange_count,
            conservative_cost_usd=result.conservative_cost_usd,
        ),
    )
    return {
        "COMPLETED": 0,
        "COMPLETED_WITH_GAPS": 10,
        "NEEDS_INPUT": 11,
        "REJECTED": 8,
    }[result.outcome]
