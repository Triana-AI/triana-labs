export type ConversationStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETE"
  | "PARTIAL"
  | "UNAVAILABLE"
  | "NOT_STARTED";

export type Ruling = "YES" | "NO" | "CANNOT_JUDGE" | "UNANSWERED";

export interface LabsCase {
  case_id: string;
  title: string;
  origin: "SEEN_IN_TRACES" | "GROUNDED_VARIATION";
  goal: string;
  done_condition: string;
  constraints: string[];
  source_basis: string;
  why_it_exists: string;
  behavior_group_ids: string[];
  source_evidence_ids: string[];
  simulated_user: {
    persona_id: string;
    persona_label: string;
    intent_id: string;
    intent_label: string;
    turn_policy_id: string;
    turn_policy_label: string;
    authority: "MODEL_PROPOSED_HUMAN_REVIEWABLE";
  };
  world_availability: {
    section_label: "Case data items";
    status: "READY" | "NEEDS_DATA" | "BLOCKED" | "NOT_CHECKED";
    items: Array<{
      item_id: string;
      label: string;
      item_kind: string;
      status: "AVAILABLE" | "MISSING" | "AMBIGUOUS" | "NOT_CHECKED" | "OUTSIDE_SCOPE";
      detail: string;
    }>;
  };
  selection: "SELECTED" | "EXCLUDED";
  selection_reason: string | null;
}

export interface Conversation {
  conversation_id: string;
  case_id: string;
  status: ConversationStatus;
  current_turn: number;
  turn_limit: number;
  latest: string;
  goal_state: "MET" | "NOT_MET" | "REVIEW_REQUIRED" | "UNKNOWN";
  termination_reason: string | null;
  turns: Array<{
    turn_id: string;
    ordinal: number;
    role: "USER" | "AGENT";
    content: string;
    evidence_ref_ids: string[];
  }>;
  tool_events: Array<{
    tool_event_id: string;
    after_turn_ordinal: number;
    tool_name: string;
    status: "SUCCEEDED" | "ERROR" | "UNKNOWN";
    detail: string;
  }>;
  gaps: Array<{
    gap_id: string;
    reason_code: string;
    label: string;
    detail: string;
    turn_ordinal: number | null;
    evidence_ref_ids: string[];
  }>;
  evidence_refs: Array<{
    evidence_ref_id: string;
    kind: "TRACE" | "CASE" | "TARGET_EVENT" | "SIMULATOR_TURN" | "TOOL_EVENT" | "LINEAGE";
    label: string;
  }>;
  accounting: {
    http_exchange_count: number;
    tool_call_count: number;
    actual_cost_usd: string | null;
  };
}

export interface Review {
  conversation_id: string;
  review_state: "RECORDED" | "UNREVIEWED";
  realism: Ruling;
  adaptation: Ruling;
  goal_completion: Ruling;
  scope_privacy_boundaries: Ruling;
  notes: string | null;
}

export interface LabsReport {
  artifact_kind: "labs_report";
  schema_version: 1;
  report_id: string;
  title: string;
  evidence_class: "SYNTHETIC_EXISTING_TRACE_CORPUS";
  mode: "GENERATED_MULTI_TURN_SIMULATION";
  privacy_class: string;
  sample_class: string;
  sample_disclosure: string;
  created_at: string;
  lineage: {
    report_contract: "LABS07_08_REPORT_V1";
    report_hash: string;
    source_sha256?: string;
    source_artifact_hashes: Array<{ artifact_kind: string; hash: string }>;
    compiler: { name: "triana-labs-report"; version: "1" };
  };
  setup: {
    source: { source_kind: string; display_name: string; authorization: string; custody: string };
    adapter: { adapter_id: string; adapter_version: string; mapping_status: "UNDERSTOOD" | "PARTIAL" | "NOT_UNDERSTOOD" };
    understanding: {
      physical_record_count: number;
      accepted_record_count: number;
      rejected_record_count: number;
      usable_conversation_count: number;
      source_status_counts: Record<string, number>;
      rejection_reasons: Array<{ reason_code: string; label: string; count: number }>;
      unassessed_semantics: string[];
    };
  };
  behavior: {
    derivation_kind: "STRUCTURAL_GROUPING";
    membership_authority: "DETERMINISTIC";
    semantic_summary_authority: "MODEL_PROPOSED";
    population_claim: "NOT_ESTABLISHED";
    groups: Array<{
      group_id: string;
      label: string;
      summary: string;
      support_count: number;
      share_basis_points: number;
      structural_pattern: string;
      fidelity_label: "STRUCTURALLY_OBSERVED_MODEL_SUMMARIZED";
      source_evidence_ids: string[];
    }>;
  };
  cases: LabsCase[];
  run: {
    run_id: string;
    recorded_state: "NOT_STARTED" | "RUNNING" | "COMPLETED" | "COMPLETED_WITH_GAPS";
    target: { target_id: string; label: string; connection_state: "READY" | "UNAVAILABLE" | "UNKNOWN" };
    simulator: { provider_label: string; model_label: string; identity_count: number };
    limits: {
      selected_case_count: number;
      max_turns_per_conversation: number;
      max_conversations: number;
      max_http_exchanges: number;
      max_minutes_per_conversation: number;
      reserved_cost_ceiling_usd: string;
      retry_policy: "NONE";
      repair_policy: "NONE";
      fallback_policy: "NONE";
    };
    privacy_egress: { provider: string; target: string; authorization: string };
    conversation_order: string[];
  };
  conversations: Conversation[];
  results: {
    learned: { headline: string; detail: string; group_count: number; usable_conversation_count: number };
    created: { headline: string; detail: string; selected_count: number; seen_count: number; variation_count: number; excluded_count: number };
    happened: {
      headline: string; detail: string; complete_count: number; partial_count: number;
      unavailable_count: number; running_count: number; queued_count: number;
      not_started_count: number; goal_met_count: number; goal_review_required_count: number;
    };
    judgment: { headline: string; detail: string; review_eligible_count: number; reviewed_count: number };
    accounting: {
      http_exchange_count: number; tool_call_count: number; actual_cost_usd: string | null;
      privacy_gap_count: number; retry_count: 0; repair_count: 0; fallback_count: 0;
    };
  };
  reviews: Review[];
  limitations: Array<{
    limitation_id: string;
    title: string;
    detail: string;
    status: "BACKLOG" | "NOT_EVALUATED" | "KNOWN_GAP";
    claim_blocked: string;
  }>;
}

export type LabsReportLoadResult =
  | { availability: "AVAILABLE"; report: LabsReport }
  | { availability: "UNAVAILABLE"; code: "BACKEND_REPORT_UNAVAILABLE"; report: null };

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireRecord(value: unknown, field: string): Record<string, unknown> {
  if (!isRecord(value)) throw new Error(`Invalid Labs report field: ${field}`);
  return value;
}

function requireArray(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`Invalid Labs report field: ${field}`);
  return value;
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) throw new Error(`Invalid Labs report field: ${field}`);
  return value;
}

function requireNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error(`Invalid Labs report field: ${field}`);
  }
  return value;
}

function requireStringArray(value: unknown, field: string): void {
  requireArray(value, field).forEach((item, index) => requireString(item, `${field}[${index}]`));
}

function requireNullableString(value: unknown, field: string): void {
  if (value !== null) requireString(value, field);
}

function requireFields(record: Record<string, unknown>, fields: string[], prefix: string): void {
  fields.forEach((field) => requireString(record[field], `${prefix}.${field}`));
}

function requireNumberFields(record: Record<string, unknown>, fields: string[], prefix: string): void {
  fields.forEach((field) => requireNumber(record[field], `${prefix}.${field}`));
}

function assertLoadedReport(value: unknown): asserts value is LabsReport {
  const report = requireRecord(value, "report");
  if (report.artifact_kind !== "labs_report" || report.schema_version !== 1) {
    throw new Error("Unsupported Labs report contract");
  }
  requireString(report.report_id, "report_id");
  requireString(report.title, "title");
  if (report.evidence_class !== "SYNTHETIC_EXISTING_TRACE_CORPUS") {
    throw new Error("Unsupported Labs report evidence class");
  }
  requireString(report.privacy_class, "privacy_class");
  requireString(report.sample_class, "sample_class");
  requireString(report.sample_disclosure, "sample_disclosure");

  const lineage = requireRecord(report.lineage, "lineage");
  requireString(lineage.report_contract, "lineage.report_contract");
  requireString(lineage.report_hash, "lineage.report_hash");
  requireArray(lineage.source_artifact_hashes, "lineage.source_artifact_hashes").forEach((item, index) => {
    requireFields(requireRecord(item, `lineage.source_artifact_hashes[${index}]`), ["artifact_kind", "hash"], `lineage.source_artifact_hashes[${index}]`);
  });
  requireFields(requireRecord(lineage.compiler, "lineage.compiler"), ["name", "version"], "lineage.compiler");

  const setup = requireRecord(report.setup, "setup");
  const source = requireRecord(setup.source, "setup.source");
  requireFields(source, ["source_kind", "display_name", "authorization", "custody"], "setup.source");
  const adapter = requireRecord(setup.adapter, "setup.adapter");
  requireFields(adapter, ["adapter_id", "adapter_version", "mapping_status"], "setup.adapter");
  const understanding = requireRecord(setup.understanding, "setup.understanding");
  requireNumberFields(understanding, ["physical_record_count", "accepted_record_count", "rejected_record_count", "usable_conversation_count"], "setup.understanding");
  const statusCounts = requireRecord(understanding.source_status_counts, "setup.understanding.source_status_counts");
  Object.entries(statusCounts).forEach(([status, count]) => {
    requireString(status, "setup.understanding.source_status_counts key");
    requireNumber(count, `setup.understanding.source_status_counts.${status}`);
  });
  requireArray(understanding.rejection_reasons, "setup.understanding.rejection_reasons").forEach((item, index) => {
    const reason = requireRecord(item, `setup.understanding.rejection_reasons[${index}]`);
    requireString(reason.reason_code, `rejection_reasons[${index}].reason_code`);
    requireString(reason.label, `rejection_reasons[${index}].label`);
    requireNumber(reason.count, `rejection_reasons[${index}].count`);
  });
  requireStringArray(understanding.unassessed_semantics, "setup.understanding.unassessed_semantics");

  const behavior = requireRecord(report.behavior, "behavior");
  requireFields(behavior, ["derivation_kind", "membership_authority", "semantic_summary_authority", "population_claim"], "behavior");
  requireArray(behavior.groups, "behavior.groups").forEach((item, index) => {
    const group = requireRecord(item, `behavior.groups[${index}]`);
    requireFields(group, ["group_id", "label", "summary", "structural_pattern", "fidelity_label"], `behavior.groups[${index}]`);
    requireNumberFields(group, ["support_count", "share_basis_points"], `behavior.groups[${index}]`);
    requireStringArray(group.source_evidence_ids, `behavior.groups[${index}].source_evidence_ids`);
  });

  requireArray(report.cases, "cases").forEach((item, index) => {
    const itemPath = `cases[${index}]`;
    const labsCase = requireRecord(item, itemPath);
    requireFields(labsCase, ["case_id", "title", "origin", "goal", "done_condition", "source_basis", "why_it_exists", "selection"], itemPath);
    requireStringArray(labsCase.constraints, `${itemPath}.constraints`);
    requireStringArray(labsCase.behavior_group_ids, `${itemPath}.behavior_group_ids`);
    requireStringArray(labsCase.source_evidence_ids, `${itemPath}.source_evidence_ids`);
    requireNullableString(labsCase.selection_reason, `${itemPath}.selection_reason`);
    requireFields(requireRecord(labsCase.simulated_user, `${itemPath}.simulated_user`), ["persona_id", "persona_label", "intent_id", "intent_label", "turn_policy_id", "turn_policy_label", "authority"], `${itemPath}.simulated_user`);
    const world = requireRecord(labsCase.world_availability, `${itemPath}.world_availability`);
    requireFields(world, ["section_label", "status"], `${itemPath}.world_availability`);
    requireArray(world.items, `${itemPath}.world_availability.items`).forEach((worldItem, worldIndex) =>
      requireFields(requireRecord(worldItem, `${itemPath}.world_availability.items[${worldIndex}]`), ["item_id", "label", "item_kind", "status", "detail"], `${itemPath}.world_availability.items[${worldIndex}]`),
    );
  });

  requireArray(report.conversations, "conversations").forEach((item, index) => {
    const itemPath = `conversations[${index}]`;
    const conversation = requireRecord(item, itemPath);
    requireFields(conversation, ["conversation_id", "case_id", "status", "latest", "goal_state"], itemPath);
    requireNumberFields(conversation, ["current_turn", "turn_limit"], itemPath);
    requireNullableString(conversation.termination_reason, `${itemPath}.termination_reason`);
    requireArray(conversation.turns, `${itemPath}.turns`).forEach((turn, turnIndex) => {
      const turnPath = `${itemPath}.turns[${turnIndex}]`;
      const turnRecord = requireRecord(turn, turnPath);
      requireFields(turnRecord, ["turn_id", "role", "content"], turnPath);
      requireNumber(turnRecord.ordinal, `${turnPath}.ordinal`);
      requireStringArray(turnRecord.evidence_ref_ids, `${turnPath}.evidence_ref_ids`);
    });
    requireArray(conversation.tool_events, `${itemPath}.tool_events`).forEach((event, eventIndex) => {
      const eventPath = `${itemPath}.tool_events[${eventIndex}]`;
      const eventRecord = requireRecord(event, eventPath);
      requireFields(eventRecord, ["tool_event_id", "tool_name", "status", "detail"], eventPath);
      requireNumber(eventRecord.after_turn_ordinal, `${eventPath}.after_turn_ordinal`);
    });
    requireArray(conversation.gaps, `${itemPath}.gaps`).forEach((gap, gapIndex) => {
      const gapPath = `${itemPath}.gaps[${gapIndex}]`;
      const gapRecord = requireRecord(gap, gapPath);
      requireFields(gapRecord, ["gap_id", "reason_code", "label", "detail"], gapPath);
      if (gapRecord.turn_ordinal !== null) requireNumber(gapRecord.turn_ordinal, `${gapPath}.turn_ordinal`);
      requireStringArray(gapRecord.evidence_ref_ids, `${gapPath}.evidence_ref_ids`);
    });
    requireArray(conversation.evidence_refs, `${itemPath}.evidence_refs`).forEach((ref, refIndex) =>
      requireFields(requireRecord(ref, `${itemPath}.evidence_refs[${refIndex}]`), ["evidence_ref_id", "kind", "label"], `${itemPath}.evidence_refs[${refIndex}]`),
    );
    const accounting = requireRecord(conversation.accounting, `${itemPath}.accounting`);
    requireNumberFields(accounting, ["http_exchange_count", "tool_call_count"], `${itemPath}.accounting`);
    requireNullableString(accounting.actual_cost_usd, `${itemPath}.accounting.actual_cost_usd`);
  });

  requireArray(report.reviews, "reviews").forEach((item, index) => {
    const review = requireRecord(item, `reviews[${index}]`);
    requireFields(review, ["conversation_id", "review_state", "realism", "adaptation", "goal_completion", "scope_privacy_boundaries"], `reviews[${index}]`);
    requireNullableString(review.notes, `reviews[${index}].notes`);
  });

  requireArray(report.limitations, "limitations").forEach((item, index) =>
    requireFields(requireRecord(item, `limitations[${index}]`), ["limitation_id", "title", "detail", "status", "claim_blocked"], `limitations[${index}]`),
  );
  const run = requireRecord(report.run, "run");
  requireFields(run, ["run_id", "recorded_state"], "run");
  requireFields(requireRecord(run.target, "run.target"), ["target_id", "label", "connection_state"], "run.target");
  const simulator = requireRecord(run.simulator, "run.simulator");
  requireFields(simulator, ["provider_label", "model_label"], "run.simulator");
  requireNumber(simulator.identity_count, "run.simulator.identity_count");
  const limits = requireRecord(run.limits, "run.limits");
  requireNumberFields(limits, ["selected_case_count", "max_turns_per_conversation", "max_conversations", "max_http_exchanges", "max_minutes_per_conversation"], "run.limits");
  requireFields(limits, ["reserved_cost_ceiling_usd", "retry_policy", "repair_policy", "fallback_policy"], "run.limits");
  requireFields(requireRecord(run.privacy_egress, "run.privacy_egress"), ["provider", "target", "authorization"], "run.privacy_egress");
  requireStringArray(run.conversation_order, "run.conversation_order");
  const results = requireRecord(report.results, "results");
  for (const field of ["learned", "created", "happened", "judgment"]) {
    requireFields(requireRecord(results[field], `results.${field}`), ["headline", "detail"], `results.${field}`);
  }
  const resultAccounting = requireRecord(results.accounting, "results.accounting");
  requireNumberFields(resultAccounting, ["http_exchange_count", "tool_call_count", "privacy_gap_count", "retry_count", "repair_count", "fallback_count"], "results.accounting");
  requireNullableString(resultAccounting.actual_cost_usd, "results.accounting.actual_cost_usd");
}

function reportUrl(apiOrigin: string, reportId: string): string {
  const origin = new URL(apiOrigin);
  if (origin.protocol !== "http:" && origin.protocol !== "https:") throw new Error("Unsupported backend origin");
  if (origin.username || origin.password || origin.search || origin.hash || !["", "/"].includes(origin.pathname)) {
    throw new Error("Backend origin must contain only scheme, host, and port");
  }
  const base = origin.toString().replace(/\/$/, "");
  return `${base}/api/v1/reports/${encodeURIComponent(reportId)}`;
}

export async function loadLabsReport({
  apiOrigin,
  reportId,
  fetchImpl = fetch,
}: {
  apiOrigin: string | undefined;
  reportId: string | undefined;
  fetchImpl?: FetchLike;
}): Promise<LabsReportLoadResult> {
  try {
    if (!apiOrigin || !reportId) throw new Error("Backend report configuration is missing");
    const response = await fetchImpl(reportUrl(apiOrigin, reportId), {
      headers: { accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`Backend report returned HTTP ${response.status}`);
    if (!(response.headers.get("content-type") ?? "").toLowerCase().includes("application/json")) {
      throw new Error("Backend report response is not JSON");
    }
    const report: unknown = await response.json();
    assertLoadedReport(report);
    if (report.report_id !== reportId) throw new Error("Backend report identity mismatch");
    return { availability: "AVAILABLE", report };
  } catch {
    return { availability: "UNAVAILABLE", code: "BACKEND_REPORT_UNAVAILABLE", report: null };
  }
}

export function loadConfiguredLabsReport(): Promise<LabsReportLoadResult> {
  return loadLabsReport({
    apiOrigin: process.env.TRIANA_BACKEND_API_ORIGIN,
    reportId: process.env.TRIANA_LABS_REPORT_ID,
  });
}

export function getCase(report: LabsReport, caseId: string): LabsCase {
  const item = report.cases.find(({ case_id }) => case_id === caseId);
  if (!item) throw new Error(`Broken report case reference: ${caseId}`);
  return item;
}

export function getReview(report: LabsReport, conversationId: string): Review {
  const item = report.reviews.find((review) => review.conversation_id === conversationId);
  if (!item) throw new Error(`Broken report review reference: ${conversationId}`);
  return item;
}

export function displayRuling(value: Ruling): string {
  return ({ YES: "Yes", NO: "No", CANNOT_JUDGE: "Cannot judge", UNANSWERED: "Unanswered" })[value];
}
