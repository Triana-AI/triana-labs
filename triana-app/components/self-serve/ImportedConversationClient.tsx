"use client";

import { useEffect, useState } from "react";
import { ConversationViewer, type ConversationViewModel } from "@/components/conversation/ConversationViewer";
import { selfServeApi } from "@/lib/self-serve/api";
import { Breadcrumbs, ErrorNotice, LoadingNotice, SelfServePage } from "@/components/self-serve/SelfServePage";

export function ImportedConversationClient({ agentId, importId, conversationId }: { agentId: string; importId: string; conversationId: string }) {
  const [conversation, setConversation] = useState<ConversationViewModel | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { selfServeApi.getConversation(conversationId).then(setConversation).catch((value: Error) => setError(value.message)); }, [conversationId]);
  return <SelfServePage eyebrow="Imported trace" title="Conversation" description="Messages and tool activity are shown in deterministic source order.">
    <Breadcrumbs items={[{ label: "Agents", href: "/agents" }, { label: agentId, href: `/agents/${agentId}` }, { label: "Import", href: `/agents/${agentId}/imports/${importId}` }, { label: conversationId }]} />
    {error ? <ErrorNotice message={error} /> : conversation === null ? <LoadingNotice label="Loading conversation…" /> : <ConversationViewer conversation={conversation} />}
  </SelfServePage>;
}
