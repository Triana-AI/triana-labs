# Supported LLM Models

This matrix mirrors the internal LLM model catalog in `catalog.py`.
Prices are in USD per 1M tokens. Context and max-output limits are token counts.
Scope: publicly documented text-output LLM/chat/reasoning/code models used
for LLM spans that still have public API access or future shutdown dates.
Specialized image, video, speech, transcription, embedding, search-preview,
deep-research, and already-shut-down models are intentionally excluded.
Model limits and pricing sources were last checked against the latest public
vendor docs on 2026-06-27:

- OpenAI API pricing and model/deprecation docs:
  https://developers.openai.com/api/docs/pricing,
  https://developers.openai.com/api/docs/models,
  https://developers.openai.com/api/docs/deprecations
- Anthropic Claude Platform pricing:
  https://platform.claude.com/docs/en/about-claude/pricing
- Google Gemini API pricing:
  https://ai.google.dev/gemini-api/docs/pricing

`gpt-5.6` is intentionally excluded until OpenAI publishes public API pricing;
the latest model docs describe it as a trusted-partner preview.

| Provider | Model | Lookup aliases | Context window | Max output | Input | Output | Long-context threshold | Long-context input | Long-context output | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| anthropic | `claude-fable-5` |  | 1,000,000 | 128,000 | 10.00 | 50.00 |  |  |  |  |
| anthropic | `claude-haiku-4-5` |  | 200,000 | 64,000 | 1.00 | 5.00 |  |  |  |  |
| anthropic | `claude-mythos-5` |  | 1,000,000 | 128,000 | 10.00 | 50.00 |  |  |  | Limited availability through Project Glasswing. |
| anthropic | `claude-opus-4-5` |  | 200,000 | 64,000 | 5.00 | 25.00 |  |  |  | Claude 4.5-generation model; newer 1M-token long-context pricing starts with Opus 4.6, Opus 4.7, Opus 4.8, and Sonnet 4.6. |
| anthropic | `claude-opus-4-6` |  | 1,000,000 | 128,000 | 5.00 | 25.00 |  |  |  | Anthropic pricing docs state Opus 4.6 includes the full 1M-token context window at standard pricing. |
| anthropic | `claude-opus-4-7` |  | 1,000,000 | 128,000 | 5.00 | 25.00 |  |  |  | Anthropic pricing docs state Opus 4.7 includes the full 1M-token context window at standard pricing. |
| anthropic | `claude-opus-4-8` |  | 1,000,000 | 128,000 | 5.00 | 25.00 |  |  |  |  |
| anthropic | `claude-sonnet-4-5` |  | 200,000 | 64,000 | 3.00 | 15.00 |  |  |  | Claude 4.5-generation model; Sonnet 4.6 is the first Sonnet model listed with the full 1M-token context window. |
| anthropic | `claude-sonnet-4-6` |  | 1,000,000 | 128,000 | 3.00 | 15.00 |  |  |  |  |
| google | `gemini-2.5-flash` |  | 1,048,576 | 65,536 | 0.30 | 2.50 |  |  |  |  |
| google | `gemini-2.5-flash-lite` |  | 1,048,576 | 65,536 | 0.10 | 0.40 |  |  |  |  |
| google | `gemini-2.5-pro` |  | 1,048,576 | 65,536 | 1.25 | 10.00 | 200,000 | 2.50 | 15.00 |  |
| google | `gemini-3.1-flash-lite` |  | 1,048,576 | 65,536 | 0.25 | 1.50 |  |  |  |  |
| google | `gemini-3.1-pro-preview` | `gemini-3.1-pro`, `gemini-3.1-pro-preview-customtools` | 1,048,576 | 65,536 | 2.00 | 12.00 | 200,000 | 4.00 | 18.00 |  |
| google | `gemini-3-flash-preview` |  | 1,048,576 | 65,536 | 0.50 | 3.00 |  |  |  | Google Gemini API standard paid-tier text/image/video pricing for the preview endpoint. |
| google | `gemini-3.5-flash` |  | 1,048,576 | 65,536 | 1.50 | 9.00 |  |  |  | Google Gemini API standard paid-tier text/image/video pricing. |
| openai | `chat-latest` |  | 400,000 | 128,000 | 5.00 | 30.00 |  |  |  | OpenAI model docs list chat-latest as the latest Instant model used in ChatGPT and recommend GPT-5.5 for production API usage. |
| openai | `gpt-4.1` |  | 1,047,576 | 32,768 | 2.00 | 8.00 |  |  |  | OpenAI launch documentation lists GPT-4.1 API pricing. |
| openai | `gpt-4.1-mini` |  | 1,047,576 | 32,768 | 0.40 | 1.60 |  |  |  | OpenAI launch documentation lists GPT-4.1 mini API pricing. |
| openai | `gpt-4.1-nano` |  | 1,047,576 | 32,768 | 0.10 | 0.40 |  |  |  | OpenAI model docs list GPT-4.1 nano API pricing. |
| openai | `gpt-4o` |  | 128,000 | 16,384 | 2.50 | 10.00 |  |  |  | OpenAI model docs list GPT-4o as a legacy omni model; latest deprecation docs recommend GPT-5.5 for dated GPT-4o snapshots. |
| openai | `gpt-4o-mini` |  | 128,000 | 16,384 | 0.15 | 0.60 |  |  |  | OpenAI launch documentation lists GPT-4o mini API pricing. |
| openai | `gpt-5` |  | 400,000 | 128,000 | 1.25 | 10.00 |  |  |  | OpenAI model docs list GPT-5 as a previous reasoning model and recommend GPT-5.5 for new work. |
| openai | `gpt-5-codex` |  | 400,000 | 128,000 | 1.25 | 10.00 |  |  |  | OpenAI lists GPT-5-Codex as an agentic coding model with GPT-5-class pricing. |
| openai | `gpt-5-mini` |  | 400,000 | 128,000 | 0.25 | 2.00 |  |  |  | OpenAI model docs list GPT-5 mini as previous-generation and recommend GPT-5.4 mini for most new low-latency workloads. |
| openai | `gpt-5-nano` |  | 400,000 | 128,000 | 0.05 | 0.40 |  |  |  | OpenAI model docs list GPT-5 nano as previous-generation and recommend GPT-5.4 nano for most new speed-sensitive workloads. |
| openai | `gpt-5.1` |  | 400,000 | 128,000 | 1.25 | 10.00 |  |  |  | OpenAI model docs list GPT-5.1 as a previous coding and agentic model and recommend GPT-5.5 for new work. |
| openai | `gpt-5.1-codex` |  | 400,000 | 128,000 | 1.25 | 10.00 |  |  |  | OpenAI lists GPT-5.1-Codex as an agentic coding model with GPT-5.1-class pricing. |
| openai | `gpt-5.2` |  | 400,000 | 128,000 | 1.75 | 14.00 |  |  |  | OpenAI model docs list GPT-5.2 as a previous frontier model and recommend GPT-5.5 for new work. |
| openai | `gpt-5.2-codex` |  | 400,000 | 128,000 | 1.75 | 14.00 |  |  |  | OpenAI lists GPT-5.2-Codex as an agentic coding model with GPT-5.2-class pricing. |
| openai | `gpt-5.3-codex` |  | 400,000 | 128,000 | 1.75 | 14.00 |  |  |  | OpenAI lists GPT-5.3-Codex as an agentic coding model with GPT-5.2-class pricing. |
| openai | `gpt-5.4` |  | 1,050,000 | 128,000 | 2.50 | 15.00 | 272,000 | 5.00 | 22.50 | OpenAI prices GPT-5.4 prompts with more than 272K input tokens at 2x input and 1.5x output for the full session. |
| openai | `gpt-5.4-mini` |  | 400,000 | 128,000 | 0.75 | 4.50 |  |  |  |  |
| openai | `gpt-5.4-nano` |  | 400,000 | 128,000 | 0.20 | 1.25 |  |  |  |  |
| openai | `gpt-5.4-pro` |  | 1,050,000 | 128,000 | 30.00 | 180.00 | 272,000 | 60.00 | 270.00 | OpenAI prices GPT-5.4 Pro prompts with more than 272K input tokens at 2x input and 1.5x output for the full session. |
| openai | `gpt-5.5` |  | 1,050,000 | 128,000 | 5.00 | 30.00 | 272,000 | 10.00 | 45.00 | OpenAI prices GPT-5.5 prompts with more than 272K input tokens at 2x input and 1.5x output for the full session. |
| openai | `gpt-5.5-pro` |  | 1,050,000 | 128,000 | 30.00 | 180.00 |  | 60.00 | 270.00 | OpenAI publishes separate short-context and long-context rates; GPT-5.5 Pro does not offer a cached-input discount. |
| openai | `o1` |  | 200,000 | 100,000 | 15.00 | 60.00 |  |  |  | OpenAI model docs list o1 as a previous full o-series model. |
| openai | `o1-mini` |  | 128,000 | 65,536 | 1.10 | 4.40 |  |  |  | OpenAI model docs list o1-mini as a previous small reasoning model and recommend o3-mini instead. |
| openai | `o3` |  | 200,000 | 100,000 | 2.00 | 8.00 |  |  |  | OpenAI model docs list o3 as a reasoning model succeeded by GPT-5. |
| openai | `o3-mini` |  | 200,000 | 100,000 | 1.10 | 4.40 |  |  |  | OpenAI model docs list o3-mini as a small reasoning model. |
| openai | `o3-pro` |  | 200,000 | 100,000 | 20.00 | 80.00 |  |  |  | OpenAI model docs list o3-pro as a higher-compute o3 variant. |
| openai | `o4-mini` |  | 200,000 | 100,000 | 1.10 | 4.40 |  |  |  | OpenAI model docs list o4-mini as a small reasoning model succeeded by GPT-5 mini. |
