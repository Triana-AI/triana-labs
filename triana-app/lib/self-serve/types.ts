import type { PartialHandlingEvidence } from "@/components/analysis/PartialHandlingEvidence";

export type ImportStatus =
  | "PENDING"
  | "VALIDATING"
  | "COMPLETED"
  | "COMPLETED_WITH_REJECTIONS"
  | "FAILED";

export interface Owner {
  owner_id?: string;
  owner_subject?: string;
  email?: string;
  workspace_id?: string;
  workspace?: { workspace_id: string };
}

export interface AgentSummary {
  agent_id: string;
  display_name: string;
  default_version_id?: string;
  created_at?: string;
}

export interface ImportSummary {
  import_id: string;
  agent_id: string;
  status: ImportStatus;
  physical_record_count: number;
  accepted_record_count?: number;
  accepted_conversation_count?: number;
  rejected_record_count: number;
  source_sha256?: string;
  created_at?: string;
  analysis?: {
    feature_state: FeatureState;
    run: AnalysisRunSummary | null;
  };
}

export interface AnalysisRunSummary {
  workspace_id: string;
  agent_id: string;
  import_id: string;
  run_id: string;
  report_id: string | null;
  state: "QUEUED" | "RUNNING" | "COMPLETED" | "COMPLETED_WITH_GAPS" | "FAILED";
  judgment_state: "NOT_AVAILABLE" | "JUDGMENT_REQUIRED" | "JUDGMENT_COMPLETE";
  created_at?: string;
}

export interface TraceToEvalReviewItem {
  item_id: string;
  item_hash: string;
  item_kind: "POPULATION_PAIR" | "EVAL_PROPOSAL";
  allowed_decisions: string[];
  trace_ids?: string[];
  evidence_trace_ids?: string[];
  name?: string;
  criterion?: string;
}

export interface TraceToEvalReviewState {
  report_id: string;
  judgment_state: "NOT_AVAILABLE" | "JUDGMENT_REQUIRED" | "JUDGMENT_COMPLETE";
  review_queue: { items: TraceToEvalReviewItem[] };
  current_rulings: Array<{
    item_id: string;
    ruling_id: string;
    decision: string;
    edited_text?: string | null;
  }>;
}

export interface TraceToEvalReport {
  report_id: string;
  run_id: string;
  agent_id: string;
  import_id: string;
  accounting: {
    physical_record_count: number;
    accepted_conversation_count: number;
    rejected_record_count: number;
  };
  behavior_analytics: {
    conversation_count: number;
    tool_observed_conversation_count: number;
    event_kind_counts: Record<string, number>;
    turn_count: { minimum: number; maximum: number; total: number };
  };
  populations: Array<{
    population_id: string;
    label: string;
    description: string;
    support: number;
    evidence_trace_ids: string[];
    proposal_state: string;
  }>;
  eval_proposals: Array<{
    proposal_id: string;
    name: string;
    criterion: string;
    evidence_trace_ids: string[];
    proposal_state: string;
  }>;
  qualified_eval_inventory: Array<Record<string, unknown>>;
  gaps: Array<{ code: string; capability: string; state: string }>;
  stability: { state: string; semantic_run_count: number; disagreements: unknown[] };
  method: Record<string, unknown>;
  outcome_analytics?: Record<string, unknown>;
  partial_handling_evidence?: PartialHandlingEvidence;
  judgment: {
    state: string;
    required_review_item_count: number;
    verdict: "NOT_ESTABLISHED";
  };
}

export interface ConversationSummary {
  conversation_id: string;
  record_id?: string;
  line_number?: number;
  status?: string;
}

export interface RejectionSummary {
  line_number: number;
  reason_code: string;
  message?: string;
}

export type FeatureKey =
  | "TRACE_INGESTION"
  | "CONVERSATION_VIEWER"
  | "ANALYSIS"
  | "SIMULATION"
  | "TEAM_COLLABORATION"
  | "API_ACCESS";

export type FeatureState = "AVAILABLE" | "LOCKED" | "REQUESTED";

export interface FeatureAccess {
  feature_key: FeatureKey;
  state: FeatureState;
}
