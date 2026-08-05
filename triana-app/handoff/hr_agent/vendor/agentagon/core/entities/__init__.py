"""Core entity models used to resolve spans across traces."""

from agentagon.core.entities.agent import AgentEntity
from agentagon.core.entities.llm import LLMEntity
from agentagon.core.entities.registry import (
    EntityRegistry,
    build_entity_registry,
)
from agentagon.core.entities.span import SpanEntity
from agentagon.core.entities.task import TaskEntity
from agentagon.core.entities.tool import (
    ToolCapability,
    ToolEntity,
    ToolPairEntity,
    tool_pair_entity,
    tool_entity_id,
    tool_pair_entity_id,
)
from agentagon.core.entities.types import EntityType


__all__ = [
    "AgentEntity",
    "EntityRegistry",
    "EntityType",
    "LLMEntity",
    "SpanEntity",
    "ToolCapability",
    "TaskEntity",
    "ToolEntity",
    "ToolPairEntity",
    "build_entity_registry",
    "tool_entity_id",
    "tool_pair_entity",
    "tool_pair_entity_id",
]
