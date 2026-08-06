from __future__ import annotations

UPSTREAM_REPOSITORY = "https://github.com/sierra-research/tau2-bench"
UPSTREAM_COMMIT = "f8de30c298689cbe0117d76a378e7315a17e5bd8"
UPSTREAM_RELEASE = "v0.2.0"

EVENT_SCHEMA = "tau2-luna-event/v1"
MANIFEST_SCHEMA = "tau2-luna-manifest/v1"
COMPLETENESS_SCHEMA = "tau2-luna-completeness/v1"
EVENT_DOMAIN = b"tau2-luna-local:event:v1\0"

BUNDLE_FILES = frozenset(
    {"events.jsonl", "spans.jsonl", "tau2-results.json", "manifest.json", "completeness.json"}
)
HASHED_ARTIFACTS = ("events.jsonl", "spans.jsonl", "tau2-results.json", "completeness.json")

REQUIRED_TELEMETRY = (
    "attempt.call_id",
    "attempt.role_lane",
    "attempt.start_time",
    "attempt.end_time",
    "attempt.duration",
    "attempt.number",
    "attempt.outcome",
    "request.model",
    "request.endpoint_host",
    "request.api_version",
    "request.kwargs",
    "request.messages",
    "request.tools",
    "request.tool_choice",
    "request.retry_setting",
    "response.mapping",
    "response.choices",
    "response.content",
    "response.tool_calls",
    "response.finish_reason",
    "response.identifiers",
    "response.created",
    "response.usage",
    "response.usage.prompt_tokens",
    "response.usage.completion_tokens",
    "response.usage.total_tokens",
    "response.usage.cached_tokens",
    "response.usage.reasoning_tokens",
    "response.cost",
    "response.headers",
    "response.hidden_metadata",
    "response.raw_class",
    "response.reasoning",
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
    "bundle.hashes",
    "verification.hashes",
    "provider_private_chain_of_thought",
)

TELEMETRY_STATES = frozenset({"CAPTURED", "NOT_RETURNED", "UNAVAILABLE", "INVALID"})
NON_SUCCESS_IF_MISSING = frozenset({"response.usage", "response.cost", "response.headers"})
