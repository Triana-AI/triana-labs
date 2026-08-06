import { SelfServeReportClient } from "@/components/analysis/SelfServeReportClient";

export default async function AgentAnalysisReportPage({ params }: { params: Promise<{ agentId: string; reportId: string }> }) {
  const { agentId, reportId } = await params;
  return <SelfServeReportClient agentId={agentId} reportId={decodeURIComponent(reportId)} />;
}
