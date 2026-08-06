import { getCase, loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable, Fact, LabsPage, RouteLink, Section, Status } from "@/components/labs/LabsPage";

export default async function RunPage() {
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  const { run } = labsReport;
  return (
    <LabsPage
      surface="runs"
      eyebrow="Recorded execution"
      title="Conversation runs"
      summary="Each selected case has one independent recorded conversation; weaker states stay visible."
      meta={<><Status value={run.recorded_state} /><code>{run.run_id}</code></>}
    >
      <div className="preflight-grid">
        <section><h2>Target</h2><strong>{run.target.label}</strong><code>{run.target.target_id}</code><Status value={run.target.connection_state} /></section>
        <section><h2>Simulated users</h2><strong>{run.simulator.identity_count} fixed identities</strong><span>{run.simulator.provider_label}</span><code>{run.simulator.model_label}</code></section>
        <section><h2>Privacy and egress</h2><strong>Synthetic use recorded</strong><span>{run.privacy_egress.provider}</span><span>{run.privacy_egress.target}</span></section>
      </div>
      <Section tone="light" title="Execution limits" description="The recorded run used no retry, repair, or fallback.">
        <div className="summary-strip limits-strip">
          <Fact label="Selected cases"><span className="num">{run.limits.selected_case_count}</span></Fact>
          <Fact label="Turn limit"><span className="num">{run.limits.max_turns_per_conversation}</span></Fact>
          <Fact label="Conversation limit"><span className="num">{run.limits.max_conversations}</span></Fact>
          <Fact label="HTTP limit"><span className="num">{run.limits.max_http_exchanges}</span></Fact>
          <Fact label="Minute limit"><span className="num">{run.limits.max_minutes_per_conversation}</span></Fact>
          <Fact label="Reserved ceiling"><span className="num">${run.limits.reserved_cost_ceiling_usd}</span></Fact>
        </div>
        <p className="policy-line"><span>{run.limits.retry_policy} retry</span><span>{run.limits.repair_policy} repair</span><span>{run.limits.fallback_policy} fallback</span></p>
      </Section>
      <Section tone="dark" title="Recorded conversations" description="Open a row for transcript, case context, gaps, and evidence.">
        <div className="operational-list run-list">
          {run.conversation_order.map((conversationId, index) => {
            const conversation = labsReport.conversations.find((item) => item.conversation_id === conversationId);
            if (!conversation) throw new Error(`Broken conversation order: ${conversationId}`);
            const item = getCase(labsReport, conversation.case_id);
            return <article className="operational-row run-row" key={conversationId}>
              <span className="run-index num">{String(index + 1).padStart(2, "0")}</span>
              <div className="row-main"><code>{conversation.conversation_id}</code><h3>{item.title}</h3><p>{conversation.latest}</p></div>
              <Status value={conversation.status} />
              <span className="turn-count num">{conversation.current_turn} / {conversation.turn_limit}</span>
              <RouteLink href={`/conversations/${conversation.conversation_id}`}>Inspect</RouteLink>
            </article>;
          })}
        </div>
      </Section>
    </LabsPage>
  );
}
