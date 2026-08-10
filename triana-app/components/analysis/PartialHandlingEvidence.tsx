export interface PartialHandlingItem {
  trace_id: string;
  handling_mode: string;
  claimed_action: "TRUE" | "FALSE" | "UNKNOWN";
  terminal_summary: string;
  evidence_quotes: string[];
  tool_observed: boolean;
  turn_count: number;
}

export interface PartialHandlingEvidence {
  state: "PARTIAL";
  authority: "PROPOSAL_ONLY";
  completed_run_count: number;
  runs: Array<{ run_index: number; items: PartialHandlingItem[] }>;
  outcome_by_handling_mode?: Array<{
    handling_mode: string;
    denominator: number;
    trace_ids: string[];
    success_count: number;
    failure_count: number;
    mean_reward: number;
  }>;
}

export function PartialHandlingEvidence({
  evidence,
  onOpenTrace,
}: {
  evidence?: PartialHandlingEvidence;
  onOpenTrace: (traceId: string) => void;
}) {
  if (!evidence) return null;

  return (
    <section className="self-serve-card">
      <div className="card-heading">
        <div>
          <span className="mono-label">Handling evidence</span>
          <h2>Completed semantic runs</h2>
        </div>
        <div className="row-evidence">
          <span className="labs-status">PARTIAL</span>
          <span className="labs-status">PROPOSAL_ONLY</span>
        </div>
      </div>
      <p>{evidence.completed_run_count} completed runs are shown separately.</p>
      <div className="operational-list">
        {evidence.runs.map((run) => (
          <article className="operational-row" key={run.run_index}>
            <div>
              <span className="mono-label">Run {run.run_index}</span>
              <strong>{run.items.length} handling proposals</strong>
            </div>
            <div className="row-evidence">
              {run.items.map((item) => {
                const traceId = item.trace_id;
                return (
                  <button
                    className="quiet-button"
                    type="button"
                    onClick={() => onOpenTrace(traceId)}
                    title={`Open conversation · ${item.handling_mode}`}
                    key={traceId}
                  >
                    {traceId} · {item.handling_mode}
                  </button>
                );
              })}
            </div>
          </article>
        ))}
      </div>
      {evidence.outcome_by_handling_mode ? (
        <div>
          <h3>Authoritative outcome join</h3>
          <p>Source outcomes joined to the first completed run.</p>
          <div className="operational-list">
            {evidence.outcome_by_handling_mode.map((row) => (
              <article className="operational-row" key={row.handling_mode}>
                <div>
                  <span className="mono-label">{row.handling_mode}</span>
                  <p>
                    Denominator {row.denominator} · Success {row.success_count} ·
                    Failure {row.failure_count} · Mean reward {row.mean_reward.toFixed(4)}
                  </p>
                </div>
                <div className="row-evidence" aria-label="Trace evidence">
                  {row.trace_ids.map((traceId) => (
                    <button
                      className="quiet-button"
                      type="button"
                      onClick={() => onOpenTrace(traceId)}
                      key={traceId}
                    >
                      {traceId}
                    </button>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
