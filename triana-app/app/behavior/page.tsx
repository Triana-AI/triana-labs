import { loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable, Fact, LabsPage, Section, Status } from "@/components/labs/LabsPage";

export default async function BehaviorPage() {
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  const { behavior } = labsReport;
  return (
    <LabsPage
      eyebrow="Observed user behavior"
      title="Structural groups, explicit authority"
      summary="Deterministic membership and support stay separate from model-proposed summaries."
      meta={<><Status value={behavior.population_claim} /><span className="mono-label">{behavior.derivation_kind}</span></>}
    >
      <div className="authority-strip">
        <Fact label="Membership"><strong>{behavior.membership_authority}</strong></Fact>
        <Fact label="Summary wording"><strong>{behavior.semantic_summary_authority}</strong></Fact>
        <Fact label="Population claim"><Status value={behavior.population_claim} /></Fact>
      </div>
      <Section title="Behavior groups" description="Shares are supplied by the report and are not presented as an exhaustive partition.">
        <div className="operational-list behavior-list">
          {behavior.groups.map((group) => <article className="operational-row behavior-row" key={group.group_id}>
            <div className="row-id"><code>{group.group_id}</code><Status value={group.fidelity_label} /></div>
            <div className="row-main"><h3>{group.label}</h3><p>{group.summary}</p><small>{group.structural_pattern}</small></div>
            <dl className="row-measures"><Fact label="Support"><span className="num">{group.support_count}</span></Fact><Fact label="Share"><span className="num">{(group.share_basis_points / 100).toFixed(2)}%</span><code>{group.share_basis_points} bp</code></Fact></dl>
            <div className="row-evidence"><span>Evidence</span>{group.source_evidence_ids.map((id) => <code key={id}>{id}</code>)}</div>
          </article>)}
        </div>
      </Section>
      <Section title="Current limitation" description="The report names the claim it cannot support.">
        {labsReport.limitations.filter(({ limitation_id }) => limitation_id.includes("semantic") || limitation_id.includes("population")).map((item) => <article className="limitation-callout" key={item.limitation_id}>
          <Status value={item.status} /><div><h3>{item.title}</h3><p>{item.detail}</p><strong>{item.claim_blocked}</strong></div>
        </article>)}
      </Section>
    </LabsPage>
  );
}
