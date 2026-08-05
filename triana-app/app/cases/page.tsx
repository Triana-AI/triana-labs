import { loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable, Fact, LabsPage, Section, Status } from "@/components/labs/LabsPage";

export default async function CasesPage() {
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  return (
    <LabsPage
      eyebrow="Grounded situations"
      title="Cases"
      summary="Every situation explains its goal, done condition, source basis, and available case data."
      meta={<span className="mono-label">{labsReport.results.created.selected_count} selected · {labsReport.results.created.excluded_count} excluded</span>}
    >
      <Section title="Seen in traces and grounded variations" description="Origin and selection are independent report-owned facts.">
        <div className="case-list">
          {labsReport.cases.map((item) => <article className="case-row" key={item.case_id}>
            <header><div><code>{item.case_id}</code><h3>{item.title}</h3></div><div className="status-pair"><Status value={item.origin} /><Status value={item.selection} /></div></header>
            <dl className="case-facts">
              <Fact label="User goal">{item.goal}</Fact>
              <Fact label="Done condition">{item.done_condition}</Fact>
              <Fact label="Why it exists">{item.why_it_exists}</Fact>
              <Fact label="Source basis">{item.source_basis}</Fact>
            </dl>
            <div className="case-detail-grid">
              <div><h4>Constraints</h4><ul>{item.constraints.map((constraint) => <li key={constraint}>{constraint}</li>)}</ul></div>
              <div className="world-list"><h4>World availability</h4><p>{item.world_availability.section_label}</p><Status value={item.world_availability.status} />
                {item.world_availability.items.map((worldItem) => <div key={worldItem.item_id}><span>{worldItem.label}</span><Status value={worldItem.status} /><small>{worldItem.detail}</small></div>)}
              </div>
              <div><h4>Simulated user</h4><p>{item.simulated_user.persona_label}</p><p>{item.simulated_user.intent_label}</p><code>{item.simulated_user.authority}</code></div>
            </div>
            {item.selection_reason ? <p className="case-reason"><strong>Exclusion reason</strong>{item.selection_reason}</p> : null}
          </article>)}
        </div>
      </Section>
    </LabsPage>
  );
}
