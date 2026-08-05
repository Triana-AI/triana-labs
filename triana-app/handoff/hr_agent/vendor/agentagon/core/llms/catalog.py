"""Internal LLM model metadata catalog."""

from __future__ import annotations

from agentagon.core.llms.normalization import normalize_llm_model_name
from agentagon.core.llms.types import LLMModelInfo


def _build_model_infos() -> dict[str, LLMModelInfo]:
    model_infos: dict[str, LLMModelInfo] = {}

    def add(model_info: LLMModelInfo, *aliases: str) -> None:
        for model in (model_info.model, *aliases):
            model_infos[normalize_llm_model_name(model)] = model_info

    def add_info(
        *,
        model: str,
        provider: str,
        context_window_tokens: int | None = None,
        max_output_tokens: int | None = None,
        input_price_per_million_tokens: float | None = None,
        output_price_per_million_tokens: float | None = None,
        input_price_per_million_tokens_long_context: float | None = None,
        output_price_per_million_tokens_long_context: float | None = None,
        long_context_threshold_tokens: int | None = None,
        pricing_notes: str | None = None,
        aliases: tuple[str, ...] = (),
    ) -> None:
        add(
            LLMModelInfo(
                model=model,
                provider=provider,
                context_window_tokens=context_window_tokens,
                max_output_tokens=max_output_tokens,
                input_price_per_million_tokens=input_price_per_million_tokens,
                output_price_per_million_tokens=output_price_per_million_tokens,
                input_price_per_million_tokens_long_context=(
                    input_price_per_million_tokens_long_context
                ),
                output_price_per_million_tokens_long_context=(
                    output_price_per_million_tokens_long_context
                ),
                long_context_threshold_tokens=long_context_threshold_tokens,
                pricing_notes=pricing_notes,
            ),
            *aliases,
        )

    add_info(
        model="gpt-5.5",
        provider="openai",
        context_window_tokens=1_050_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=5.0,
        output_price_per_million_tokens=30.0,
        input_price_per_million_tokens_long_context=10.0,
        output_price_per_million_tokens_long_context=45.0,
        long_context_threshold_tokens=272_000,
        pricing_notes=(
            "OpenAI prices GPT-5.5 prompts with more than 272K input tokens "
            "at 2x input and 1.5x output for the full session."
        ),
    )
    add_info(
        model="gpt-5.5-pro",
        provider="openai",
        context_window_tokens=1_050_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=30.0,
        output_price_per_million_tokens=180.0,
        input_price_per_million_tokens_long_context=60.0,
        output_price_per_million_tokens_long_context=270.0,
        pricing_notes=(
            "OpenAI publishes separate short-context and long-context rates; "
            "GPT-5.5 Pro does not offer a cached-input discount."
        ),
    )
    add_info(
        model="gpt-5.4",
        provider="openai",
        context_window_tokens=1_050_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=2.5,
        output_price_per_million_tokens=15.0,
        input_price_per_million_tokens_long_context=5.0,
        output_price_per_million_tokens_long_context=22.5,
        long_context_threshold_tokens=272_000,
        pricing_notes=(
            "OpenAI prices GPT-5.4 prompts with more than 272K input tokens "
            "at 2x input and 1.5x output for the full session."
        ),
    )
    add_info(
        model="gpt-5.4-pro",
        provider="openai",
        context_window_tokens=1_050_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=30.0,
        output_price_per_million_tokens=180.0,
        input_price_per_million_tokens_long_context=60.0,
        output_price_per_million_tokens_long_context=270.0,
        long_context_threshold_tokens=272_000,
        pricing_notes=(
            "OpenAI prices GPT-5.4 Pro prompts with more than 272K input "
            "tokens at 2x input and 1.5x output for the full session."
        ),
    )
    add_info(
        model="gpt-5.4-mini",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=0.75,
        output_price_per_million_tokens=4.5,
    )
    add_info(
        model="gpt-5.4-nano",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=0.2,
        output_price_per_million_tokens=1.25,
    )
    add_info(
        model="gpt-5.3-codex",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.75,
        output_price_per_million_tokens=14.0,
        pricing_notes=(
            "OpenAI lists GPT-5.3-Codex as an agentic coding model with "
            "GPT-5.2-class pricing."
        ),
    )
    add_info(
        model="gpt-5.2",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.75,
        output_price_per_million_tokens=14.0,
        pricing_notes=(
            "OpenAI model docs list GPT-5.2 as a previous frontier model and "
            "recommend GPT-5.5 for new work."
        ),
    )
    add_info(
        model="gpt-5.2-codex",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.75,
        output_price_per_million_tokens=14.0,
        pricing_notes=(
            "OpenAI lists GPT-5.2-Codex as an agentic coding model with "
            "GPT-5.2-class pricing."
        ),
    )
    add_info(
        model="gpt-5.1",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.25,
        output_price_per_million_tokens=10.0,
        pricing_notes=(
            "OpenAI model docs list GPT-5.1 as a previous coding and agentic "
            "model and recommend GPT-5.5 for new work."
        ),
    )
    add_info(
        model="gpt-5.1-codex",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.25,
        output_price_per_million_tokens=10.0,
        pricing_notes=(
            "OpenAI lists GPT-5.1-Codex as an agentic coding model with "
            "GPT-5.1-class pricing."
        ),
    )
    add_info(
        model="gpt-5",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.25,
        output_price_per_million_tokens=10.0,
        pricing_notes=(
            "OpenAI model docs list GPT-5 as a previous reasoning model and "
            "recommend GPT-5.5 for new work."
        ),
    )
    add_info(
        model="gpt-5-codex",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=1.25,
        output_price_per_million_tokens=10.0,
        pricing_notes=(
            "OpenAI lists GPT-5-Codex as an agentic coding model with "
            "GPT-5-class pricing."
        ),
    )
    add_info(
        model="gpt-5-mini",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=0.25,
        output_price_per_million_tokens=2.0,
        pricing_notes=(
            "OpenAI model docs list GPT-5 mini as previous-generation and "
            "recommend GPT-5.4 mini for most new low-latency workloads."
        ),
    )
    add_info(
        model="gpt-5-nano",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=0.05,
        output_price_per_million_tokens=0.4,
        pricing_notes=(
            "OpenAI model docs list GPT-5 nano as previous-generation and "
            "recommend GPT-5.4 nano for most new speed-sensitive workloads."
        ),
    )
    add_info(
        model="gpt-4.1",
        provider="openai",
        context_window_tokens=1_047_576,
        max_output_tokens=32_768,
        input_price_per_million_tokens=2.0,
        output_price_per_million_tokens=8.0,
        pricing_notes="OpenAI launch documentation lists GPT-4.1 API pricing.",
    )
    add_info(
        model="gpt-4.1-mini",
        provider="openai",
        context_window_tokens=1_047_576,
        max_output_tokens=32_768,
        input_price_per_million_tokens=0.4,
        output_price_per_million_tokens=1.6,
        pricing_notes="OpenAI launch documentation lists GPT-4.1 mini API pricing.",
    )
    add_info(
        model="gpt-4.1-nano",
        provider="openai",
        context_window_tokens=1_047_576,
        max_output_tokens=32_768,
        input_price_per_million_tokens=0.1,
        output_price_per_million_tokens=0.4,
        pricing_notes="OpenAI model docs list GPT-4.1 nano API pricing.",
    )
    add_info(
        model="gpt-4o",
        provider="openai",
        context_window_tokens=128_000,
        max_output_tokens=16_384,
        input_price_per_million_tokens=2.5,
        output_price_per_million_tokens=10.0,
        pricing_notes=(
            "OpenAI model docs list GPT-4o as a legacy omni model; latest "
            "deprecation docs recommend GPT-5.5 for dated GPT-4o snapshots."
        ),
    )
    add_info(
        model="gpt-4o-mini",
        provider="openai",
        context_window_tokens=128_000,
        max_output_tokens=16_384,
        input_price_per_million_tokens=0.15,
        output_price_per_million_tokens=0.6,
        pricing_notes="OpenAI launch documentation lists GPT-4o mini API pricing.",
    )
    add_info(
        model="chat-latest",
        provider="openai",
        context_window_tokens=400_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=5.0,
        output_price_per_million_tokens=30.0,
        pricing_notes=(
            "OpenAI model docs list chat-latest as the latest Instant model "
            "used in ChatGPT and recommend GPT-5.5 for production API usage."
        ),
    )
    add_info(
        model="o3",
        provider="openai",
        context_window_tokens=200_000,
        max_output_tokens=100_000,
        input_price_per_million_tokens=2.0,
        output_price_per_million_tokens=8.0,
        pricing_notes=(
            "OpenAI model docs list o3 as a reasoning model succeeded by GPT-5."
        ),
    )
    add_info(
        model="o3-pro",
        provider="openai",
        context_window_tokens=200_000,
        max_output_tokens=100_000,
        input_price_per_million_tokens=20.0,
        output_price_per_million_tokens=80.0,
        pricing_notes="OpenAI model docs list o3-pro as a higher-compute o3 variant.",
    )
    add_info(
        model="o4-mini",
        provider="openai",
        context_window_tokens=200_000,
        max_output_tokens=100_000,
        input_price_per_million_tokens=1.1,
        output_price_per_million_tokens=4.4,
        pricing_notes=(
            "OpenAI model docs list o4-mini as a small reasoning model "
            "succeeded by GPT-5 mini."
        ),
    )
    add_info(
        model="o3-mini",
        provider="openai",
        context_window_tokens=200_000,
        max_output_tokens=100_000,
        input_price_per_million_tokens=1.1,
        output_price_per_million_tokens=4.4,
        pricing_notes="OpenAI model docs list o3-mini as a small reasoning model.",
    )
    add_info(
        model="o1",
        provider="openai",
        context_window_tokens=200_000,
        max_output_tokens=100_000,
        input_price_per_million_tokens=15.0,
        output_price_per_million_tokens=60.0,
        pricing_notes="OpenAI model docs list o1 as a previous full o-series model.",
    )
    add_info(
        model="o1-mini",
        provider="openai",
        context_window_tokens=128_000,
        max_output_tokens=65_536,
        input_price_per_million_tokens=1.1,
        output_price_per_million_tokens=4.4,
        pricing_notes=(
            "OpenAI model docs list o1-mini as a previous small reasoning model "
            "and recommend o3-mini instead."
        ),
    )

    add_info(
        model="claude-fable-5",
        provider="anthropic",
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=10.0,
        output_price_per_million_tokens=50.0,
    )
    add_info(
        model="claude-mythos-5",
        provider="anthropic",
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=10.0,
        output_price_per_million_tokens=50.0,
        pricing_notes="Limited availability through Project Glasswing.",
    )
    add_info(
        model="claude-opus-4-8",
        provider="anthropic",
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=5.0,
        output_price_per_million_tokens=25.0,
    )
    add_info(
        model="claude-opus-4-7",
        provider="anthropic",
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=5.0,
        output_price_per_million_tokens=25.0,
        pricing_notes=(
            "Anthropic pricing docs state Opus 4.7 includes the full 1M-token "
            "context window at standard pricing."
        ),
    )
    add_info(
        model="claude-opus-4-6",
        provider="anthropic",
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=5.0,
        output_price_per_million_tokens=25.0,
        pricing_notes=(
            "Anthropic pricing docs state Opus 4.6 includes the full 1M-token "
            "context window at standard pricing."
        ),
    )
    add_info(
        model="claude-opus-4-5",
        provider="anthropic",
        context_window_tokens=200_000,
        max_output_tokens=64_000,
        input_price_per_million_tokens=5.0,
        output_price_per_million_tokens=25.0,
        pricing_notes=(
            "Claude 4.5-generation model; newer 1M-token long-context pricing "
            "starts with Opus 4.6, Opus 4.7, Opus 4.8, and Sonnet 4.6."
        ),
    )
    add_info(
        model="claude-sonnet-4-6",
        provider="anthropic",
        context_window_tokens=1_000_000,
        max_output_tokens=128_000,
        input_price_per_million_tokens=3.0,
        output_price_per_million_tokens=15.0,
    )
    add_info(
        model="claude-sonnet-4-5",
        provider="anthropic",
        context_window_tokens=200_000,
        max_output_tokens=64_000,
        input_price_per_million_tokens=3.0,
        output_price_per_million_tokens=15.0,
        pricing_notes=(
            "Claude 4.5-generation model; Sonnet 4.6 is the first Sonnet model "
            "listed with the full 1M-token context window."
        ),
    )
    add_info(
        model="claude-haiku-4-5",
        provider="anthropic",
        context_window_tokens=200_000,
        max_output_tokens=64_000,
        input_price_per_million_tokens=1.0,
        output_price_per_million_tokens=5.0,
    )

    add_info(
        model="gemini-3.5-flash",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=1.5,
        output_price_per_million_tokens=9.0,
        pricing_notes="Google Gemini API standard paid-tier text/image/video pricing.",
    )
    add_info(
        model="gemini-3-flash-preview",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=0.5,
        output_price_per_million_tokens=3.0,
        pricing_notes=(
            "Google Gemini API standard paid-tier text/image/video pricing for "
            "the preview endpoint."
        ),
    )
    add_info(
        model="gemini-3.1-pro-preview",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=2.0,
        output_price_per_million_tokens=12.0,
        input_price_per_million_tokens_long_context=4.0,
        output_price_per_million_tokens_long_context=18.0,
        long_context_threshold_tokens=200_000,
        aliases=("gemini-3.1-pro", "gemini-3.1-pro-preview-customtools"),
    )
    add_info(
        model="gemini-3.1-flash-lite",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=0.25,
        output_price_per_million_tokens=1.5,
    )
    add_info(
        model="gemini-2.5-pro",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=1.25,
        output_price_per_million_tokens=10.0,
        input_price_per_million_tokens_long_context=2.5,
        output_price_per_million_tokens_long_context=15.0,
        long_context_threshold_tokens=200_000,
    )
    add_info(
        model="gemini-2.5-flash",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=0.3,
        output_price_per_million_tokens=2.5,
    )
    add_info(
        model="gemini-2.5-flash-lite",
        provider="google",
        context_window_tokens=1_048_576,
        max_output_tokens=65_536,
        input_price_per_million_tokens=0.1,
        output_price_per_million_tokens=0.4,
    )

    return model_infos


_MODEL_INFOS: dict[str, LLMModelInfo] = _build_model_infos()


def lookup_llm_model_info(model: str | None) -> LLMModelInfo | None:
    model_key = normalize_llm_model_name(model)
    if not model_key:
        return None

    model_info = _MODEL_INFOS.get(model_key)
    if model_info is not None:
        return model_info

    for known_model_key, known_model_info in _model_info_prefixes():
        if model_key == known_model_key:
            return known_model_info

        if model_key.startswith(f"{known_model_key}-") and _has_snapshot_suffix(
            model_key.removeprefix(f"{known_model_key}-")
        ):
            return known_model_info
    return None


def list_llm_model_infos() -> tuple[LLMModelInfo, ...]:
    return tuple(
        sorted(
            set(_MODEL_INFOS.values()),
            key=lambda model_info: (
                model_info.provider or "",
                model_info.model,
            ),
        )
    )


def register_llm_model_info(model_info: LLMModelInfo) -> None:
    _MODEL_INFOS[normalize_llm_model_name(model_info.model)] = model_info


def unregister_llm_model_info(model: str) -> None:
    _MODEL_INFOS.pop(normalize_llm_model_name(model), None)


def _has_snapshot_suffix(suffix: str) -> bool:
    first_segment = suffix.split("-", 1)[0]
    if len(first_segment) == 8 and first_segment.isdigit():
        return True

    date_segments = suffix.split("-", 3)
    return (
        len(date_segments) >= 3
        and len(date_segments[0]) == 4
        and len(date_segments[1]) == 2
        and len(date_segments[2]) == 2
        and all(segment.isdigit() for segment in date_segments[:3])
    )


def _model_info_prefixes() -> tuple[tuple[str, LLMModelInfo], ...]:
    return tuple(
        sorted(
            _MODEL_INFOS.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )
    )


__all__ = [
    "list_llm_model_infos",
    "lookup_llm_model_info",
    "register_llm_model_info",
    "unregister_llm_model_info",
]
