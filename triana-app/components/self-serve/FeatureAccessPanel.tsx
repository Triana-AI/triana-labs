"use client";

import { useEffect, useState } from "react";
import { selfServeApi } from "@/lib/self-serve/api";
import type { FeatureAccess, FeatureKey } from "@/lib/self-serve/types";
import { ErrorNotice, LoadingNotice } from "@/components/self-serve/SelfServePage";

const LABELS: Record<FeatureKey, string> = {
  TRACE_INGESTION: "Trace ingestion",
  CONVERSATION_VIEWER: "Conversation viewer",
  ANALYSIS: "Analysis",
  SIMULATION: "Simulation",
  TEAM_COLLABORATION: "Team collaboration",
  API_ACCESS: "API access",
};

export function FeatureAccessPanel() {
  const [features, setFeatures] = useState<FeatureAccess[] | null>(null);
  const [requesting, setRequesting] = useState<FeatureKey | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    selfServeApi.listFeatures().then(setFeatures).catch((value: Error) => setError(value.message));
  }, []);

  async function requestAccess(featureKey: FeatureKey) {
    setRequesting(featureKey);
    setError(null);
    try {
      const updated = await selfServeApi.requestFeatureAccess(featureKey);
      setFeatures((current) => current?.map((feature) => feature.feature_key === featureKey ? updated : feature) ?? [updated]);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Access request failed.");
    } finally {
      setRequesting(null);
    }
  }

  return <section className="self-serve-card" aria-labelledby="feature-access-title">
    <span className="mono-label">Gradual rollout</span>
    <div className="card-heading"><h2 id="feature-access-title">Feature access</h2><span>Backend owned</span></div>
    <p>Core trace ingestion and conversation viewing stay available. Requesting a staged feature does not grant it automatically.</p>
    {error ? <ErrorNotice message={error} /> : features === null ? <LoadingNotice label="Loading feature access…" /> : <ul className="agent-list">{features.map((feature) => <li key={feature.feature_key}>
      <div className="feature-access-row">
        <span><strong>{LABELS[feature.feature_key] ?? feature.feature_key}</strong><small>{feature.feature_key}</small></span>
        <span className="labs-status" data-tone={feature.state === "AVAILABLE" ? "positive" : feature.state === "REQUESTED" ? "warning" : "neutral"}>{feature.state}</span>
        {feature.state === "LOCKED" ? <button className="quiet-button" type="button" disabled={requesting === feature.feature_key} onClick={() => requestAccess(feature.feature_key)}>{requesting === feature.feature_key ? "Requesting…" : "Request access"}</button> : null}
      </div>
    </li>)}</ul>}
  </section>;
}
