"use client";

import { useState } from "react";
import { AppNav } from "@/components/AppNav";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [navCollapsed, setNavCollapsed] = useState(true);

  return (
    <div
      className={[
        "app-shell",
        navCollapsed ? "is-nav-collapsed" : "",
      ].filter(Boolean).join(" ")}
    >
      <AppNav
        collapsed={navCollapsed}
        onToggleCollapsed={() => setNavCollapsed((value) => !value)}
      />
      <main className="app-content">{children}</main>
    </div>
  );
}
