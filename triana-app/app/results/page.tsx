import { loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable, Fact, LabsPage, RouteLink, Section, Status, Unavailable } from "@/components/labs/LabsPage";

export default async function ResultsPage() {
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  const { results, limitations, lineage } = labsReport;
  const sections = [
    ["What Triana learned from the traces", results.learned, "/behavior", "Explore behavior"],
    ["What situations Triana created", results.created, "/cases", "View cases"],
    ["What happened when those situations ran", results.happened, "/run", "Inspect runs"],
    ["What exactly requires human judgment", results.judgment, "/review", "View judgment"],
  ] as const;
  return (
    <LabsPage
      eyebrow="Report overview"
      title={labsReport.title}
      summary="What Triana read, constructed, observed, could not establish, and asks a human to judge."
      meta={<><Status value={labsReport.privacy_class} /><code>{labsReport.report_id}</code></>}
    >
      <aside className="bundle-disclosure" aria-label="Backend report disclosure">
        <span>Backend report</span>
        <strong>{labsReport.evidence_class}</strong>
        <p>Every visible result below is rendered from the validated backend report.</p>
      </aside>
      <div className="result-stage">
        <div className="result-questions">
        {sections.map(([title, value, href, label], index) => <section key={title}>
          <span className="result-number num">0{index + 1}</span><div><h2>{title}</h2><h3>{value.headline}</h3><p>{value.detail}</p><RouteLink href={href}>{label}</RouteLink></div>
        </section>)}
        </div>
      </div>
      <Section title="Run accounting" description="Missing cost stays unavailable; zero-action policies remain explicit.">
        <dl className="summary-strip accounting-strip">
          <Fact label="HTTP exchanges"><span className="num">{results.accounting.http_exchange_count}</span></Fact>
          <Fact label="Tool calls"><span className="num">{results.accounting.tool_call_count}</span></Fact>
          <Fact label="Actual cost">{results.accounting.actual_cost_usd === null ? <Unavailable /> : <span className="num">${results.accounting.actual_cost_usd}</span>}</Fact>
          <Fact label="Privacy gaps"><span className="num">{results.accounting.privacy_gap_count}</span></Fact>
          <Fact label="Retries"><span className="num">{results.accounting.retry_count}</span></Fact>
          <Fact label="Repairs"><span className="num">{results.accounting.repair_count}</span></Fact>
          <Fact label="Fallbacks"><span className="num">{results.accounting.fallback_count}</span></Fact>
        </dl>
        <div className="lineage-line"><span>Lineage</span><code>{lineage.report_contract}</code><code>{lineage.compiler_result_hash ?? lineage.report_hash}</code></div>
      </Section>
      <Section title="Visible limitations" description="Claims blocked by missing evaluation stay in the interface.">
        <ul className="limitation-list">{limitations.map((item) => <li key={item.limitation_id}><Status value={item.status} /><div><strong>{item.title}</strong><p>{item.detail}</p><small>{item.claim_blocked}</small></div></li>)}</ul>
      </Section>
    </LabsPage>
  );
}
