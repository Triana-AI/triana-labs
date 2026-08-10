import { ImportDetailClient } from "@/components/self-serve/ImportDetailClient";

export default async function ImportPage({ params }: { params: Promise<{ agentId: string; importId: string }> }) {
  const { agentId, importId } = await params;
  return <ImportDetailClient agentId={agentId} importId={importId} />;
}
