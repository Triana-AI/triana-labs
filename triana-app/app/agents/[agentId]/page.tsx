import { AgentDetailClient } from "@/components/self-serve/AgentDetailClient";

export default async function AgentPage({ params }: { params: Promise<{ agentId: string }> }) {
  const { agentId } = await params;
  return <AgentDetailClient agentId={agentId} />;
}
