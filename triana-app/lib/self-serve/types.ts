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
