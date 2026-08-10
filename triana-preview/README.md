# Triana Preview

Triana Preview is an invite-only, local distribution facade for the one
repository-owned `triana-labs` Behavior Map engine. It does not fork analysis
logic. Updating the paired Labs dependency updates the engine used here.

## Local source run

Use Python 3.13.14 from the repository checkout:

```sh
cd triana-preview
uv sync --locked
uv run triana-preview analyze \
  --traces /absolute/path/to/preview-traces.jsonl \
  --agent "Order-support agent that tracks deliveries." \
  --output /absolute/path/to/new-output \
  --confirm-authorized-traces
```

The acknowledgement confirms that the operator is authorized to analyze the
declared traces. Raw traces are never copied to the output. The directory
contains a redacted local projection, a redaction audit, the evidence and run
manifests, and the canonical JSON, Markdown, and static HTML Behavior Map.

Use two explicit stages:

1. For the deterministic, no-network first run, omit every
   `TRIANA_BEHAVIOR_MAP_*` provider variable and do not pass an environment
   file. Accounting completes and semantic work remains a typed gap.
2. For semantic analysis, copy `.env.example` to a private file and fill every
   field explicitly. The complete configuration authorizes provider egress.
   Each endpoint must be the full OpenAI-v1 base URL, including its path (for
   example, `https://resource.openai.azure.com/openai/v1`).

Partial configuration is refused. Preview does not infer credentials, select a
provider, add fallback, or retry on the operator's behalf.

## Local container build and run

Build from the repository root so the image contains the paired Labs and
Preview source at the same commit:

```sh
docker build -f triana-preview/Dockerfile -t triana-preview:0.1.0-alpha.1 .
docker run --rm \
  --env-file /absolute/private/path/to/provider.env \
  -v "$PWD/traces:/input:ro" \
  -v "$PWD/output:/output" \
  triana-preview:0.1.0-alpha.1 analyze \
  --traces /input/preview-traces.jsonl \
  --agent "Order-support agent that tracks deliveries." \
  --output /output/run-001 \
  --confirm-authorized-traces
```

Omit `--env-file` for the deterministic, no-network mode. Pass only the private,
complete environment file when intentionally authorizing semantic egress. The
image runs as a non-root user, reads the input mount as `:ro`, writes only to
the output mount, and has no telemetry or hosted upload contract. No registry
publication is part of this preview.
