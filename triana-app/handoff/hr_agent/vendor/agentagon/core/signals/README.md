# agentagon/core/signals/

Core signal observation and query primitives. These are shared support types,
while executable signal callbacks live under `agentagon/signals/`.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Re-exports core signal helper types. |
| `observations.py` | Observation containers for signal values and provenance. |
| `queries.py` | Query helpers for reading signals from spans, traces, and summaries. |
| `summaries.py` | Builds per-entity signal summaries and summary-level stats lookups. |
| `types.py` | Core signal type definitions. |
