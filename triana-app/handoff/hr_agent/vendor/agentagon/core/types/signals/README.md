# agentagon/core/types/signals/

Typed signal result model. Signal callbacks use these dataclasses to attach
values, summaries, observations, and provenance to traces and entities.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public exports for signal value and callback types. |
| `analysis.py` | Analysis container attached to traces and spans. |
| `base.py` | Base signal, summary, callback, context, and run-result types. |
| `bool.py` | Boolean signal value implementation and aggregations. |
| `category.py` | Categorical signal value implementation and aggregations. |
| `context.py` | Context objects passed into span, parent, trace, and cohort callbacks. |
| `decimal.py` | Decimal/numeric signal value implementation and aggregations. |
| `string.py` | String signal value implementation and aggregations. |
