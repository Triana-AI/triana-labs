"""Catalog of entity implementations."""

from __future__ import annotations

from agentagon.core.entities.agent import AgentEntity
from agentagon.core.entities.llm import LLMEntity
from agentagon.core.entities.span import SpanEntity
from agentagon.core.entities.task import TaskEntity
from agentagon.core.entities.tool import ToolEntity
from agentagon.core.span import SpanType


ENTITY_CLASS_BY_SPAN_TYPE: dict[SpanType, type[SpanEntity]] = {
    SpanType.TOOL: ToolEntity,
    SpanType.LLM: LLMEntity,
    SpanType.AGENT: AgentEntity,
    SpanType.TASK: TaskEntity,
}

ENTITY_CLASSES: tuple[type[SpanEntity], ...] = (
    *ENTITY_CLASS_BY_SPAN_TYPE.values(),
    SpanEntity,
)


__all__ = [
    "ENTITY_CLASS_BY_SPAN_TYPE",
    "ENTITY_CLASSES",
]
