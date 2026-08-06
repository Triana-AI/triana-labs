import type { ReactNode } from "react";

export type ConversationEvent =
  | { kind: "message"; sequence: number; role: "system" | "user" | "assistant"; content: string }
  | { kind: "tool_call"; sequence: number; callId?: string; toolName: string; arguments: unknown }
  | { kind: "tool_result"; sequence: number; callId?: string; status?: string; result: unknown }
  | { kind: "terminal"; sequence: number; status: string; detail?: string }
  | { kind: "gap"; sequence?: number; code: string; detail: string };

export interface ConversationViewModel {
  conversation_id?: string;
  conversationId?: string;
  status: string;
  events: ConversationEvent[];
  metadata?: Record<string, unknown>;
  source?: { import_id?: string; importId?: string; record_id?: string; recordId?: string; line_number?: number };
}

function JsonValue({ value, label }: { value: unknown; label: string }) {
  const json = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  if (!json) return <span className="conversation-empty">No {label}</span>;
  const content = <pre>{json}</pre>;
  return json.length > 420 ? <details><summary>Show {label}</summary>{content}</details> : content;
}

function Event({ event }: { event: ConversationEvent }) {
  const sequence = event.sequence === undefined ? "—" : event.sequence.toString().padStart(2, "0");
  if (event.kind === "message") return (
    <article className="conversation-event message-event" data-role={event.role}>
      <header><strong>{event.role}</strong><code>{sequence}</code></header>
      <p>{event.content}</p>
    </article>
  );
  if (event.kind === "tool_call") return (
    <article className="conversation-event tool-call-event">
      <header><strong>Tool call · {event.toolName}</strong><code>{sequence}</code></header>
      {event.callId ? <small>Call ID · {event.callId}</small> : null}
      <JsonValue value={event.arguments} label="arguments" />
    </article>
  );
  if (event.kind === "tool_result") return (
    <article className="conversation-event tool-result-event">
      <header><strong>Tool result</strong><code>{sequence}</code></header>
      <small>{event.callId ? `Call ID · ${event.callId}` : "Unlinked result"}{event.status ? ` · ${event.status}` : ""}</small>
      <JsonValue value={event.result} label="result" />
    </article>
  );
  if (event.kind === "terminal") return (
    <article className="conversation-event terminal-event">
      <header><strong>Terminal · {event.status}</strong><code>{sequence}</code></header>
      {event.detail ? <p>{event.detail}</p> : null}
    </article>
  );
  return (
    <article className="conversation-event gap-event" role="note">
      <header><strong>Evidence gap</strong><code>{event.code}</code></header>
      <p>{event.detail}</p>
    </article>
  );
}

export function ConversationViewer({ conversation, context }: { conversation: ConversationViewModel; context?: ReactNode }) {
  const id = conversation.conversation_id ?? conversation.conversationId ?? "Unknown conversation";
  const ordered = [...conversation.events].sort((left, right) => (left.sequence ?? Number.MAX_SAFE_INTEGER) - (right.sequence ?? Number.MAX_SAFE_INTEGER));
  return (
    <div className={`conversation-viewer${context ? " has-context" : ""}`}>
      <section className="conversation-timeline" aria-label="Conversation timeline">
        <header className="conversation-viewer-header">
          <div><span className="mono-label">Conversation</span><h2>{id}</h2></div>
          <span className="labs-status" data-tone={conversation.status.includes("FAIL") ? "negative" : "neutral"}>{conversation.status}</span>
        </header>
        {ordered.length ? ordered.map((event, index) => <Event event={event} key={`${event.kind}-${event.sequence ?? "gap"}-${index}`} />) : (
          <article className="conversation-event gap-event"><strong>Evidence gap</strong><p>No conversation events were recorded.</p></article>
        )}
      </section>
      {context ? <aside className="conversation-context">{context}</aside> : null}
    </div>
  );
}
