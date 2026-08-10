import { ImportedConversationClient } from "@/components/self-serve/ImportedConversationClient";

export default async function ImportedConversationPage({ params }: { params: Promise<{ agentId: string; importId: string; conversationId: string }> }) {
  const { agentId, importId, conversationId } = await params;
  return <ImportedConversationClient agentId={agentId} importId={importId} conversationId={conversationId} />;
}
