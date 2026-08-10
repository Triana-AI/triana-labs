import { ConversationViewer, type ConversationEvent } from "@/components/conversation/ConversationViewer";
import { Fact, LabsPage, RouteLink, Status, Unavailable } from "@/components/labs/LabsPage";
import { getCase, getReview, type Conversation, type LabsReport } from "@/lib/labs-report";

export function LegacyReportConversationAdapter({ report, conversation }: { report: LabsReport; conversation: Conversation }) {
  const item = getCase(report, conversation.case_id);
  const review = getReview(report, conversation.conversation_id);
  const events: ConversationEvent[] = [];
  for (const turn of conversation.turns) {
    events.push({ kind: "message", sequence: turn.ordinal * 10, role: turn.role === "USER" ? "user" : "assistant", content: turn.content });
    conversation.tool_events.filter((event) => event.after_turn_ordinal === turn.ordinal).forEach((event, index) => {
      events.push({ kind: "tool_call", sequence: turn.ordinal * 10 + index + 1, callId: event.tool_event_id, toolName: event.tool_name, arguments: event.detail });
    });
    conversation.gaps.filter((gap) => gap.turn_ordinal === turn.ordinal).forEach((gap) => {
      events.push({ kind: "gap", sequence: turn.ordinal * 10 + 9, code: gap.reason_code, detail: `${gap.label}: ${gap.detail}` });
    });
  }
  conversation.gaps.filter((gap) => gap.turn_ordinal === null).forEach((gap) => {
    events.push({ kind: "gap", code: gap.reason_code, detail: `${gap.label}: ${gap.detail}` });
  });
  if (conversation.termination_reason) {
    events.push({ kind: "terminal", sequence: (conversation.turn_limit + 1) * 10, status: conversation.status, detail: conversation.termination_reason });
  }

  const context = <>
    <h2>Case context</h2>
    <dl>
      <Fact label="User goal">{item.goal}</Fact>
      <Fact label="Done condition">{item.done_condition}</Fact>
      <Fact label="Constraints"><ul>{item.constraints.map((constraint) => <li key={constraint}>{constraint}</li>)}</ul></Fact>
      <Fact label="Goal evidence"><Status value={conversation.goal_state} /></Fact>
      <Fact label="Human judgment"><Status value={review.review_state} /></Fact>
      <Fact label="HTTP exchanges"><span className="num">{conversation.accounting.http_exchange_count}</span></Fact>
      <Fact label="Tool calls"><span className="num">{conversation.accounting.tool_call_count}</span></Fact>
      <Fact label="Actual cost">{conversation.accounting.actual_cost_usd === null ? <Unavailable /> : `$${conversation.accounting.actual_cost_usd}`}</Fact>
    </dl>
    <RouteLink href="/review">View recorded judgment</RouteLink>
  </>;

  return <LabsPage
    surface="conversation"
    eyebrow={`Conversation ${conversation.conversation_id}`}
    title={item.title}
    summary="The complete recorded transcript stays primary; case context and evidence qualify it nearby."
    meta={<><Status value={conversation.status} /><span className="mono-label">{conversation.current_turn} / {conversation.turn_limit} turns</span></>}
  >
    <ConversationViewer conversation={{ conversationId: conversation.conversation_id, status: conversation.status, events }} context={context} />
  </LabsPage>;
}
