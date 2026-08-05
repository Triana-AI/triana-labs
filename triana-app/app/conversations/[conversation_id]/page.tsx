import { notFound } from "next/navigation";
import { ConversationDetail } from "@/components/labs/ConversationDetail";
import { labsReport } from "@/lib/labs-report";

export const dynamicParams = false;

export function generateStaticParams() {
  return labsReport.conversations.map(({ conversation_id }) => ({ conversation_id }));
}

export default async function ConversationPage({ params }: { params: Promise<{ conversation_id: string }> }) {
  const { conversation_id } = await params;
  const conversation = labsReport.conversations.find((item) => item.conversation_id === conversation_id);
  if (!conversation) notFound();
  return <ConversationDetail conversation={conversation} />;
}
