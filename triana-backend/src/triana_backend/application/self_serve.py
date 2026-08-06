"""Deterministic self-serve trace ingestion with infrastructure behind ports."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

from triana_labs.contracts.traces import LineRejection, parse_and_validate_line

MAX_UPLOAD_BYTES = 16 * 1024 * 1024
MAX_LINE_BYTES = 1024 * 1024
MAX_PHYSICAL_RECORDS = 1_000
CUSTOMER_PRIVACY_CLASS = "CUSTOMER_AUTHORIZED_TRACE_DATA"


@dataclass(slots=True)
class SelfServeRefusal(Exception):
    status_code: int
    code: str
    safe_message: str


@dataclass(frozen=True, slots=True)
class ParsedConversation:
    line_number: int
    trace_id: str
    source_trace_id: str
    events: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class SafeRejection:
    line_number: int
    code: str
    json_pointer: str
    safe_message: str


class PrivateTraceStore(Protocol):
    def publish_owner_trace(
        self, *, workspace_id: str, payload: bytes, content_type: str
    ) -> Mapping[str, Any]: ...


class SelfServeRepository(Protocol):
    def get_or_create_me(self, owner_subject: str) -> Mapping[str, Any]: ...
    def create_agent(
        self, owner_subject: str, display_name: str
    ) -> Mapping[str, Any]: ...
    def list_agents(self, owner_subject: str) -> Sequence[Mapping[str, Any]]: ...
    def get_agent(self, owner_subject: str, agent_id: str) -> Mapping[str, Any]: ...
    def persist_import(
        self,
        owner_subject: str,
        agent_id: str,
        *,
        filename: str,
        source: Mapping[str, Any],
        source_sha256: str,
        idempotency_key: str,
        conversations: Sequence[ParsedConversation],
        rejections: Sequence[SafeRejection],
    ) -> Mapping[str, Any]: ...
    def list_agent_imports(
        self, owner_subject: str, agent_id: str
    ) -> Sequence[Mapping[str, Any]]: ...
    def get_import(self, owner_subject: str, import_id: str) -> Mapping[str, Any]: ...
    def list_import_conversations(
        self, owner_subject: str, import_id: str
    ) -> Sequence[Mapping[str, Any]]: ...
    def list_import_rejections(
        self, owner_subject: str, import_id: str
    ) -> Sequence[Mapping[str, Any]]: ...
    def get_conversation(
        self, owner_subject: str, conversation_id: str
    ) -> Mapping[str, Any]: ...


class SelfServeService:
    """Validate first, publish privately, then atomically persist safe projections."""

    def __init__(
        self, *, repository: SelfServeRepository, storage: PrivateTraceStore
    ) -> None:
        self._repository = repository
        self._storage = storage

    def get_or_create_me(self, owner_subject: str) -> Mapping[str, Any]:
        return self._repository.get_or_create_me(owner_subject)

    def create_agent(self, owner_subject: str, display_name: str) -> Mapping[str, Any]:
        return self._repository.create_agent(owner_subject, display_name)

    def list_agents(self, owner_subject: str) -> Sequence[Mapping[str, Any]]:
        return self._repository.list_agents(owner_subject)

    def get_agent(self, owner_subject: str, agent_id: str) -> Mapping[str, Any]:
        return self._repository.get_agent(owner_subject, agent_id)

    def create_import(
        self,
        owner_subject: str,
        agent_id: str,
        *,
        filename: str,
        content_type: str,
        payload: bytes,
        owner_attested: bool,
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        if not owner_attested:
            raise SelfServeRefusal(
                422,
                "OWNER_ATTESTATION_REQUIRED",
                "Upload authorization must be attested.",
            )
        if not filename.lower().endswith(".jsonl"):
            raise SelfServeRefusal(
                415, "UNSUPPORTED_FILE_TYPE", "Upload must be a .jsonl file."
            )
        if content_type not in {
            "application/x-ndjson",
            "application/jsonl",
            "application/json",
            "text/plain",
        }:
            raise SelfServeRefusal(
                415, "UNSUPPORTED_MEDIA_TYPE", "Upload media type is not supported."
            )
        if not payload:
            raise SelfServeRefusal(
                422, "EMPTY_UPLOAD", "Upload contains no physical records."
            )
        if len(payload) > MAX_UPLOAD_BYTES:
            raise SelfServeRefusal(
                413, "UPLOAD_TOO_LARGE", "Upload exceeds the size limit."
            )
        if not idempotency_key.strip() or len(idempotency_key) > 255:
            raise SelfServeRefusal(
                422,
                "INVALID_IDEMPOTENCY_KEY",
                "Idempotency-Key is required and must be at most 255 characters.",
            )

        # Ownership is checked before parsing or publishing, preventing an attacker
        # from using another owner's identifier as a storage side channel.
        agent = self._repository.get_agent(owner_subject, agent_id)
        workspace_id = str(agent["workspace_id"])
        conversations, rejections, physical_count = _parse_jsonl(payload)
        source_sha256 = hashlib.sha256(payload).hexdigest()
        source = self._storage.publish_owner_trace(
            workspace_id=workspace_id,
            payload=payload,
            content_type="application/x-ndjson",
        )
        result = dict(
            self._repository.persist_import(
                owner_subject,
                agent_id,
                filename=filename,
                source=source,
                source_sha256=source_sha256,
                idempotency_key=idempotency_key,
                conversations=conversations,
                rejections=rejections,
            )
        )
        if result.get("physical_record_count") != physical_count:
            raise RuntimeError(
                "persisted import accounting does not match parsed input"
            )
        return result

    def list_agent_imports(
        self, owner_subject: str, agent_id: str
    ) -> Sequence[Mapping[str, Any]]:
        return self._repository.list_agent_imports(owner_subject, agent_id)

    def get_import(self, owner_subject: str, import_id: str) -> Mapping[str, Any]:
        return self._repository.get_import(owner_subject, import_id)

    def list_import_conversations(
        self, owner_subject: str, import_id: str
    ) -> Sequence[Mapping[str, Any]]:
        return self._repository.list_import_conversations(owner_subject, import_id)

    def list_import_rejections(
        self, owner_subject: str, import_id: str
    ) -> Sequence[Mapping[str, Any]]:
        return self._repository.list_import_rejections(owner_subject, import_id)

    def get_conversation(
        self, owner_subject: str, conversation_id: str
    ) -> Mapping[str, Any]:
        return self._repository.get_conversation(owner_subject, conversation_id)


def _parse_jsonl(
    payload: bytes,
) -> tuple[list[ParsedConversation], list[SafeRejection], int]:
    accepted: list[ParsedConversation] = []
    rejected: list[SafeRejection] = []
    trace_ids: set[str] = set()
    source_ids: set[str] = set()
    lines = payload.splitlines()
    if len(lines) > MAX_PHYSICAL_RECORDS:
        raise SelfServeRefusal(
            413, "TOO_MANY_RECORDS", "Upload exceeds the physical record limit."
        )
    for line_number, line in enumerate(lines, start=1):
        try:
            if len(line) > MAX_LINE_BYTES:
                raise LineRejection("LINE_TOO_LARGE")
            validated = parse_and_validate_line(line, first_line=line_number == 1)
            value = validated.value
            trace_id = cast(str, value["trace_id"])
            source_id = cast(str, value["source_trace_id"])
            if trace_id in trace_ids:
                raise LineRejection("DUPLICATE_TRACE_ID", "/trace_id")
            if source_id in source_ids:
                raise LineRejection("DUPLICATE_SOURCE_TRACE_ID", "/source_trace_id")
            trace_ids.add(trace_id)
            source_ids.add(source_id)
            accepted.append(
                ParsedConversation(
                    line_number=line_number,
                    trace_id=trace_id,
                    source_trace_id=source_id,
                    events=cast(list[dict[str, Any]], value["events"]),
                )
            )
        except LineRejection as error:
            record = error.as_record(line_number)
            rejected.append(
                SafeRejection(
                    line_number=cast(int, record["line_number"]),
                    code=cast(str, record["code"]),
                    json_pointer=cast(str, record["json_pointer"]),
                    safe_message=cast(str, record["safe_message"]),
                )
            )
    return accepted, rejected, len(lines)
