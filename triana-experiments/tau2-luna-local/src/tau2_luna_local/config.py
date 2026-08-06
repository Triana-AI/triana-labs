from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class ConfigurationError(ValueError):
    """Raised before egress when the explicit run configuration is unsafe."""


_REQUIRED = ("AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION", "TAU2_LUNA_DEPLOYMENT")
_AZURE_SUFFIXES = (".openai.azure.com", ".services.ai.azure.com", ".cognitiveservices.azure.com")


@dataclass(frozen=True)
class Config:
    api_key: str
    api_base: str
    api_version: str
    deployment: str
    trace_root: Path
    domain: str = "retail"
    task_id: str | None = None
    task_count: int = 1
    trial_count: int = 1
    seed: int = 1729
    max_steps: int = 100
    max_errors: int = 10
    concurrency: int = 1

    @property
    def model(self) -> str:
        return f"azure/{self.deployment}"

    @property
    def endpoint_host(self) -> str:
        return (urlparse(self.api_base).hostname or "").lower()

    def safe_projection(self) -> dict[str, object]:
        return {
            "model": self.model,
            "endpoint_host": self.endpoint_host,
            "api_version": self.api_version,
            "domain": self.domain,
            "task_id": self.task_id,
            "task_count": self.task_count,
            "trial_count": self.trial_count,
            "seed": self.seed,
            "max_steps": self.max_steps,
            "max_errors": self.max_errors,
            "concurrency": self.concurrency,
            "environment_presence": {"AZURE_API_KEY": bool(self.api_key)},
        }


def _required_value(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} is required and must be non-empty")
    return value


def _bounded(name: str, value: int, minimum: int, maximum: int) -> int:
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum} and {maximum}")
    return value


def load_config(
    environ: Mapping[str, str] | None = None,
    *,
    domain: str = "retail",
    task_id: str | None = None,
    task_count: int = 1,
    trial_count: int = 1,
    seed: int = 1729,
    max_steps: int = 100,
    max_errors: int = 10,
    concurrency: int = 1,
) -> Config:
    source = os.environ if environ is None else environ
    values = {name: _required_value(source, name) for name in _REQUIRED}
    parsed = urlparse(values["AZURE_API_BASE"])
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not any(host.endswith(suffix) for suffix in _AZURE_SUFFIXES):
        raise ConfigurationError("AZURE_API_BASE must be an HTTPS Microsoft Azure AI endpoint")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ConfigurationError("AZURE_API_BASE must not contain credentials, a query, or a fragment")
    if not domain.strip():
        raise ConfigurationError("domain must be non-empty")
    trace_root = Path(source.get("TAU2_TRACE_ROOT", "./runs")).expanduser()
    if trace_root.resolve() == Path(trace_root.anchor or "/"):
        raise ConfigurationError("TAU2_TRACE_ROOT may not be a filesystem root")
    return Config(
        api_key=values["AZURE_API_KEY"],
        api_base=values["AZURE_API_BASE"],
        api_version=values["AZURE_API_VERSION"],
        deployment=values["TAU2_LUNA_DEPLOYMENT"],
        trace_root=trace_root,
        domain=domain.strip(),
        task_id=task_id,
        task_count=_bounded("task_count", task_count, 1, 1),
        trial_count=_bounded("trial_count", trial_count, 1, 1),
        seed=_bounded("seed", seed, 0, 2**31 - 1),
        max_steps=_bounded("max_steps", max_steps, 1, 1000),
        max_errors=_bounded("max_errors", max_errors, 1, 100),
        concurrency=_bounded("concurrency", concurrency, 1, 1),
    )
