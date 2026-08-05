"""LLM entity model."""

from __future__ import annotations

from dataclasses import dataclass

from agentagon.core.entities.span import SpanEntity
from agentagon.core.entities.types import EntityType
from agentagon.core.llms import (
    LLMModelInfo,
    lookup_llm_model_info,
)
from agentagon.core.span import Span
from agentagon.core.type_utils import optional_string


@dataclass(slots=True)
class LLMEntity(SpanEntity):
    entity_type: EntityType = EntityType.LLM
    model: str | None = None
    model_info: LLMModelInfo | None = None

    @classmethod
    def from_span(cls, span: Span) -> LLMEntity:
        raw_model = _raw_model_from_span(span)
        model_info = lookup_llm_model_info(raw_model)
        model = model_info.model if model_info is not None else raw_model
        return cls(
            entity_id=_entity_id_from_span(span),
            name=span.name,
            model=model,
            model_info=model_info,
            observed_span_count=1,
        )


def _entity_id_from_span(span: Span) -> str:
    raw_model = _raw_model_from_span(span)
    model_info = lookup_llm_model_info(raw_model)
    model = model_info.model if model_info is not None else raw_model
    name = model or span.name or "unknown"
    return f"llm:{name}"


def _raw_model_from_span(span: Span) -> str | None:
    model = optional_string(span.metadata.get("model"))
    return model.strip() if model is not None else None


__all__ = ["LLMEntity"]
