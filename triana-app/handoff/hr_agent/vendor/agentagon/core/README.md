# agentagon/core/

Shared domain primitives for trace analysis. Higher-level ingestion,
signals, findings, dashboards, and reports depend on these types.

## Files

| File | Purpose |
|------|---------|
| `span.py` | Span model, span type enum, timestamps, IO fields, parent links, metadata, and attached analysis state. |
| `span_sequence.py` | Utilities for ordered span traversal and neighboring span relationships. |
| `stats.py` | Numeric summary helpers used by signal and dashboard aggregation. |
| `trace.py` | Trace model, provider enum, user metadata, timestamps, and span collection. |
| `type_utils.py` | Helpers for extracting text and common values from heterogeneous trace payloads. |

## Folders

| Folder | Purpose |
|--------|---------|
| [`cohort/`](cohort/) | Cohort-level typing for groups of traces. |
| [`entities/`](entities/) | Entity models and registry logic for agents, tasks, spans, tools, LLMs, and catalogs. |
| [`llms/`](llms/) | LLM model catalog, normalization, and pricing/context metadata. |
| [`signals/`](signals/) | Core signal observation/query types used by older and shared analysis paths. |
| [`types/`](types/) | JSON and signal-value dataclasses used throughout analysis results. |
