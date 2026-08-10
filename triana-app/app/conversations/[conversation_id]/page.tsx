import { notFound } from "next/navigation";
import { LegacyReportConversationAdapter } from "@/components/conversation/LegacyReportConversationAdapter";
import { loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable } from "@/components/labs/LabsPage";

export default async function ConversationPage({ params }: { params: Promise<{ conversation_id: string }> }) {
  const { conversation_id } = await params;
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  const conversation = labsReport.conversations.find((item) => item.conversation_id === conversation_id);
  if (!conversation) notFound();
  return <LegacyReportConversationAdapter report={labsReport} conversation={conversation} />;
}
