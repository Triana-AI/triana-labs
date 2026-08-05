"""Agent entity model."""

from __future__ import annotations

from dataclasses import dataclass

from agentagon.core.entities.span import SpanEntity
from agentagon.core.entities.types import EntityType
from agentagon.core.span import Span


@dataclass(slots=True)
class AgentEntity(SpanEntity):
    entity_type: EntityType = EntityType.AGENT

    @classmethod
    def from_span(cls, span: Span) -> AgentEntity:
        return cls(
            entity_id=_entity_id_from_span(span),
            name=span.name,
            observed_span_count=1,
        )


def _entity_id_from_span(span: Span) -> str:
    return f"agent:{span.name or 'unknown'}"


__all__ = ["AgentEntity"]
