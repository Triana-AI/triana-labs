"""Tool entity model and identity helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agentagon.core.entities.span import SpanEntity
from agentagon.core.entities.types import EntityType
from agentagon.core.span import Span
from agentagon.core.type_utils import as_dict, optional_string
from agentagon.core.types.json import JsonObject


class ToolCapability(StrEnum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"
    UNKNOWN = "unknown"

    @classmethod
    def from_value(cls, value: Any) -> ToolCapability:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            return cls.UNKNOWN
        try:
            return cls(value.strip().lower())
        except ValueError:
            return cls.UNKNOWN


@dataclass(slots=True)
class ToolEntity(SpanEntity):
    entity_type: EntityType = EntityType.TOOL
    tool_name: str = ""
    description: str | None = None
    parameters: JsonObject = field(default_factory=dict)
    capability: ToolCapability = ToolCapability.UNKNOWN

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.tool_name

    @classmethod
    def from_span(cls, span: Span) -> ToolEntity:
        tool_name = _tool_name_from_span(span)
        entity = cls(
            entity_id="",
            name=tool_name,
            tool_name=tool_name,
            description=optional_string(span.metadata.get("description")),
            capability=_capability_from_sources(
                span.metadata,
                name=tool_name,
                description=optional_string(span.metadata.get("description")),
            ),
            observed_span_count=1,
        )
        entity.entity_id = tool_entity_id(entity)
        return entity

    @classmethod
    def from_span_metadata(cls, span: Span) -> tuple[ToolEntity, ...]:
        tools = span.metadata.get("tools")
        if not isinstance(tools, list):
            return ()

        entities: list[ToolEntity] = []
        for tool_definition in tools:
            entity = _entity_from_definition(tool_definition)
            if entity is not None:
                entities.append(entity)
        return tuple(entities)


@dataclass(slots=True)
class ToolPairEntity(SpanEntity):
    entity_type: EntityType = EntityType.TOOLS
    previous_tool_name: str = ""
    next_tool_name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"{self.previous_tool_name} -> {self.next_tool_name}"


def tool_entity_id(tool: ToolEntity) -> str:
    return f"tool:{tool.tool_name or 'unknown'}"


def tool_pair_entity_id(previous_tool_name: str, next_tool_name: str) -> str:
    return f"tools:{previous_tool_name or 'unknown'}:{next_tool_name or 'unknown'}"


def tool_pair_entity(previous_tool_name: str, next_tool_name: str) -> ToolPairEntity:
    return ToolPairEntity(
        entity_id=tool_pair_entity_id(previous_tool_name, next_tool_name),
        previous_tool_name=previous_tool_name or "unknown",
        next_tool_name=next_tool_name or "unknown",
        observed_span_count=1,
    )


def _entity_from_definition(tool_definition: Any) -> ToolEntity | None:
    definition = as_dict(tool_definition)
    function_definition = as_dict(definition.get("function"))
    source = function_definition or definition

    tool_name = optional_string(source.get("name"))
    if not tool_name:
        return None

    entity = ToolEntity(
        entity_id="",
        name=tool_name,
        tool_name=tool_name,
        description=optional_string(source.get("description")),
        parameters=as_dict(source.get("parameters")),
        capability=_capability_from_sources(
            definition,
            function_definition,
            source,
            name=tool_name,
            description=optional_string(source.get("description")),
        ),
        observed_span_count=0,
    )
    entity.entity_id = tool_entity_id(entity)
    return entity


def _tool_name_from_span(span: Span) -> str:
    return span.name or optional_string(span.metadata.get("tool")) or "unknown"


_READ_ONLY_VERBS = {
    "check",
    "fetch",
    "find",
    "get",
    "list",
    "lookup",
    "query",
    "read",
    "retrieve",
    "search",
    "select",
    "view",
}
_MUTATING_VERBS = {
    "add",
    "archive",
    "cancel",
    "commit",
    "create",
    "delete",
    "deploy",
    "edit",
    "insert",
    "merge",
    "modify",
    "patch",
    "post",
    "publish",
    "push",
    "remove",
    "save",
    "send",
    "set",
    "submit",
    "trash",
    "update",
    "upload",
    "write",
}
_CAPABILITY_HINT_KEYS = {
    "capability",
    "effect",
    "effect_type",
    "mutability",
    "side_effect",
    "side_effects",
    "tool_capability",
    "x_capability",
    "x_effect",
    "x_read_only",
    "x_mutating",
}
_READ_ONLY_HINT_KEYS = {
    "readOnlyHint",
    "read_only",
    "readonly",
    "safe",
    "x-readOnlyHint",
}
_MUTATING_HINT_KEYS = {
    "mutable",
    "mutating",
    "destructive",
    "write",
    "writes",
    "x-mutating",
}


def merge_tool_capability(
    existing: ToolCapability,
    incoming: ToolCapability,
) -> ToolCapability:
    if existing is ToolCapability.MUTATING or incoming is ToolCapability.MUTATING:
        return ToolCapability.MUTATING
    if existing is not ToolCapability.UNKNOWN:
        return existing
    return incoming


def _capability_from_sources(
    *sources: JsonObject,
    name: str,
    description: str | None,
) -> ToolCapability:
    for source in sources:
        capability = _explicit_capability_from_value(source)
        if capability is not ToolCapability.UNKNOWN:
            return capability
    return _heuristic_capability(name, description)


def _explicit_capability_from_value(value: Any) -> ToolCapability:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_text = str(key)
            if key_text in _READ_ONLY_HINT_KEYS and nested_value is True:
                return ToolCapability.READ_ONLY
            if key_text in _READ_ONLY_HINT_KEYS and nested_value is False:
                return ToolCapability.MUTATING
            if key_text in _MUTATING_HINT_KEYS and nested_value is True:
                return ToolCapability.MUTATING
            if key_text in _MUTATING_HINT_KEYS and nested_value is False:
                return ToolCapability.READ_ONLY
            if key_text in _CAPABILITY_HINT_KEYS:
                capability = ToolCapability.from_value(nested_value)
                if capability is not ToolCapability.UNKNOWN:
                    return capability
        for nested_key in ("annotations", "metadata", "extra", "schema"):
            capability = _explicit_capability_from_value(value.get(nested_key))
            if capability is not ToolCapability.UNKNOWN:
                return capability
    return ToolCapability.UNKNOWN


def _heuristic_capability(name: str, description: str | None) -> ToolCapability:
    words = _capability_words(name)
    description_words = _capability_words(description or "")
    if words & _MUTATING_VERBS:
        return ToolCapability.MUTATING
    if words & _READ_ONLY_VERBS:
        return ToolCapability.READ_ONLY
    if description_words & _MUTATING_VERBS:
        return ToolCapability.MUTATING
    if description_words & _READ_ONLY_VERBS:
        return ToolCapability.READ_ONLY
    return ToolCapability.UNKNOWN


def _capability_words(value: str) -> set[str]:
    normalized = value.replace("-", "_").replace(".", "_").replace("/", "_")
    return {part.strip().lower() for part in normalized.split("_") if part.strip()}


__all__ = [
    "ToolCapability",
    "ToolEntity",
    "ToolPairEntity",
    "merge_tool_capability",
    "tool_entity_id",
    "tool_pair_entity",
    "tool_pair_entity_id",
]
