"""Classify spans and dispatch entity construction."""

from __future__ import annotations

import re

from agentagon.core.entities.agent import AgentEntity
from agentagon.core.entities.catalog import ENTITY_CLASS_BY_SPAN_TYPE
from agentagon.core.entities.span import SpanEntity
from agentagon.core.span import Span, SpanType


_AGENT_NAME_COMPONENT = re.compile(r"(?:Agent|agent)(?=$|[^A-Za-z0-9])")


def resolve_entity_for_span(span: Span) -> SpanEntity:
    if _is_agent_named_task(span):
        return AgentEntity.from_span(span)
    entity_class = ENTITY_CLASS_BY_SPAN_TYPE.get(span.span_type, SpanEntity)
    return entity_class.from_span(span)


def _is_agent_named_task(span: Span) -> bool:
    return span.span_type is SpanType.TASK and bool(
        _AGENT_NAME_COMPONENT.search(span.name or "")
    )


__all__ = [
    "resolve_entity_for_span",
]
