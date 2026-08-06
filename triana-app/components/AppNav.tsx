"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/results", label: "Overview" },
  { href: "/behavior", label: "User behavior" },
  { href: "/cases", label: "Cases" },
  { href: "/run", label: "Runs" },
  { href: "/review", label: "Review" },
];

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg
      className="app-control-icon"
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="square"
      aria-hidden="true"
    >
      {open ? (
        <path d="M5 5l10 10M15 5 5 15" />
      ) : (
        <path d="M4 5.5h12M4 10h12M4 14.5h12" />
      )}
    </svg>
  );
}
function SidebarIcon({ collapsed }: { collapsed: boolean }) {
  return (
    <svg
      className="app-control-icon"
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="square"
      strokeLinejoin="miter"
      aria-hidden="true"
    >
      <rect x="2.75" y="3" width="14.5" height="14" rx="1.5" />
      <path d="M7.5 3v14" />
      {collapsed ? <path d="M11 7l3 3-3 3" /> : <path d="M14 7l-3 3 3 3" />}
    </svg>
  );
}

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
          <button
            type="button"
            className="app-expand-button"
            onClick={onToggleCollapsed}
            aria-label="Expand navigation"
          >
            <SidebarIcon collapsed />
          </button>
          <strong>{section}</strong>
        </div>
        <small>Labs · Backend report · Read only</small>
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
        <MenuIcon open={open} />
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
            aria-label="Collapse navigation"
          >
            <SidebarIcon collapsed={false} />
          </button>
        </div>

        <div className="app-agent">
          <span className="app-nav-copy">
            <span className="mono-label">Report artifact</span>
            <strong>Configured backend</strong>
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
            >
              <span className="app-nav-copy">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="app-connections app-nav-copy">
          <div><span>Mode</span><strong>Read only</strong></div>
          <div><span>Source</span><strong>Backend report</strong></div>
          <div><span>Access</span><strong>Private tunnel</strong></div>
        </div>

        <Link href="/setup" className="app-switch-link app-nav-copy">
          Report source
        </Link>
      </aside>
    </>
  );
}
