"use client";

import Link from "next/link";
import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { selfServeApi } from "@/lib/self-serve/api";
import type { AgentSummary, ImportSummary } from "@/lib/self-serve/types";
import { Breadcrumbs, ErrorNotice, LoadingNotice, SelfServePage } from "@/components/self-serve/SelfServePage";

export function AgentDetailClient({ agentId }: { agentId: string }) {
  const router = useRouter();
  const [agent, setAgent] = useState<AgentSummary | null>(null);
  const [imports, setImports] = useState<ImportSummary[] | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [attested, setAttested] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([selfServeApi.getAgent(agentId), selfServeApi.listImports(agentId)])
      .then(([nextAgent, nextImports]) => { setAgent(nextAgent); setImports(nextImports); })
      .catch((value: Error) => setError(value.message));
  }, [agentId]);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    setError(null);
    const selected = event.target.files?.[0] ?? null;
    if (selected && !selected.name.toLowerCase().endsWith(".jsonl")) { setFile(null); setError("Choose a .jsonl file."); return; }
    setFile(selected);
  }

  async function upload() {
    if (!file || !attested) return;
    setBusy(true); setError(null);
    try {
      const result = await selfServeApi.uploadImport(agentId, file);
      router.push(`/agents/${agentId}/imports/${result.import_id}`);
    } catch (value) { setError(value instanceof Error ? value.message : "Upload failed."); }
    finally { setBusy(false); }
  }

  return <SelfServePage eyebrow="Agent" title={agent?.display_name ?? "Agent"} description="Upload prescribed traces and inspect every accepted conversation.">
    <Breadcrumbs items={[{ label: "Agents", href: "/agents" }, { label: agent?.display_name ?? agentId }]} />
    {error ? <ErrorNotice message={error} /> : null}
    <section className="self-serve-grid">
      <div className="self-serve-card upload-card">
        <span className="mono-label">Trace source</span><h2>Upload PreviewTrace JSONL</h2>
        <p>One conversation per physical line. Maximum 16 MiB, 1,000 lines, and 1 MiB per line.</p>
        <label className="file-picker"><input type="file" accept=".jsonl,application/x-ndjson" onChange={selectFile} /><span>{file ? file.name : "Choose .jsonl file"}</span></label>
        <label className="attestation"><input type="checkbox" checked={attested} onChange={(event) => setAttested(event.target.checked)} /><span>I own or am authorized to upload this trace data. It will remain private and will not be sent to an LLM.</span></label>
        <button className="primary-button" type="button" disabled={!file || !attested || busy} onClick={upload}>{busy ? "Uploading and validating…" : "Upload traces"}</button>
      </div>
      <div className="self-serve-card import-list-card">
        <div className="card-heading"><h2>Import history</h2><span>{imports?.length ?? "—"}</span></div>
        {imports === null && !error ? <LoadingNotice /> : imports?.length === 0 ? <div className="self-serve-empty"><strong>No imports</strong><p>Your validated uploads will appear here.</p></div> : <ul className="import-list">{imports?.map((item) => <li key={item.import_id}><Link href={`/agents/${agentId}/imports/${item.import_id}`}><span><strong>{item.status}</strong><small>{item.import_id}</small></span><span className="import-counts"><b>{item.accepted_conversation_count ?? item.accepted_record_count ?? 0}</b> accepted · <b>{item.rejected_record_count}</b> rejected</span></Link></li>)}</ul>}
      </div>
    </section>
  </SelfServePage>;
}
