# PreviewTrace v1 adapter contract

Emit UTF-8 JSON Lines with one complete trace object per LF-delimited physical
line. CRLF is accepted and counted at its original byte size; CR alone is not a
record separator. A file is limited to 16 MiB and 1,000 physical lines. Each
physical line, including its original line ending, is limited to 1 MiB. Do not
emit a UTF-8 BOM, blank line, duplicate JSON key, non-finite number, or JSON
nesting deeper than 32 containers.

## Closed trace envelope

Every trace has exactly these fields:

- `contract_kind`: exactly `preview_trace`
- `schema_version`: integer `1` (a boolean is not an integer here)
- `privacy_class`: exactly one of `SYNTHETIC`,
  `OWNER_AUTHORIZED_REAL_DATA_CANARY`, or
  `CUSTOMER_AUTHORIZED_TRACE_DATA`; every trace in one file must use the same
  class
- `trace_id`: unique in the file and matched by
  `^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$`
- `source_trace_id`: unique in the file, control-free, and at most
  512 UTF-8 bytes
- `events`: between 1 and 1,000 events in observed order

The trace object and every event variant are closed schemas. Do not add
convenience fields such as `role`, inferred metadata, or source-only values.
Every event has a non-boolean safe integer `sequence` equal to its zero-based
array index. Safe integers range from -9,007,199,254,740,991 to
9,007,199,254,740,991, while an event sequence is additionally non-negative.

## Exact event variants

| Variant | Exact fields |
| --- | --- |
| `SYSTEM_VISIBLE_MESSAGE` | `sequence`, `event_kind`, `content` |
| `USER_MESSAGE` | `sequence`, `event_kind`, `content` |
| `ASSISTANT_MESSAGE` | `sequence`, `event_kind`, `content`, `is_final` |
| `TOOL_CALL` | `sequence`, `event_kind`, `call_id`, `tool_name`, `arguments` |
| `TOOL_RESULT SUCCEEDED` | `sequence`, `event_kind`, `call_id`, `result_state`, `result` |
| `TOOL_RESULT ERROR` | `sequence`, `event_kind`, `call_id`, `result_state`, `error_code` |
| `TERMINAL SUCCESS` | `sequence`, `event_kind`, `terminal_state` |
| `TERMINAL ERROR/ABORTED` | `sequence`, `event_kind`, `terminal_state`, `reason_code` |

`USER_MESSAGE` and `SYSTEM_VISIBLE_MESSAGE` content is 1 to 65,536 UTF-8
bytes. `ASSISTANT_MESSAGE` content is 0 to 65,536 UTF-8 bytes and `is_final`
is a boolean. Text may contain LF but no other C0 or C1 controls.

`call_id` and `tool_name` use the same SafeId regex as `trace_id`. Calls are
unique. A result must follow its matching call, and there is at most one result
per call. `SUCCEEDED` requires portable JSON `result` and forbids
`error_code`; `ERROR` requires `error_code` and forbids `result`.
`error_code` and `reason_code` match `^[A-Z][A-Z0-9_]{0,63}$`.

Portable JSON in `arguments` and `result` permits null, booleans, safe
integers, arrays, objects, and strings of at most 65,536 UTF-8 bytes. It rejects
fractional/exponent numbers, out-of-range integers, excessive depth, and
forbidden controls.

A terminal may appear at most once and must be last. `SUCCESS` has no
`reason_code`; `ERROR` and `ABORTED` require one. At most one assistant message
may set `is_final: true`. User and terminal events are optional; mechanical
validation does not invent either one.

## Mapping rule

Map only source facts. If a source field is absent or ambiguous, stop and ask
the operator rather than inventing it. Preserve each conversation as one trace
and preserve event order. Never place credentials or raw source values in logs,
adapter contracts, or error messages. After adapting, run `validate` and then
`preview` before constructing the digest-pinned Docker command.
