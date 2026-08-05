import { getCase, getReview, type Conversation } from "@/lib/labs-report";
import { Fact, LabsPage, RouteLink, Status, Unavailable } from "@/components/labs/LabsPage";

export function ConversationDetail({ conversation }: { conversation: Conversation }) {
  const item = getCase(conversation.case_id);
  const review = getReview(conversation.conversation_id);
  const evidence = new Map(conversation.evidence_refs.map((ref) => [ref.evidence_ref_id, ref]));

  return (
    <LabsPage
      eyebrow={`Conversation ${conversation.conversation_id}`}
      title={item.title}
      summary="The complete recorded transcript stays primary; case context and evidence qualify it nearby."
      meta={<><Status value={conversation.status} /><span className="mono-label">{conversation.current_turn} / {conversation.turn_limit} turns</span></>}
    >
      <div className="conversation-layout">
        <section className="transcript" aria-label="Recorded transcript">
          {conversation.turns.length ? conversation.turns.map((turn) => {
            const attachedGaps = conversation.gaps.filter(({ turn_ordinal }) => turn_ordinal === turn.ordinal);
            const attachedEvents = conversation.tool_events.filter(({ after_turn_ordinal }) => after_turn_ordinal === turn.ordinal);
            return (
              <article className="transcript-turn" key={turn.turn_id} data-role={turn.role.toLowerCase()}>
                <header><span>{turn.role}</span><code>{turn.ordinal.toString().padStart(2, "0")}</code></header>
                <p>{turn.content}</p>
                {turn.evidence_ref_ids.length ? <ul className="evidence-chips" aria-label={`Evidence for turn ${turn.ordinal}`}>
                  {turn.evidence_ref_ids.map((refId) => <li key={refId}>{evidence.get(refId)?.label}</li>)}
                </ul> : null}
                {attachedEvents.map((event) => <div className="tool-event" key={event.tool_event_id}>
                  <span>Tool event</span><code>{event.tool_name}</code><Status value={event.status} /><p>{event.detail}</p>
                </div>)}
                {attachedGaps.map((gap) => <div className="gap-note" key={gap.gap_id}>
                  <Status value="PARTIAL" /><strong>{gap.label}</strong><p>{gap.detail}</p><code>{gap.reason_code}</code>
                </div>)}
              </article>
            );
          }) : <div className="empty-evidence"><Status value={conversation.status} /><p>{conversation.latest}</p><p>No transcript turns were recorded.</p></div>}
          {conversation.gaps.filter(({ turn_ordinal }) => turn_ordinal === null).map((gap) => <div className="gap-note" key={gap.gap_id}>
            <Status value={conversation.status} /><strong>{gap.label}</strong><p>{gap.detail}</p><code>{gap.reason_code}</code>
          </div>)}
          <footer className="transcript-accounting">
            <Fact label="HTTP exchanges"><span className="num">{conversation.accounting.http_exchange_count}</span></Fact>
            <Fact label="Tool calls"><span className="num">{conversation.accounting.tool_call_count}</span></Fact>
            <Fact label="Actual cost">{conversation.accounting.actual_cost_usd === null ? <Unavailable /> : <span className="num">${conversation.accounting.actual_cost_usd}</span>}</Fact>
          </footer>
        </section>

        <aside className="case-context">
          <h2>Case context</h2>
          <dl>
            <Fact label="User goal">{item.goal}</Fact>
            <Fact label="Done condition">{item.done_condition}</Fact>
            <Fact label="Constraints"><ul>{item.constraints.map((constraint) => <li key={constraint}>{constraint}</li>)}</ul></Fact>
            <Fact label="Simulated user"><strong>{item.simulated_user.persona_label}</strong><span>{item.simulated_user.intent_label}</span><span>{item.simulated_user.turn_policy_label}</span></Fact>
            <Fact label="Goal evidence"><Status value={conversation.goal_state} /></Fact>
            <Fact label="Human judgment"><Status value={review.review_state} /></Fact>
          </dl>
          <div className="world-list">
            <h3>World availability</h3>
            <p>{item.world_availability.section_label}</p>
            {item.world_availability.items.map((worldItem) => <div key={worldItem.item_id}>
              <span>{worldItem.label}</span><Status value={worldItem.status} /><small>{worldItem.detail}</small>
            </div>)}
          </div>
          <RouteLink href="/review">View recorded judgment</RouteLink>
        </aside>
      </div>
    </LabsPage>
  );
}
