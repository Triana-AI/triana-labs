"""Entity registry."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentagon.core.entities.catalog import ENTITY_CLASSES
from agentagon.core.entities.classification import resolve_entity_for_span
from agentagon.core.entities.llm import LLMEntity
from agentagon.core.entities.span import SpanEntity
from agentagon.core.entities.tool import (
    ToolEntity,
    merge_tool_capability,
    tool_pair_entity,
)
from agentagon.core.session import Session
from agentagon.core.span import Span
from agentagon.core.span_sequence import serial_adjacent_tool_pairs
from agentagon.core.trace import Trace


@dataclass(slots=True)
class EntityRegistry:
    entities: dict[str, SpanEntity] = field(default_factory=dict)

    def get(self, entity_id: str) -> SpanEntity | None:
        return self.entities.get(entity_id)

    def entity_for_span(self, span: Span) -> SpanEntity | None:
        return self.get(resolve_entity_for_span(span).entity_id)

    def tool_entity_for_span(self, span: Span) -> ToolEntity | None:
        entity = self.entity_for_span(span)
        return entity if isinstance(entity, ToolEntity) else None

    def register_entity(self, entity: SpanEntity) -> SpanEntity:
        existing = self.get(entity.entity_id)
        if existing is None:
            self.entities[entity.entity_id] = entity
            return entity
        _merge_entity_observation(existing, entity)
        return existing


def build_entity_registry(sessions: list[Session] | tuple[Session, ...]) -> EntityRegistry:
    registry = EntityRegistry()
    for session in sessions:
        for entity in _entities_from_session(session):
            registry.register_entity(entity)
    return registry


def _merge_entity_observation(existing: SpanEntity, incoming: SpanEntity) -> None:
    if isinstance(existing, LLMEntity) and isinstance(incoming, LLMEntity):
        if existing.model is None:
            existing.model = incoming.model
        if existing.model_info is None:
            existing.model_info = incoming.model_info
    if isinstance(existing, ToolEntity) and isinstance(incoming, ToolEntity):
        if existing.description is None:
            existing.description = incoming.description
        if not existing.parameters:
            existing.parameters = incoming.parameters
        existing.capability = merge_tool_capability(
            existing.capability,
            incoming.capability,
        )
    existing.observed_span_count += incoming.observed_span_count


def _entities_from_session(session: Session) -> tuple[SpanEntity, ...]:
    entities: list[SpanEntity] = []
    for span in session.spans:
        entities.append(resolve_entity_for_span(span))
        entities.extend(_entities_from_span_metadata(span))
    for trace in session.traces:
        entities.extend(_serial_adjacent_tool_pair_entities_from_trace(trace))
    return tuple(entities)


def _entities_from_span_metadata(span: Span) -> tuple[SpanEntity, ...]:
    entities: list[SpanEntity] = []
    for entity_class in ENTITY_CLASSES:
        entities.extend(entity_class.from_span_metadata(span))
    return tuple(entities)


def _serial_adjacent_tool_pair_entities_from_trace(
    trace: Trace,
) -> tuple[SpanEntity, ...]:
    entities: list[SpanEntity] = []
    for child_spans in _children_by_parent(trace).values():
        for previous_tool, next_tool in serial_adjacent_tool_pairs(child_spans):
            entities.append(tool_pair_entity(previous_tool.name, next_tool.name))
    return tuple(entities)


def _children_by_parent(trace: Trace) -> dict[str, list[Span]]:
    children_by_parent: dict[str, list[Span]] = {
        span.span_id: [] for span in trace.spans
    }
    for span in trace.spans:
        for parent_id in span.parent_span_ids:
            if parent_id in children_by_parent:
                children_by_parent[parent_id].append(span)
    return children_by_parent


__all__ = [
    "EntityRegistry",
    "build_entity_registry",
]
