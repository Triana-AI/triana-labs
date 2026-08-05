# agentagon/core/llms/

LLM model metadata used by token, cost, context-window, and provider-normalized
signals.

## Files

| File | Purpose |
|------|---------|
| `MODELS.md` | Human-readable model catalog notes. |
| `__init__.py` | Public exports for model catalog and normalization helpers. |
| `catalog.py` | Registry of model context windows, token pricing, and long-context pricing. |
| `normalization.py` | Normalizes provider/model names into catalog keys. |
| `types.py` | Dataclasses for model pricing and context metadata. |
