import type {
  AgentSummary,
  ConversationSummary,
  ImportSummary,
  Owner,
  RejectionSummary,
} from "@/lib/self-serve/types";
import type { ConversationEvent, ConversationViewModel } from "@/components/conversation/ConversationViewer";

const TOKEN_KEY = "triana_owner_bearer_token";

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export function getSessionToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function setSessionToken(token: string): void {
  window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearSessionToken(): void {
  window.sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getSessionToken();
  if (!token) throw new ApiError(401, "Sign in is required.");
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json() as { detail?: string; message?: string };
      message = body.detail ?? body.message ?? message;
    } catch {
      // Server errors are intentionally reduced to a safe status-only message.
    }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

function listFrom<T>(value: T[] | Record<string, unknown>, key: string): T[] {
  if (Array.isArray(value)) return value;
  const candidate = value[key] ?? value.items;
  return Array.isArray(candidate) ? candidate as T[] : [];
}

function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function normalizedEvent(value: unknown, index: number): ConversationEvent {
  const event = record(value);
  const sequence = typeof event.sequence === "number" ? event.sequence : index;
  const kind = event.kind ?? event.event_kind;
  if (kind === "message") return event as unknown as ConversationEvent;
  if (kind === "USER_MESSAGE" || kind === "ASSISTANT_MESSAGE" || kind === "SYSTEM_VISIBLE_MESSAGE") {
    return {
      kind: "message",
      sequence,
      role: kind === "USER_MESSAGE" ? "user" : kind === "ASSISTANT_MESSAGE" ? "assistant" : "system",
      content: typeof event.content === "string" ? event.content : "",
    };
  }
  if (kind === "TOOL_CALL") return { kind: "tool_call", sequence, callId: String(event.call_id ?? ""), toolName: String(event.tool_name ?? "Unknown tool"), arguments: event.arguments };
  if (kind === "TOOL_RESULT") return { kind: "tool_result", sequence, callId: String(event.call_id ?? ""), status: String(event.result_state ?? "UNKNOWN"), result: event.result ?? event.error_code ?? null };
  if (kind === "TERMINAL") return { kind: "terminal", sequence, status: String(event.terminal_state ?? "UNKNOWN"), detail: typeof event.reason_code === "string" ? event.reason_code : undefined };
  if (kind === "tool_call" || kind === "tool_result" || kind === "terminal" || kind === "gap") return event as unknown as ConversationEvent;
  return { kind: "gap", sequence, code: "UNKNOWN_EVENT", detail: "The server returned an event kind this viewer does not understand." };
}

function normalizedConversation(value: unknown): ConversationViewModel {
  const item = record(value);
  const trace = record(item.trace);
  const rawEvents = Array.isArray(item.events) ? item.events : Array.isArray(trace.events) ? trace.events : [];
  return {
    conversation_id: String(item.conversation_id ?? trace.trace_id ?? "Unknown conversation"),
    status: String(item.status ?? "ACCEPTED"),
    events: rawEvents.map(normalizedEvent),
    metadata: record(item.metadata),
    source: record(item.source) as ConversationViewModel["source"],
  };
}

export const selfServeApi = {
  me: () => request<Owner>("/api/v1/me"),
  async listAgents(): Promise<AgentSummary[]> {
    return listFrom(await request<AgentSummary[] | Record<string, unknown>>("/api/v1/agents"), "agents");
  },
  createAgent: (displayName: string) => request<AgentSummary>("/api/v1/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: displayName }),
  }),
  getAgent: (agentId: string) => request<AgentSummary>(`/api/v1/agents/${encodeURIComponent(agentId)}`),
  async listImports(agentId: string): Promise<ImportSummary[]> {
    return listFrom(await request<ImportSummary[] | Record<string, unknown>>(
      `/api/v1/agents/${encodeURIComponent(agentId)}/imports`,
    ), "imports");
  },
  uploadImport: (agentId: string, file: File) => {
    const body = new FormData();
    body.append("file", file);
    body.append("owner_attested", "true");
    return request<ImportSummary>(`/api/v1/agents/${encodeURIComponent(agentId)}/imports`, {
      method: "POST",
      headers: { "Idempotency-Key": window.crypto.randomUUID() },
      body,
    });
  },
  getImport: (importId: string) => request<ImportSummary>(`/api/v1/imports/${encodeURIComponent(importId)}`),
  async listConversations(importId: string): Promise<ConversationSummary[]> {
    return listFrom(await request<ConversationSummary[] | Record<string, unknown>>(
      `/api/v1/imports/${encodeURIComponent(importId)}/conversations`,
    ), "conversations");
  },
  async listRejections(importId: string): Promise<RejectionSummary[]> {
    const rows = listFrom<Record<string, unknown>>(await request<Record<string, unknown>>(
      `/api/v1/imports/${encodeURIComponent(importId)}/rejections`,
    ), "rejections");
    return rows.map((row) => ({
      line_number: Number(row.line_number),
      reason_code: String(row.reason_code ?? row.code ?? "UNKNOWN_REJECTION"),
      message: typeof row.message === "string" ? row.message : typeof row.safe_message === "string" ? row.safe_message : undefined,
    }));
  },
  async getConversation(conversationId: string): Promise<ConversationViewModel> {
    return normalizedConversation(await request<unknown>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`));
  },
};
