import type { DecisionAttestation } from "../types/decision_attestation.js";
import type { NormalizedTrace } from "../types/normalized_trace.js";
import type { ProtectedCase } from "../types/protected_case.js";
import type { RecordChain } from "../types/record_chain.js";
import type { ReleaseEvidenceRecord } from "../types/release_evidence_record.js";

export type TrianaDocument =
  | DecisionAttestation
  | NormalizedTrace
  | ProtectedCase
  | RecordChain
  | ReleaseEvidenceRecord;

export function documentIdentity(document: TrianaDocument): string {
  switch (document.contract_kind) {
    case "decision_attestation":
      return document.attestation_hash;
    case "normalized_trace":
      return document.trace_hash;
    case "protected_case":
      return document.case_version;
    case "record_chain":
      return document.chain_hash;
    case "release_evidence_record":
      return document.current_record_hash ?? "unsigned";
  }
}
