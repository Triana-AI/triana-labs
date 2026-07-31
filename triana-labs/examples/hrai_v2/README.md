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

The adapter creates a new directory with `preview_traces.jsonl`, safe per-line
rejections, and a manifest. It refuses to overwrite an existing directory.
Partial mappings remain explicit and exit nonzero; rejected content is not
echoed into the safe artifacts or terminal event.
