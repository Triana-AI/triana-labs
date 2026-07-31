# HRAI v2 synthetic reference adapter

This standalone reference transform demonstrates the external `PreviewTrace`
file boundary. It is deliberately small and dependency-free so a coding agent
can copy `adapter.py` into a customer repository and adapt the mapping there.
It is not a supported HRAI product integration, adapter SDK, or generic import
framework.

From the Triana repository checkout, run:

```sh
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache \
  uv run --project triana-labs --locked python \
  triana-labs/examples/hrai_v2/adapter.py synthetic-hrai-v2.jsonl \
  --out adapter-output --data-class SYNTHETIC

UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache \
  uv run --project triana-labs --locked triana traces observe \
  adapter-output/preview_traces.jsonl --out observer-output
```

`--data-class SYNTHETIC` is a required human attestation; it does not inspect,
classify, or redact the input. Real data is unsupported. Do not use
production-derived, customer, Blitz, local-sensitive, or otherwise private
exports with this LABS-02 example.

The adapter maps the entire input before creating a new directory containing
`preview_traces.jsonl` and `rejected_source_traces.jsonl`. It refuses to
overwrite an existing directory and removes only that new directory if a write
fails. Consume the two files only after exit 0 or 10; this small reference does
not promise atomic multi-file publication. Partial mappings remain explicit
and exit nonzero, without echoing rejected content.
