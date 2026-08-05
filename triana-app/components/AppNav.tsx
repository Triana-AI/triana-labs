"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/results", label: "Overview", glyph: "O" },
  { href: "/behavior", label: "User behavior", glyph: "U" },
  { href: "/cases", label: "Cases", glyph: "C" },
  { href: "/run", label: "Runs", glyph: "R" },
  { href: "/review", label: "Review", glyph: "V" },
];

export function AppNav({
  collapsed,
  onToggleCollapsed,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const activeHref = pathname.startsWith("/conversations/") ? "/run" : pathname;
  const section = pathname === "/setup"
    ? "Report source"
    : pathname.startsWith("/conversations/")
      ? "Conversation"
      : NAV_ITEMS.find(({ href }) => href === activeHref)?.label ?? "Labs";

  return (
    <>
      <header className="app-product-header">
        <div>
          <img src="/brand/triana-lazo-favicon-master.svg" alt="" aria-hidden="true" />
          <strong>Triana</strong>
          <span>{section}</span>
        </div>
        <small>Labs · Read only</small>
      </header>
      <button
        type="button"
        className="app-menu-button"
        aria-expanded={open}
        aria-controls="primary-navigation"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="app-brand-mark" aria-hidden="true">
          <img src="/brand/triana-lazo-favicon-master.svg" alt="" />
        </span>
        <span>Triana Labs</span>
        <span aria-hidden="true">{open ? "×" : "≡"}</span>
      </button>

      <aside className={`app-sidebar${open ? " is-open" : ""}${collapsed ? " is-collapsed" : ""}`}>
        <div className="app-brand">
          <Link href="/results" className="app-brand-link" aria-label="Triana Labs">
            <span className="app-brand-mark" aria-hidden="true">
              <img src="/brand/triana-lazo-favicon-master.svg" alt="" />
            </span>
            <strong className="app-nav-copy">Triana Labs</strong>
          </Link>
          <button
            type="button"
            className="app-collapse-button"
            onClick={onToggleCollapsed}
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
            title={collapsed ? "Expand navigation" : "Collapse navigation"}
          >
            <span aria-hidden="true">{collapsed ? "›" : "‹"}</span>
          </button>
        </div>

        <div className="app-agent">
          <span className="app-agent-pulse" aria-hidden="true" />
          <span className="app-nav-copy">
            <span className="mono-label">Connected agent</span>
            <strong>Synthetic report</strong>
          </span>
        </div>

        <nav id="primary-navigation" className="app-nav" aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="app-nav-link"
              aria-current={activeHref === item.href ? "page" : undefined}
              onClick={() => setOpen(false)}
              title={collapsed ? item.label : undefined}
            >
              <span className="app-nav-glyph" aria-hidden="true">{item.glyph}</span>
              <span className="app-nav-copy">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="app-connections app-nav-copy">
          <div><span>Mode</span><strong>Read only</strong></div>
          <div><span>Privacy</span><strong>Synthetic</strong></div>
          <div><span>Custody</span><strong>Local</strong></div>
        </div>

        <Link href="/setup" className="app-switch-link app-nav-copy">
          Report source
        </Link>
      </aside>
    </>
  );
}
