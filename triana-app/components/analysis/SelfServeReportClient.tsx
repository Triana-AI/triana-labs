"use client";

import { useEffect, useMemo, useState } from "react";
import { PartialHandlingEvidence } from "@/components/analysis/PartialHandlingEvidence";
import { ConversationViewer, type ConversationViewModel } from "@/components/conversation/ConversationViewer";
import { Breadcrumbs, ErrorNotice, LoadingNotice, SelfServePage } from "@/components/self-serve/SelfServePage";
import { selfServeApi } from "@/lib/self-serve/api";
import type { TraceToEvalReport, TraceToEvalReviewItem, TraceToEvalReviewState } from "@/lib/self-serve/types";

type Tab = "overview" | "behavior" | "evals" | "review" | "lineage";

export function SelfServeReportClient({ agentId, reportId }: { agentId: string; reportId: string }) {
  const [report, setReport] = useState<TraceToEvalReport | null>(null);
  const [review, setReview] = useState<TraceToEvalReviewState | null>(null);
  const [conversation, setConversation] = useState<ConversationViewModel | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [busyItem, setBusyItem] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const [nextReport, nextReview] = await Promise.all([
      selfServeApi.getAnalysisReport(reportId),
      selfServeApi.getAnalysisReview(reportId),
    ]);
    if (nextReport.agent_id !== agentId) throw new Error("This report does not belong to the selected agent.");
    setReport(nextReport);
    setReview(nextReview);
  }

  useEffect(() => { reload().catch((value: Error) => setError(value.message)); }, [agentId, reportId]);
  const current = useMemo(() => new Map(review?.current_rulings.map((item) => [item.item_id, item]) ?? []), [review]);

  async function openEvidence(traceId: string) {
    setError(null);
    try { setConversation(await selfServeApi.getAnalysisConversation(reportId, traceId)); }
    catch (value) { setError(value instanceof Error ? value.message : "Evidence is unavailable."); }
  }

  async function rule(item: TraceToEvalReviewItem, decision: string) {
    const editedText = decision === "EDIT" ? edits[item.item_id]?.trim() : null;
    if (decision === "EDIT" && !editedText) { setError("Enter the edited criterion before saving."); return; }
    setBusyItem(item.item_id); setError(null);
    try {
      await selfServeApi.appendAnalysisRuling(reportId, {
        item_id: item.item_id,
        item_hash: item.item_hash,
        decision,
        edited_text: editedText,
        supersedes_ruling_id: current.get(item.item_id)?.ruling_id ?? null,
      });
      await reload();
    } catch (value) { setError(value instanceof Error ? value.message : "Ruling was rejected."); }
    finally { setBusyItem(null); }
  }

  if (error && !report) return <SelfServePage eyebrow="Analysis report" title="Report unavailable" description="The backend refused or could not verify this report."><ErrorNotice message={error} /></SelfServePage>;
  if (!report || !review) return <SelfServePage eyebrow="Analysis report" title="Loading report" description="Verifying canonical artifacts and owner scope."><LoadingNotice /></SelfServePage>;

  const tabs: Array<[Tab, string]> = [["overview", "Overview"], ["behavior", "User behavior"], ["evals", "Eval proposals"], ["review", "Review"], ["lineage", "Lineage & gaps"]];
  return <SelfServePage eyebrow="Canonical trace analysis" title="Analysis report" description="Deterministic facts, model proposals, and human judgments remain visibly separate.">
    <Breadcrumbs items={[{ label: "Agents", href: "/agents" }, { label: agentId, href: `/agents/${agentId}` }, { label: report.report_id }]} />
    {error ? <ErrorNotice message={error} /> : null}
    <section className="accounting-row" aria-label="Report accounting">
      <div><span>Accepted</span><strong>{report.accounting.accepted_conversation_count}</strong></div>
      <div><span>Rejected</span><strong>{report.accounting.rejected_record_count}</strong></div>
      <div><span>Populations</span><strong>{report.populations.length}</strong></div>
      <div><span>Proposed evals</span><strong>{report.eval_proposals.length}</strong></div>
    </section>
    <nav className="row-evidence" aria-label="Report sections">{tabs.map(([value, label]) => <button className={tab === value ? "primary-button" : "quiet-button"} type="button" onClick={() => setTab(value)} key={value}>{label}</button>)}</nav>

    {tab === "overview" ? <section className="self-serve-grid">
      <div className="self-serve-card"><span className="mono-label">Deterministic behavior</span><h2>{report.behavior_analytics.conversation_count} conversations</h2><p>{report.behavior_analytics.turn_count.total} turns · {report.behavior_analytics.tool_observed_conversation_count} with tool activity.</p><div className="row-evidence">{Object.entries(report.behavior_analytics.event_kind_counts).map(([kind, count]) => <span className="labs-status" key={kind}>{kind}: {count}</span>)}</div></div>
      <div className="self-serve-card"><span className="mono-label">Human authority</span><h2>{review.judgment_state}</h2><p>{report.judgment.required_review_item_count} bounded review items. No aggregate verdict is established.</p>{report.outcome_analytics ? <pre>{JSON.stringify(report.outcome_analytics, null, 2)}</pre> : <p>Outcome evidence is unavailable; no reward or pass was invented.</p>}</div>
    </section> : null}

    {tab === "behavior" ? <><PartialHandlingEvidence evidence={report.partial_handling_evidence} onOpenTrace={openEvidence} /><section className="self-serve-card"><div className="card-heading"><h2>Proposed user populations</h2><span>{report.stability.state}</span></div>{report.populations.length ? <div className="operational-list">{report.populations.map((population) => <article className="operational-row" key={population.population_id}><div><span className="labs-status">{population.proposal_state}</span><h3>{population.label}</h3><p>{population.description}</p></div><div><strong>{population.support} conversations</strong><div className="row-evidence">{population.evidence_trace_ids.map((id) => <button className="quiet-button" type="button" onClick={() => openEvidence(id)} key={id}>{id}</button>)}</div></div></article>)}</div> : <div className="self-serve-empty"><strong>Semantic populations unavailable</strong><p>Deterministic behavior accounting remains valid. No model-derived meaning was invented.</p></div>}</section></> : null}

    {tab === "evals" ? <section className="self-serve-card"><div className="card-heading"><h2>Proposed evals</h2><span>{report.eval_proposals.length} primary · {report.qualified_eval_inventory.length} qualified</span></div>{report.eval_proposals.length ? <div className="operational-list">{report.eval_proposals.map((proposal) => <article className="operational-row" key={proposal.proposal_id}><div><span className="labs-status">{proposal.proposal_state}</span><h3>{proposal.name}</h3><p>{proposal.criterion}</p></div><div className="row-evidence">{proposal.evidence_trace_ids.map((id) => <button className="quiet-button" type="button" onClick={() => openEvidence(id)} key={id}>{id}</button>)}</div></article>)}</div> : <div className="self-serve-empty"><strong>No eval proposal available</strong><p>Provider absence is a typed gap, not a successful evaluation.</p></div>}</section> : null}

    {tab === "review" ? <section className="self-serve-card"><div className="card-heading"><h2>Bounded human review</h2><span>{review.judgment_state}</span></div>{review.review_queue.items.length ? <div className="operational-list">{review.review_queue.items.map((item) => <ReviewRow item={item} currentDecision={current.get(item.item_id)?.decision} edit={edits[item.item_id] ?? ""} busy={busyItem === item.item_id} setEdit={(value) => setEdits((values) => ({ ...values, [item.item_id]: value }))} openEvidence={openEvidence} rule={rule} key={item.item_id} />)}</div> : <div className="self-serve-empty"><strong>No judgment requested</strong><p>The report produced no bounded semantic review items.</p></div>}</section> : null}

    {tab === "lineage" ? <section className="self-serve-grid"><div className="self-serve-card"><span className="mono-label">Typed gaps</span><h2>{report.gaps.length}</h2>{report.gaps.map((gap) => <div className="self-serve-notice" key={gap.code}><strong>{gap.capability}</strong><p>{gap.code} · {gap.state}</p></div>)}</div><div className="self-serve-card"><span className="mono-label">Immutable identity</span><h2>Lineage</h2><dl><dt>Report</dt><dd><code>{report.report_id}</code></dd><dt>Run</dt><dd><code>{report.run_id}</code></dd><dt>Import</dt><dd><code>{report.import_id}</code></dd></dl><details><summary>Method detail</summary><pre>{JSON.stringify(report.method, null, 2)}</pre></details></div></section> : null}

    {conversation ? <section className="self-serve-card"><div className="card-heading"><h2>Report-bound evidence</h2><button className="quiet-button" type="button" onClick={() => setConversation(null)}>Close</button></div><ConversationViewer conversation={conversation} context={<p>This conversation is cited by the canonical report and is visible from the DEVELOPMENT evidence split only.</p>} /></section> : null}
  </SelfServePage>;
}

function ReviewRow({ item, currentDecision, edit, busy, setEdit, openEvidence, rule }: { item: TraceToEvalReviewItem; currentDecision?: string; edit: string; busy: boolean; setEdit: (value: string) => void; openEvidence: (traceId: string) => void; rule: (item: TraceToEvalReviewItem, decision: string) => void }) {
  const evidence = item.trace_ids ?? item.evidence_trace_ids ?? [];
  return <article className="operational-row"><div><span className="mono-label">{item.item_kind}</span><h3>{item.name ?? "Do these conversations express the same need?"}</h3><p>{item.criterion ?? evidence.join(" ↔ ")}</p><div className="row-evidence">{evidence.map((id) => <button className="quiet-button" type="button" onClick={() => openEvidence(id)} key={id}>{id}</button>)}</div>{item.allowed_decisions.includes("EDIT") ? <label><span>Edited criterion</span><input value={edit} onChange={(event) => setEdit(event.target.value)} maxLength={2000} /></label> : null}</div><div><span className="labs-status">{currentDecision ?? "PENDING"}</span><div className="row-evidence">{item.allowed_decisions.map((decision) => <button className="quiet-button" disabled={busy} type="button" onClick={() => rule(item, decision)} key={decision}>{decision}</button>)}</div></div></article>;
}
