import type { ReactNode } from "react";
import Link from "next/link";

export function LabsPage({
  surface,
  eyebrow,
  title,
  summary,
  meta,
  children,
}: {
  surface: "overview" | "source" | "behavior" | "cases" | "runs" | "review" | "conversation";
  eyebrow: string;
  title: string;
  summary: string;
  meta?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="labs-page" data-surface={surface}>
      <header className="labs-header">
        <div className="labs-header-main">
          <h1>{title}</h1>
          <p className="labs-lede">{summary}</p>
        </div>
        <div className="labs-header-side">
          <span className="labs-surface-label">{eyebrow}</span>
          {meta ? <div className="labs-header-meta">{meta}</div> : null}
        </div>
      </header>
      {children}
    </div>
  );
}

export function Section({
  title,
  description,
  children,
  className = "",
  tone = "dark",
}: {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  tone?: "light" | "dark" | "raised";
}) {
  return (
    <section className={`labs-section is-${tone} ${className}`.trim()}>
      <header className="labs-section-heading">
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </header>
      {children}
    </section>
  );
}

export function Status({ value }: { value: string }) {
  const tone = ["COMPLETE", "COMPLETED", "READY", "AVAILABLE", "RECORDED", "MET", "UNDERSTOOD", "SELECTED", "SUCCEEDED"].includes(value)
    ? "positive"
    : ["PARTIAL", "UNKNOWN", "NOT_CHECKED", "UNREVIEWED", "REVIEW_REQUIRED", "AMBIGUOUS", "NEEDS_DATA", "RUNNING", "QUEUED", "BACKLOG", "NOT_EVALUATED", "KNOWN_GAP"].includes(value)
      ? "warning"
      : ["UNAVAILABLE", "NOT_STARTED", "MISSING", "OUTSIDE_SCOPE", "ERROR", "NOT_UNDERSTOOD", "EXCLUDED"].includes(value)
        ? "negative"
        : "neutral";
  return <span className="labs-status" data-tone={tone}>{value}</span>;
}

export function Fact({ label, children }: { label: string; children: ReactNode }) {
  return <div className="labs-fact"><dt>{label}</dt><dd>{children}</dd></div>;
}

export function RouteLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link className="labs-link" href={href}>{children}<span aria-hidden="true">→</span></Link>;
}

export function Unavailable() {
  return <span className="labs-unavailable">Unavailable</span>;
}

export function BackendReportUnavailable() {
  return (
    <LabsPage
      surface="source"
      eyebrow="Backend report"
      title="Report unavailable"
      summary="Triana could not load the configured report from the backend. No fixture or simulated replacement is being shown."
      meta={<Status value="UNAVAILABLE" />}
    >
      <Section title="What this means" description="The report remains unavailable until the configured backend can serve the requested report identity.">
        <div className="limitation-callout">
          <Status value="UNAVAILABLE" />
          <div>
            <h3>Backend report unavailable</h3>
            <p>Check the private tunnel, backend service, and configured report ID.</p>
            <code>BACKEND_REPORT_UNAVAILABLE</code>
          </div>
        </div>
      </Section>
    </LabsPage>
  );
}
