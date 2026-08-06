"use client";

import { FormEvent, useState } from "react";
import {
  ConversationEvent,
  ConversationViewer,
  ConversationViewModel,
} from "@/components/conversation/ConversationViewer";

type Gap = { code: string; capability: string; state: string };
type Population = {
  population_id: string;
  label: string;
  description: string;
  support: number;
  evidence_trace_ids: string[];
  proposal_state: "PROPOSED";
};
type Proposal = {
  proposal_id: string;
  name: string;
  criterion: string;
  support: number;
  evidence_trace_ids: string[];
  proposal_state: "PROPOSED";
};
type Report = {
  report_id: string;
  accounting: {
    physical_record_count: number;
    accepted_conversation_count: number;
    rejected_record_count: number;
    upstream_physical_record_count?: number;
    canonical_normalized_record_count?: number;
  };
  populations: Population[];
  eval_proposals: Proposal[];
  qualified_eval_inventory: Proposal[];
  gaps: Gap[];
  stability: { state: string; semantic_run_count: number; disagreements: unknown[] };
  review_state: { state: string; ruling_count: number };
  behavior_analytics: {
    conversation_count: number;
    tool_observed_conversation_count: number;
    event_kind_counts: Record<string, number>;
    turn_count: { minimum: number; maximum: number; total: number };
  };
  outcome_analytics?: {
    authority: "DETERMINISTIC";
    source: string;
    denominator: number;
    success_count: number;
    failure_count: number;
    mean_reward: number;
  };
  method: {
    semantic_discovery_conversation_count: number;
    sealed_calibration_conversation_count: number;
    sealed_holdout_conversation_count: number;
    persisted_conversation_split: string;
  };
};
type ReviewItem = {
  item_id: string;
  item_hash: string;
  item_kind: "POPULATION_PAIR" | "EVAL_PROPOSAL";
  allowed_decisions: string[];
  name?: string;
  criterion?: string;
  trace_ids?: string[];
  evidence_trace_ids?: string[];
};
type Queue = { report_id: string; items: ReviewItem[] };
type RunReceipt = { report: Report; review_queue: Queue };
type ReviewState = {
  review_queue: Queue;
  current_rulings: Array<{ item_id: string; decision: string }>;
};
type PreviewEvent = Record<string, unknown> & { sequence: number; event_kind: string };
type PreviewTrace = { trace_id: string; events: PreviewEvent[] };
const requestBackend = globalThis.fetch.bind(globalThis);

function toConversation(trace: PreviewTrace): ConversationViewModel {
  const events: ConversationEvent[] = trace.events.map((event) => {
    const sequence = event.sequence;
    if (event.event_kind === "USER_MESSAGE" || event.event_kind === "ASSISTANT_MESSAGE" || event.event_kind === "SYSTEM_VISIBLE_MESSAGE") {
      return {
        kind: "message",
        sequence,
        role: event.event_kind === "USER_MESSAGE" ? "user" : event.event_kind === "ASSISTANT_MESSAGE" ? "assistant" : "system",
        content: typeof event.content === "string" ? event.content : "",
      };
    }
    if (event.event_kind === "TOOL_CALL") return {
      kind: "tool_call",
      sequence,
      callId: typeof event.call_id === "string" ? event.call_id : undefined,
      toolName: typeof event.tool_name === "string" ? event.tool_name : "unknown-tool",
      arguments: event.arguments,
    };
    if (event.event_kind === "TOOL_RESULT") return {
      kind: "tool_result",
      sequence,
      callId: typeof event.call_id === "string" ? event.call_id : undefined,
      status: typeof event.result_state === "string" ? event.result_state : undefined,
      result: event.result ?? event.error_code ?? null,
    };
    return {
      kind: "terminal",
      sequence,
      status: typeof event.terminal_state === "string" ? event.terminal_state : "UNKNOWN",
      detail: typeof event.reason_code === "string" ? event.reason_code : undefined,
    };
  });
  return { conversation_id: trace.trace_id, status: "OBSERVED", events };
}

export default function AnalysisPage() {
  const [sourcePath, setSourcePath] = useState("");
  const [sourceKind, setSourceKind] = useState("preview-trace-jsonl");
  const [reportId, setReportId] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [queue, setQueue] = useState<Queue | null>(null);
  const [conversation, setConversation] = useState<ConversationViewModel | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rulings, setRulings] = useState<Record<string, string>>({});

  async function start(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setConversation(null);
    try {
      const response = await requestBackend("/api/v1/trace-to-eval/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sourceKind === "manifest"
          ? { manifest_path: sourcePath }
          : { source_path: sourcePath, source_kind: sourceKind }),
      });
      if (!response.ok) throw new Error("Analysis was rejected. Check the manifest path and source integrity.");
      const receipt = await response.json() as RunReceipt;
      setReport(receipt.report);
      setQueue(receipt.review_queue);
      setReportId(receipt.report.report_id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Analysis failed.");
    } finally {
      setBusy(false);
    }
  }

  async function refresh() {
    if (!reportId) return;
    setBusy(true);
    setError(null);
    try {
      const [reportResponse, reviewResponse] = await Promise.all([
        requestBackend(`/api/v1/trace-to-eval/reports/${encodeURIComponent(reportId)}`),
        requestBackend(`/api/v1/trace-to-eval/reports/${encodeURIComponent(reportId)}/review`),
      ]);
      if (!reportResponse.ok || !reviewResponse.ok) throw new Error("Report or review state was not found or failed integrity validation.");
      setReport(await reportResponse.json() as Report);
      const review = await reviewResponse.json() as ReviewState;
      setQueue(review.review_queue);
      setRulings(Object.fromEntries(review.current_rulings.map((ruling) => [ruling.item_id, ruling.decision])));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Report refresh failed.");
    } finally {
      setBusy(false);
    }
  }

  async function openConversation(traceId: string) {
    if (!report) return;
    setError(null);
    const response = await requestBackend(`/api/v1/trace-to-eval/reports/${encodeURIComponent(report.report_id)}/conversations/${encodeURIComponent(traceId)}`);
    if (!response.ok) {
      setError("Cited conversation is unavailable or failed integrity validation.");
      return;
    }
    const value = await response.json() as { conversation: PreviewTrace };
    setConversation(toConversation(value.conversation));
  }

  async function downloadReport() {
    if (!report) return;
    setError(null);
    const response = await requestBackend(`/api/v1/trace-to-eval/reports/${encodeURIComponent(report.report_id)}`);
    if (!response.ok) {
      setError("Report download failed integrity validation.");
      return;
    }
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `triana-report-${report.report_id.slice(7, 19)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function rule(item: ReviewItem, decision: string) {
    if (!report) return;
    const editedText = decision === "EDIT" ? window.prompt("Enter the edited criterion") : null;
    if (decision === "EDIT" && !editedText) return;
    const response = await requestBackend(`/api/v1/trace-to-eval/reports/${encodeURIComponent(report.report_id)}/rulings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        artifact_kind: "human_ruling_v0",
        schema_version: 0,
        report_id: report.report_id,
        item_id: item.item_id,
        item_hash: item.item_hash,
        decision,
        edited_text: editedText,
        reviewer_id: "local-operator",
        ruled_at: new Date().toISOString(),
        supersedes_ruling_id: null,
      }),
    });
    if (!response.ok) {
      setError("Ruling was rejected and the ledger was not changed.");
      return;
    }
    setRulings((current) => ({ ...current, [item.item_id]: decision }));
  }

  return (
    <main className="labs-page">
      <header className="labs-hero">
        <div><span className="mono-label">Trace-to-Eval Review V0</span><h1>Analyze local traces</h1></div>
        <p>Point Triana at a supported local trace source or an evidence manifest. Raw traces remain local; semantic proposals are visibly separate from deterministic accounting and human rulings.</p>
      </header>

      <section className="labs-section light-section">
        <form onSubmit={start} className="setup-form">
          <label><span>Source format</span><select value={sourceKind} onChange={(event) => setSourceKind(event.target.value)}><option value="preview-trace-jsonl">PreviewTrace JSONL</option><option value="blitz-normalized-jsonl">Blitz normalized JSONL</option><option value="langsmith-normalized-jsonl">LangSmith normalized JSONL</option><option value="langsmith-grouped-jsonl">LangSmith grouped JSONL</option><option value="hrai-normalized-jsonl">HRAI normalized JSONL</option><option value="tau-preview-jsonl">TAU PreviewTrace JSONL</option><option value="tau-archive">TAU archive</option><option value="manifest">Evidence manifest</option></select></label>
          <label><span>Local source path</span><input value={sourcePath} onChange={(event) => setSourcePath(event.target.value)} placeholder="/absolute/path/to/traces.jsonl" required /></label>
          <button className="btn primary" type="submit" disabled={busy}>{busy ? "Working…" : "Run analysis"}</button>
        </form>
        <div className="setup-form">
          <label><span>Existing report ID</span><input value={reportId} onChange={(event) => setReportId(event.target.value)} placeholder="sha256:…" /></label>
          <button className="btn" type="button" onClick={refresh} disabled={busy || !reportId}>Refresh report</button>
        </div>
        {error ? <div className="limitation-callout"><strong>Operation stopped</strong><p>{error}</p></div> : null}
      </section>

      {report ? <>
        <section className="authority-strip">
          {report.accounting.upstream_physical_record_count !== undefined ? <div className="labs-fact"><span className="mono-label">Source rows</span><strong>{report.accounting.upstream_physical_record_count}</strong></div> : null}
          <div className="labs-fact"><span className="mono-label">Analyzed conversations</span><strong>{report.accounting.accepted_conversation_count}</strong></div>
          <div className="labs-fact"><span className="mono-label">Rejected</span><strong>{report.accounting.rejected_record_count}</strong></div>
          <div className="labs-fact"><span className="mono-label">Populations</span><strong>{report.populations.length}</strong></div>
          <div className="labs-fact"><span className="mono-label">Proposed evals</span><strong>{report.eval_proposals.length}</strong></div>
          <div className="labs-fact"><span className="mono-label">Semantic stability</span><strong>{report.stability.state}</strong></div>
        </section>

        <section className="labs-section light-section"><div className="section-heading"><div><span className="mono-label">Deterministic</span><h2>Behavior summary</h2></div><button className="btn" type="button" onClick={downloadReport}>Download report JSON</button></div><div className="authority-strip"><div className="labs-fact"><span className="mono-label">Conversations</span><strong>{report.behavior_analytics.conversation_count}</strong></div><div className="labs-fact"><span className="mono-label">Tool observed</span><strong>{report.behavior_analytics.tool_observed_conversation_count}</strong></div><div className="labs-fact"><span className="mono-label">Turns</span><strong>{report.behavior_analytics.turn_count.total}</strong><p>{report.behavior_analytics.turn_count.minimum}–{report.behavior_analytics.turn_count.maximum} per conversation</p></div><div className="labs-fact"><span className="mono-label">Discovery visible</span><strong>{report.method.semantic_discovery_conversation_count}</strong><p>{report.method.persisted_conversation_split}</p></div><div className="labs-fact"><span className="mono-label">Sealed</span><strong>{report.method.sealed_calibration_conversation_count + report.method.sealed_holdout_conversation_count}</strong><p>{report.method.sealed_calibration_conversation_count} calibration · {report.method.sealed_holdout_conversation_count} holdout</p></div></div><div className="row-evidence">{Object.entries(report.behavior_analytics.event_kind_counts).map(([kind, count]) => <span className="labs-status" key={kind}>{kind}: {count}</span>)}</div></section>

        {report.outcome_analytics ? <section className="labs-section light-section"><div className="section-heading"><div><span className="mono-label">Official outcome evidence</span><h2>Observed benchmark result</h2></div><span className="labs-status">{report.outcome_analytics.authority}</span></div><div className="authority-strip"><div className="labs-fact"><span className="mono-label">Denominator</span><strong>{report.outcome_analytics.denominator}</strong></div><div className="labs-fact"><span className="mono-label">Success</span><strong>{report.outcome_analytics.success_count}</strong></div><div className="labs-fact"><span className="mono-label">Failure</span><strong>{report.outcome_analytics.failure_count}</strong></div><div className="labs-fact"><span className="mono-label">Mean reward</span><strong>{report.outcome_analytics.mean_reward.toFixed(4)}</strong></div></div><p>Source: {report.outcome_analytics.source}. This is deterministic source reward accounting, not an L4 judgment or first-broken-link explanation.</p></section> : null}

        {report.gaps.length ? <section className="labs-section light-section"><h2>Typed gaps</h2><div className="operational-list">{report.gaps.map((gap) => <article className="operational-row" key={gap.code}><code>{gap.code}</code><div><strong>{gap.capability}</strong><p>{gap.state}</p></div></article>)}</div></section> : null}

        <section className="labs-section light-section"><h2>Proposed user populations</h2><p>Model-proposed meaning; deterministic support and citations.</p><div className="operational-list">{report.populations.map((population) => <article className="operational-row" key={population.population_id}><div><span className="labs-status">{population.proposal_state}</span><h3>{population.label}</h3><p>{population.description}</p></div><div><strong>{population.support} conversations</strong><div className="row-evidence">{population.evidence_trace_ids.map((traceId) => <button className="btn" type="button" onClick={() => openConversation(traceId)} key={traceId}>{traceId}</button>)}</div></div></article>)}</div></section>

        <section className="labs-section light-section"><h2>Proposed evals</h2><p>At most three primary proposals; a human must Track, Edit, or Defer.</p><div className="operational-list">{report.eval_proposals.map((proposal) => <article className="operational-row" key={proposal.proposal_id}><div><span className="labs-status">{proposal.proposal_state}</span><h3>{proposal.name}</h3><p>{proposal.criterion}</p></div><div className="row-evidence">{proposal.evidence_trace_ids.map((traceId) => <button className="btn" type="button" onClick={() => openConversation(traceId)} key={traceId}>{traceId}</button>)}</div></article>)}</div></section>

        {queue ? <section className="labs-section light-section"><h2>Human review queue</h2><div className="operational-list">{queue.items.map((item) => <article className="operational-row" key={item.item_id}><div><span className="mono-label">{item.item_kind}</span><h3>{item.name ?? "Do these conversations express the same need?"}</h3><p>{item.criterion ?? (item.trace_ids ?? []).join(" ↔ ")}</p></div><div>{rulings[item.item_id] ? <strong>{rulings[item.item_id]}</strong> : item.allowed_decisions.map((decision) => <button className="btn" type="button" onClick={() => rule(item, decision)} key={decision}>{decision}</button>)}</div></article>)}</div></section> : null}

        {conversation ? <section className="labs-section light-section"><ConversationViewer conversation={conversation} context={<div><span className="mono-label">Evidence for</span><strong>{report.report_id}</strong><button className="btn" type="button" onClick={() => setConversation(null)}>Close evidence</button></div>} /></section> : null}
      </> : null}
    </main>
  );
}
