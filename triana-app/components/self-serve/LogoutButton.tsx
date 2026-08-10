"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserSupabaseClient } from "@/lib/supabase/browser";

export function LogoutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function logout() {
    setBusy(true);
    setFailed(false);
    try {
      const supabase = createBrowserSupabaseClient();
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      router.replace("/login");
      router.refresh();
    } catch {
      setFailed(true);
      setBusy(false);
    }
  }

  return <button className="quiet-button" type="button" onClick={logout} disabled={busy}>{failed ? "Logout unavailable" : busy ? "Logging out…" : "Log out"}</button>;
}
