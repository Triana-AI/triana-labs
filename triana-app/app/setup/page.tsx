import { loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable, Fact, LabsPage, Section, Status } from "@/components/labs/LabsPage";

export default async function SetupPage() {
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  const { setup, sample_disclosure: disclosure } = labsReport;
  const { understanding } = setup;
  return (
    <LabsPage
      surface="source"
      eyebrow="Report source"
      title="Understand the trace file"
      summary="The configured backend report shows what Triana read, accepted, rejected, and left unassessed."
      meta={<><Status value={setup.adapter.mapping_status} /><code>{setup.adapter.adapter_id}@{setup.adapter.adapter_version}</code></>}
    >
      <aside className="sample-disclosure"><strong>{labsReport.evidence_class}</strong><p>{disclosure}</p></aside>
      <Section tone="dark" title="Trace source" description="These source facts come from the configured backend report.">
        <dl className="facts-grid">
          <Fact label="File"><code>{setup.source.display_name}</code></Fact>
          <Fact label="Source kind"><span>{setup.source.source_kind}</span></Fact>
          <Fact label="Custody"><span>{setup.source.custody}</span></Fact>
          <Fact label="Authorization"><span>{setup.source.authorization}</span></Fact>
        </dl>
      </Section>
      <Section tone="light" title="Trace understanding" description="Transparent report-owned counts replace an opaque quality score.">
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
      <Section tone="raised" title="Unassessed semantics" description="These unknowns remain visible and do not become success claims.">
        <ul className="limitation-list">{understanding.unassessed_semantics.map((item) => <li key={item}><Status value="UNKNOWN" /><span>{item}</span></li>)}</ul>
      </Section>
    </LabsPage>
  );
}
