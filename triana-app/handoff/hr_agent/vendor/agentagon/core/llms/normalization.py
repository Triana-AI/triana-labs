"""LLM model-name normalization helpers."""

from __future__ import annotations


def normalize_llm_model_name(model: str | None) -> str:
    if model is None:
        return ""

    normalized_model = str(model).strip().lower().rstrip("/")
    if not normalized_model:
        return ""

    for resource_marker in (
        "/models/",
        "/foundation-model/",
        "/inference-profile/",
    ):
        if resource_marker in normalized_model:
            normalized_model = normalized_model.rsplit(resource_marker, 1)[1]
            break
    else:
        if normalized_model.startswith("models/"):
            normalized_model = normalized_model.removeprefix("models/")

    if "/" in normalized_model:
        normalized_model = normalized_model.rsplit("/", 1)[1]

    if "@" in normalized_model:
        normalized_model = normalized_model.split("@", 1)[0]

    model_segments = normalized_model.split(".")
    if (
        len(model_segments) >= 3
        and model_segments[0] in {"apac", "eu", "global", "us"}
        and model_segments[1] in {"amazon", "anthropic", "cohere", "meta", "mistral"}
    ):
        normalized_model = ".".join(model_segments[1:])

    for provider_prefix in (
        "openai/",
        "azure/openai/",
        "azure/",
        "anthropic/",
        "anthropic.",
        "google/",
        "gemini/",
    ):
        if normalized_model.startswith(provider_prefix):
            normalized_model = normalized_model.removeprefix(provider_prefix)
            break

    if _looks_like_openai_fine_tuned_model(normalized_model):
        return normalized_model

    if ":" in normalized_model:
        normalized_model = normalized_model.split(":", 1)[0]

    base_model, separator, version_suffix = normalized_model.rpartition("-")
    if (
        separator == "-"
        and version_suffix.startswith("v")
        and version_suffix[1:].isdigit()
    ):
        return base_model
    return normalized_model


def _looks_like_openai_fine_tuned_model(model: str) -> bool:
    return model.startswith(("ft:gpt", "ft:o"))


__all__ = ["normalize_llm_model_name"]
