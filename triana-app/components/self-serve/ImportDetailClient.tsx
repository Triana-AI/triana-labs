"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { selfServeApi } from "@/lib/self-serve/api";
import type { ConversationSummary, ImportSummary, RejectionSummary } from "@/lib/self-serve/types";
import { Breadcrumbs, ErrorNotice, LoadingNotice, SelfServePage } from "@/components/self-serve/SelfServePage";

export function ImportDetailClient({ agentId, importId }: { agentId: string; importId: string }) {
  const [item, setItem] = useState<ImportSummary | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[] | null>(null);
  const [rejections, setRejections] = useState<RejectionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([selfServeApi.getImport(importId), selfServeApi.listConversations(importId), selfServeApi.listRejections(importId)])
      .then(([nextItem, nextConversations, nextRejections]) => { setItem(nextItem); setConversations(nextConversations); setRejections(nextRejections); })
      .catch((value: Error) => setError(value.message));
  }, [importId]);

  return <SelfServePage eyebrow="Import" title="Import accounting" description="Every physical line is either accepted or rejected—never silently dropped.">
    <Breadcrumbs items={[{ label: "Agents", href: "/agents" }, { label: agentId, href: `/agents/${agentId}` }, { label: importId }]} />
    {error ? <ErrorNotice message={error} /> : item === null ? <LoadingNotice label="Loading import accounting…" /> : <>
      <section className="accounting-row" aria-label="Import accounting">
        <div><span>Status</span><strong data-status={item.status}>{item.status}</strong></div>
        <div><span>Physical lines</span><strong>{item.physical_record_count}</strong></div>
        <div><span>Accepted</span><strong>{item.accepted_conversation_count ?? item.accepted_record_count ?? 0}</strong></div>
        <div><span>Rejected</span><strong>{item.rejected_record_count}</strong></div>
      </section>
      {item.status === "FAILED" ? <div className="self-serve-notice is-error" role="alert"><strong>Import failed</strong><p>No conversation was accepted. Correct the file and upload a new immutable import.</p></div> : null}
      <section className="self-serve-grid">
        <div className="self-serve-card">
          <div className="card-heading"><h2>Accepted conversations</h2><span>{conversations?.length ?? "—"}</span></div>
          {conversations === null ? <LoadingNotice /> : conversations.length === 0 ? <div className="self-serve-empty"><strong>None accepted</strong><p>This is not a passing import.</p></div> : <ol className="conversation-list">{conversations.map((conversation, index) => <li key={conversation.conversation_id}><Link href={`/agents/${agentId}/imports/${importId}/conversations/${conversation.conversation_id}`}><span className="num">{String(index + 1).padStart(2, "0")}</span><span><strong>{conversation.conversation_id}</strong><small>{conversation.line_number ? `Physical line ${conversation.line_number}` : conversation.status ?? "Accepted"}</small></span><b aria-hidden="true">→</b></Link></li>)}</ol>}
        </div>
        <div className="self-serve-card">
          <div className="card-heading"><h2>Rejected lines</h2><span>{rejections?.length ?? "—"}</span></div>
          {rejections === null ? <LoadingNotice /> : rejections.length === 0 ? <div className="self-serve-empty"><strong>No rejections</strong><p>All physical lines matched the prescribed contract.</p></div> : <ul className="rejection-list">{rejections.map((rejection) => <li key={`${rejection.line_number}-${rejection.reason_code}`}><code>Line {rejection.line_number}</code><div><strong>{rejection.reason_code}</strong><p>{rejection.message ?? "This line did not match the prescribed contract."}</p></div></li>)}</ul>}
        </div>
      </section>
    </>}
  </SelfServePage>;
}
