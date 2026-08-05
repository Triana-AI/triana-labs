# agentagon/core/entities/

Entity layer for identifying the subjects of signals and findings: spans,
tools, LLMs, agents, tasks, and catalogs.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public exports for entity construction and registry helpers. |
| `agent.py` | Agent entity model and extraction helpers. |
| `catalog.py` | Catalog-level grouping for known entities. |
| `classification.py` | Resolves which entity a span should belong to. |
| `llm.py` | LLM entity model and metadata helpers. |
| `registry.py` | Builds and queries an entity registry from traces. |
| `span.py` | Span entity wrappers for span-level signal subjects. |
| `task.py` | Task entity model and task identification helpers. |
| `tool.py` | Tool entity model and tool naming helpers. |
| `types.py` | Shared `EntityType` enum. |
