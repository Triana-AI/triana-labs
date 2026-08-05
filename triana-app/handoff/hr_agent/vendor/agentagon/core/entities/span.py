"""Generic span entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentagon.core.entities.types import EntityType
from agentagon.core.span import Span
from agentagon.core.types.json import JsonObject


@dataclass(slots=True)
class SpanEntity:
    entity_id: str = ""
    entity_type: EntityType = EntityType.SPAN
    name: str = ""
    metadata: JsonObject = field(default_factory=dict)
    observed_span_count: int = 0

    @classmethod
    def from_span(cls, span: Span) -> SpanEntity:
        return cls(
            entity_id=_entity_id_from_span(span),
            name=span.name,
            metadata={"span_type": span.span_type.value},
            observed_span_count=1,
        )

    @classmethod
    def from_span_metadata(cls, span: Span) -> tuple[SpanEntity, ...]:
        return ()


def _entity_id_from_span(span: Span) -> str:
    return f"span:{span.span_type.value}:{span.name or 'unknown'}"


__all__ = ["SpanEntity"]
