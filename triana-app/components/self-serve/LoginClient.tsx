"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSessionToken, selfServeApi, setSessionToken } from "@/lib/self-serve/api";

export function LoginClient() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      setSessionToken(token.trim());
      await selfServeApi.me();
      router.push("/agents");
    } catch (value) {
      clearSessionToken();
      setError(value instanceof Error ? value.message : "Sign in failed.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-stage">
    <section className="login-panel">
      <span className="mono-label">Triana self-serve preview</span>
      <h1>Bring the traces.<br />See every conversation.</h1>
      <p>Create an agent, upload prescribed PreviewTrace JSONL, and inspect deterministic import accounting.</p>
      <form onSubmit={submit}>
        <label htmlFor="owner-token">Owner bearer token</label>
        <input id="owner-token" type="password" autoComplete="off" required value={token} onChange={(event) => setToken(event.target.value)} placeholder="Paste a development JWT" />
        <button className="primary-button" type="submit" disabled={busy || !token.trim()}>{busy ? "Checking…" : "Log in"}</button>
      </form>
      {error ? <div className="self-serve-notice is-error" role="alert"><strong>Sign in failed</strong><p>{error}</p></div> : null}
      <aside className="login-config-note">
        <strong>Hosted OIDC configuration required</strong>
        <p>This launch scaffold keeps the bearer token in this tab&apos;s session storage only. Configure the hosted OIDC redirect before public deployment.</p>
      </aside>
    </section>
  </main>;
}
