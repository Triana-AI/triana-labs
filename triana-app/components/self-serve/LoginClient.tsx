"use client";

import { FormEvent, useState } from "react";
import { createBrowserSupabaseClient } from "@/lib/supabase/browser";
import { getSupabaseConfigurationError } from "@/lib/supabase/config";

export function LoginClient({ confirmationFailed = false }: { confirmationFailed?: boolean }) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const configurationError = getSupabaseConfigurationError();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const supabase = createBrowserSupabaseClient();
      const { error: authError } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: {
          shouldCreateUser: true,
          emailRedirectTo: `${window.location.origin}/auth/confirm`,
        },
      });
      if (authError) throw authError;
      setSent(true);
    } catch {
      setError("We could not send a sign-in link. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-stage">
    <section className="login-panel">
      <span className="mono-label">Triana self-serve preview</span>
      <h1>Bring the traces.<br />See every conversation.</h1>
      <p>Create an agent, upload prescribed PreviewTrace JSONL, and inspect deterministic import accounting.</p>
      {sent ? <div className="self-serve-notice" role="status"><strong>Check your email</strong><p>If the address can receive mail, a sign-in link is on its way.</p></div> : <form onSubmit={submit}>
        <label htmlFor="owner-email">Email</label>
        <input id="owner-email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" />
        <button className="primary-button" type="submit" disabled={busy || !email.trim() || Boolean(configurationError)}>{busy ? "Sending…" : "Email me a magic link"}</button>
      </form>}
      {confirmationFailed ? <div className="self-serve-notice is-error" role="alert"><strong>Link unavailable</strong><p>This sign-in link is invalid or expired. Request a new one.</p></div> : null}
      {configurationError ? <div className="self-serve-notice is-error" role="alert"><strong>Authentication unavailable</strong><p>{configurationError}</p></div> : null}
      {error ? <div className="self-serve-notice is-error" role="alert"><strong>Email unavailable</strong><p>{error}</p></div> : null}
    </section>
  </main>;
}
