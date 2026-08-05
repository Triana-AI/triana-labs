import { labsReport } from "@/lib/labs-report";
import { Fact, LabsPage, Section, Status } from "@/components/labs/LabsPage";

export default function SetupPage() {
  const { setup, sample_disclosure: disclosure } = labsReport;
  const { understanding } = setup;
  return (
    <LabsPage
      eyebrow="Report source"
      title="Understand the trace file"
      summary="One checked-in synthetic report shows what Triana read, accepted, rejected, and left unassessed."
      meta={<><Status value={setup.adapter.mapping_status} /><code>{setup.adapter.adapter_id}@{setup.adapter.adapter_version}</code></>}
    >
      <aside className="sample-disclosure"><strong>Public synthetic reference</strong><p>{disclosure}</p></aside>
      <Section title="Trace source" description="This slice reads a recorded local artifact; it does not ingest or contact anything.">
        <dl className="facts-grid">
          <Fact label="File"><code>{setup.source.display_name}</code></Fact>
          <Fact label="Source kind"><span>{setup.source.source_kind}</span></Fact>
          <Fact label="Custody"><span>{setup.source.custody}</span></Fact>
          <Fact label="Authorization"><span>{setup.source.authorization}</span></Fact>
        </dl>
      </Section>
      <Section title="Trace understanding" description="Transparent report-owned counts replace an opaque quality score.">
        <div className="summary-strip">
          <Fact label="Physical records"><span className="num">{understanding.physical_record_count}</span></Fact>
          <Fact label="Accepted records"><span className="num">{understanding.accepted_record_count}</span></Fact>
          <Fact label="Rejected records"><span className="num">{understanding.rejected_record_count}</span></Fact>
          <Fact label="Usable conversations"><span className="num">{understanding.usable_conversation_count}</span></Fact>
        </div>
        <div className="operational-list">
          {understanding.rejection_reasons.map((reason) => <article className="operational-row" key={reason.reason_code}>
            <code>{reason.reason_code}</code><strong>{reason.label}</strong><span className="num">{reason.count}</span>
          </article>)}
        </div>
      </Section>
      <Section title="Unassessed semantics" description="These unknowns remain visible and do not become success claims.">
        <ul className="limitation-list">{understanding.unassessed_semantics.map((item) => <li key={item}><Status value="UNKNOWN" /><span>{item}</span></li>)}</ul>
      </Section>
    </LabsPage>
  );
}
