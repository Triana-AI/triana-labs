import { loadConfiguredLabsReport } from "@/lib/labs-report";
import { BackendReportUnavailable, LabsPage, Section, Status } from "@/components/labs/LabsPage";

export default async function CasesPage() {
  const loaded = await loadConfiguredLabsReport();
  if (loaded.availability === "UNAVAILABLE") return <BackendReportUnavailable />;
  const labsReport = loaded.report;
  return (
    <LabsPage
      surface="cases"
      eyebrow="Case workspace"
      title="Cases"
      summary="This surface is paused until real-run cases are available to shape it around actual operator evidence."
      meta={<Status value="BACKLOG" />}
    >
      <Section tone="light" title="Waiting for real-run cases" description="The synthetic cases remain in the report, but this draft intentionally does not turn them into a final case-management UI.">
        <div className="cases-backlog">
          <Status value="BACKLOG" />
          <div>
            <h3>Bring the first real run here</h3>
            <p>Once its case structure and evidence are available, this page can be designed around the decisions an operator actually needs to make.</p>
          </div>
        </div>
        <details className="cases-retained">
          <summary>Retained synthetic fixture metadata</summary>
          <ul>
            {labsReport.cases.map((item) => <li key={item.case_id}>
              <div><code>{item.case_id}</code><strong>{item.title}</strong></div>
              <div><Status value={item.origin} /><Status value={item.world_availability.status} /><Status value={item.selection} /></div>
            </li>)}
          </ul>
        </details>
      </Section>
    </LabsPage>
  );
}
