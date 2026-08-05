"""Pinned, cached structured-model boundary for Exploration V1."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Protocol

import litellm  # type: ignore[import-not-found]


class StructuredModel(Protocol):
    model_id: str

    def complete_json(
        self, *, stage: str, prompt_version: str, system: str, payload: dict[str, Any]
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class CachedLiteLLMModel:
    model_id: str
    cache_dir: Path
    api_base: str | None = None
    api_key_env: str = "OPENROUTER_API_KEY"
    provider: str = "openrouter"
    aws_region_name: str | None = None
    temperature: float = 0.0
    timeout: int = 120
    num_retries: int = 2
    calls: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def complete_json(
        self, *, stage: str, prompt_version: str, system: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        key = hashlib.sha256(
            "\0".join((self.model_id, stage, prompt_version, system, canonical)).encode()
        ).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.is_file():
            with self._lock:
                self.cache_hits += 1
            result = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(result, dict):
                raise RuntimeError(f"Invalid cached object for {stage}")
            return result
        is_bedrock = self.provider == "bedrock" or self.model_id.startswith("bedrock/")
        completion_kwargs: dict[str, Any] = dict(
            model=self.model_id,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": canonical},
            ],
            num_retries=self.num_retries,
            timeout=self.timeout,
        )
        if is_bedrock:
            # Bedrock auth resolves via the boto3 credential chain (AWS_PROFILE);
            # no api_key/api_base to pass, unlike the OpenRouter path.
            completion_kwargs["aws_region_name"] = self.aws_region_name
        else:
            api_key = os.environ.get(self.api_key_env)
            if not api_key:
                raise RuntimeError(f"{self.api_key_env} is required for uncached semantic work")
            completion_kwargs["api_base"] = self.api_base
            completion_kwargs["api_key"] = api_key
        try:
            response = litellm.completion(**completion_kwargs)
        except Exception as error:
            raise RuntimeError(
                f"Structured model call failed at {stage} ({self.model_id}, {prompt_version}): {error}"
            ) from error
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        if not isinstance(result, dict):
            raise RuntimeError(f"Model returned a non-object for {stage}")
        usage = getattr(response, "usage", None)
        with self._lock:
            self.calls += 1
            self.input_tokens += int(getattr(usage, "prompt_tokens", 0) or 0)
            self.output_tokens += int(getattr(usage, "completion_tokens", 0) or 0)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, sort_keys=True, ensure_ascii=True) + "\n")
        return result

    def usage(self) -> dict[str, int | str]:
        return {
            "model_id": self.model_id,
            "calls": self.calls,
            "cache_hits": self.cache_hits,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
