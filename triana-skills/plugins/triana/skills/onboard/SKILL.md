---
name: onboard
description: Prepare operator-authorized local conversational trace JSONL for Triana Preview. Use when Codex or Claude Code needs to inspect an unfamiliar trace schema without exposing values, validate existing PreviewTrace v1 data, scaffold a bounded local adapter, preview redacted validation evidence, or construct a digest-pinned private Triana Preview Docker command without executing it.
---

# Onboard traces to Triana Preview

Keep raw traces local. Require the operator's explicit authorization before
reading them, and never infer missing messages, roles, tool links, timestamps,
or authorization.

## Workflow

1. Ask for the local trace path and a one-to-three-line agent description.
2. Ask the operator to confirm they are authorized to analyze the traces.
3. Run structural inspection. It reports keys and types, never source values:

   ```sh
   python scripts/onboard.py inspect --source /absolute/traces.jsonl \
     --confirm-authorized-traces
   ```

4. Try exact PreviewTrace v1 validation. Valid input is copied byte-for-byte
   to a new local destination:

   ```sh
   python scripts/onboard.py validate --source /absolute/traces.jsonl \
     --output /absolute/validated.jsonl --confirm-authorized-traces
   ```

5. If validation refuses because the source schema is different, scaffold the
   adapter seam. Complete only the marked mapping function using facts visible
   in the customer's schema. Do not create defaults for absent evidence:

   ```sh
   python scripts/onboard.py scaffold --source /absolute/traces.jsonl \
     --output-dir /absolute/new-adapter --confirm-authorized-traces
   ```

6. Run the completed adapter locally, validate its output, then inspect at most
   three redacted previews:

   ```sh
   python scripts/onboard.py preview --source /absolute/validated.jsonl \
     --confirm-authorized-traces
   ```

7. After receiving a separately published private release manifest, construct
   the exact Docker argv. This command prints JSON and never starts Docker:

   ```sh
   python scripts/onboard.py docker-command \
     --source /absolute/validated.jsonl \
     --output-dir /absolute/private-output \
     --agent "Order-support agent that tracks and changes deliveries." \
     --release-manifest /absolute/release-manifest.json \
     --confirm-authorized-traces
   ```

8. Show the operator the generated argv and ask them whether to execute it.
   Do not add credentials, provider fallback, uploads, or mutable image tags.

9. Start with a deterministic, no-network run: omit all
   `TRIANA_BEHAVIOR_MAP_*` provider variables and do not add `--env-file`.
   Treat unavailable semantic analysis as a typed gap.

10. Enable semantic analysis only after the operator explicitly chooses it.
    Have the operator create a private environment file from Triana Preview's
    `.env.example`, fill every field, and pass that exact file with
    `--env-file`. A complete explicit configuration authorizes provider egress.
    Preserve each full OpenAI-v1 base URL, including its path such as
    `/openai/v1`. Never infer credentials or provider settings, and never add
    fallback or retry behavior.

Read [references/previewtrace-v1.md](references/previewtrace-v1.md) before
implementing an adapter. Use [assets/adapter.py.template](assets/adapter.py.template)
only through the deterministic scaffold command.

## Refusals

Treat every nonzero result as a stop condition. Do not turn
`TRACE_AUTHORIZATION_REQUIRED`, `TRACE_SOURCE_UNSAFE`,
`TRACE_SOURCE_INVALID`, `ADAPTER_OUTPUT_INVALID`, `PREVIEWTRACE_INVALID`,
`RELEASE_UNPUBLISHED`, or `RELEASE_IMAGE_NOT_DIGEST_PINNED` into success.
