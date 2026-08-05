import reportDocument from "@/data/labs-report.json";

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
  mode: "GENERATED_MULTI_TURN_SIMULATION";
  privacy_class: "SYNTHETIC";
  sample_class: "PUBLIC_SYNTHETIC_REFERENCE";
  sample_disclosure: string;
  created_at: string;
  lineage: {
    report_contract: "LABS07_08_REPORT_V1";
    report_hash: string;
    source_artifact_hashes: Array<{ artifact_kind: string; hash: string }>;
    compiler: { name: "triana-labs-report"; version: "1" };
  };
  setup: {
    source: { source_kind: "LOCAL_FILE"; display_name: string; authorization: "AUTHORIZED_SYNTHETIC"; custody: "LOCAL" };
    adapter: { adapter_id: string; adapter_version: string; mapping_status: "UNDERSTOOD" | "PARTIAL" | "NOT_UNDERSTOOD" };
    understanding: {
      physical_record_count: number;
      accepted_record_count: number;
      rejected_record_count: number;
      usable_conversation_count: number;
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
    privacy_egress: { provider: string; target: string; authorization: "SYNTHETIC_APPROVED" };
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

function assertLoadedReport(value: unknown): asserts value is LabsReport {
  if (!value || typeof value !== "object") throw new Error("Labs report is unavailable");
  const report = value as Record<string, unknown>;
  if (report.artifact_kind !== "labs_report" || report.schema_version !== 1) {
    throw new Error("Unsupported Labs report contract");
  }
}

assertLoadedReport(reportDocument);

export const labsReport: LabsReport = reportDocument;

export function getCase(caseId: string): LabsCase {
  const item = labsReport.cases.find(({ case_id }) => case_id === caseId);
  if (!item) throw new Error(`Broken report case reference: ${caseId}`);
  return item;
}

export function getConversation(conversationId: string): Conversation {
  const item = labsReport.conversations.find(({ conversation_id }) => conversation_id === conversationId);
  if (!item) throw new Error(`Unknown report conversation: ${conversationId}`);
  return item;
}

export function getReview(conversationId: string): Review {
  const item = labsReport.reviews.find((review) => review.conversation_id === conversationId);
  if (!item) throw new Error(`Broken report review reference: ${conversationId}`);
  return item;
}

export function displayRuling(value: Ruling): string {
  return ({ YES: "Yes", NO: "No", CANNOT_JUDGE: "Cannot judge", UNANSWERED: "Unanswered" })[value];
}
