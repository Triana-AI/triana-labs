"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSessionToken, selfServeApi } from "@/lib/self-serve/api";
import type { AgentSummary } from "@/lib/self-serve/types";
import { ErrorNotice, LoadingNotice, SelfServePage } from "@/components/self-serve/SelfServePage";

export function AgentsClient() {
  const router = useRouter();
  const [agents, setAgents] = useState<AgentSummary[] | null>(null);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { selfServeApi.listAgents().then(setAgents).catch((value: Error) => setError(value.message)); }, []);

  async function createAgent(event: FormEvent) {
    event.preventDefault();
    setCreating(true); setError(null);
    try {
      const agent = await selfServeApi.createAgent(name.trim());
      router.push(`/agents/${agent.agent_id}`);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Agent creation failed.");
    } finally { setCreating(false); }
  }

  return <SelfServePage eyebrow="Workspace" title="Your agents" description="Each agent has its own immutable trace-import history."
    actions={<button className="quiet-button" type="button" onClick={() => { clearSessionToken(); router.push("/login"); }}>Log out</button>}>
    <section className="self-serve-grid">
      <div className="self-serve-card create-agent-card">
        <span className="mono-label">One by one</span><h2>Add agent</h2>
        <form onSubmit={createAgent}><label htmlFor="agent-name">Display name</label><input id="agent-name" required maxLength={120} value={name} onChange={(event) => setName(event.target.value)} placeholder="Support agent" /><button className="primary-button" disabled={creating || !name.trim()}>{creating ? "Creating…" : "Create agent"}</button></form>
      </div>
      <div className="self-serve-card agent-list-card">
        <div className="card-heading"><h2>Agents</h2><span>{agents?.length ?? "—"}</span></div>
        {error ? <ErrorNotice message={error} /> : agents === null ? <LoadingNotice /> : agents.length === 0 ? <div className="self-serve-empty"><strong>No agents yet</strong><p>Create the first one to unlock trace upload.</p></div> : <ul className="agent-list">{agents.map((agent) => <li key={agent.agent_id}><Link href={`/agents/${agent.agent_id}`}><span><strong>{agent.display_name}</strong><small>{agent.agent_id}</small></span><b aria-hidden="true">→</b></Link></li>)}</ul>}
      </div>
    </section>
  </SelfServePage>;
}
