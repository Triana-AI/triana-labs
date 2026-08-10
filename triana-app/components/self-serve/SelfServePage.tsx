import type { ReactNode } from "react";
import Link from "next/link";

export function SelfServePage({ eyebrow, title, description, actions, children }: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return <div className="self-serve-page">
    <header className="self-serve-header">
      <div><span className="mono-label">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
      {actions ? <div className="self-serve-actions">{actions}</div> : null}
    </header>
    {children}
  </div>;
}

export function Breadcrumbs({ items }: { items: Array<{ label: string; href?: string }> }) {
  return <nav className="breadcrumbs" aria-label="Breadcrumb">
    {items.map((item, index) => <span key={`${item.label}-${index}`}>
      {item.href ? <Link href={item.href}>{item.label}</Link> : item.label}
      {index < items.length - 1 ? <i aria-hidden="true">/</i> : null}
    </span>)}
  </nav>;
}

export function ErrorNotice({ message }: { message: string }) {
  return <div className="self-serve-notice is-error" role="alert"><strong>Unavailable</strong><p>{message}</p></div>;
}

export function LoadingNotice({ label = "Loading…" }: { label?: string }) {
  return <div className="self-serve-notice" role="status"><span className="live-dot" /><p>{label}</p></div>;
}
