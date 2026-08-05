"""Shared entity enums."""

from enum import StrEnum


class EntityType(StrEnum):
    SPAN = "span"
    TOOL = "tool"
    TOOLS = "tools"
    LLM = "llm"
    AGENT = "agent"
    TASK = "task"


__all__ = ["EntityType"]
