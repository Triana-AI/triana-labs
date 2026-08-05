#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const HASH = /^sha256:[0-9a-f]{64}$/;
const DECIMAL = /^(0|[1-9][0-9]*)(\.[0-9]+)?$/;
const FORBIDDEN_KEYS = new Set([
  "pass", "block", "verdict", "recommendation", "regression",
  "release_memory", "baseline", "candidate", "upload", "auth",
  "credential", "billing",
]);

const fail = (path, message) => { throw new Error(`${path}: ${message}`); };
const object = (value, path) => {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(path, "expected object");
  return value;
};
const array = (value, path) => {
  if (!Array.isArray(value)) fail(path, "expected array");
  return value;
};
const exact = (value, keys, path) => {
  object(value, path);
  const expected = new Set(keys);
  for (const key of Object.keys(value)) {
    if (FORBIDDEN_KEYS.has(key)) fail(`${path}.${key}`, "forbidden field");
    if (!expected.has(key)) fail(`${path}.${key}`, "unknown field");
  }
  for (const key of keys) if (!(key in value)) fail(`${path}.${key}`, "missing field");
};
const text = (value, path, { nullable = false } = {}) => {
  if (nullable && value === null) return;
  if (typeof value !== "string" || value.trim() === "") fail(path, "expected nonempty string");
};
const safeId = (value, path) => {
  text(value, path);
  if (!SAFE_ID.test(value)) fail(path, "expected SafeId");
};
const integer = (value, path, minimum = 0) => {
  if (!Number.isInteger(value) || value < minimum) fail(path, `expected integer >= ${minimum}`);
};
const variant = (value, allowed, path) => {
  if (!allowed.includes(value)) fail(path, `expected one of ${allowed.join(", ")}`);
};
const decimal = (value, path, nullable = false) => {
  if (nullable && value === null) return;
  if (typeof value !== "string" || !DECIMAL.test(value)) fail(path, "expected unsigned decimal string");
};
const unique = (values, path) => {
  if (new Set(values).size !== values.length) fail(path, "duplicate identity");
};
const ids = (value, path, { nonempty = false } = {}) => {
  array(value, path);
  if (nonempty && value.length === 0) fail(path, "expected nonempty array");
  value.forEach((item, index) => safeId(item, `${path}[${index}]`));
  unique(value, path);
};
const countBy = (items, field, expected) => items.filter((item) => item[field] === expected).length;

function scanForbiddenFields(value, path = "$") {
  if (Array.isArray(value)) return value.forEach((item, index) => scanForbiddenFields(item, `${path}[${index}]`));
  if (!value || typeof value !== "object") return;
  for (const [key, child] of Object.entries(value)) {
    if (FORBIDDEN_KEYS.has(key)) fail(`${path}.${key}`, "forbidden field");
    scanForbiddenFields(child, `${path}.${key}`);
  }
}

function validateLineage(value, path) {
  exact(value, ["report_contract", "report_hash", "source_artifact_hashes", "compiler"], path);
  variant(value.report_contract, ["LABS07_08_REPORT_V1"], `${path}.report_contract`);
  if (typeof value.report_hash !== "string" || !HASH.test(value.report_hash)) fail(`${path}.report_hash`, "invalid sha256 hash");
  array(value.source_artifact_hashes, `${path}.source_artifact_hashes`).forEach((item, index) => {
    const itemPath = `${path}.source_artifact_hashes[${index}]`;
    exact(item, ["artifact_kind", "hash"], itemPath);
    text(item.artifact_kind, `${itemPath}.artifact_kind`);
    if (typeof item.hash !== "string" || !HASH.test(item.hash)) fail(`${itemPath}.hash`, "invalid sha256 hash");
  });
  exact(value.compiler, ["name", "version"], `${path}.compiler`);
  variant(value.compiler.name, ["triana-labs-report"], `${path}.compiler.name`);
  variant(value.compiler.version, ["1"], `${path}.compiler.version`);
}

function validateSetup(value, path) {
  exact(value, ["source", "adapter", "understanding"], path);
  exact(value.source, ["source_kind", "display_name", "authorization", "custody"], `${path}.source`);
  variant(value.source.source_kind, ["LOCAL_FILE"], `${path}.source.source_kind`);
  text(value.source.display_name, `${path}.source.display_name`);
  if (/[\\/]/.test(value.source.display_name)) fail(`${path}.source.display_name`, "expected safe basename");
  variant(value.source.authorization, ["AUTHORIZED_SYNTHETIC"], `${path}.source.authorization`);
  variant(value.source.custody, ["LOCAL"], `${path}.source.custody`);
  exact(value.adapter, ["adapter_id", "adapter_version", "mapping_status"], `${path}.adapter`);
  safeId(value.adapter.adapter_id, `${path}.adapter.adapter_id`);
  text(value.adapter.adapter_version, `${path}.adapter.adapter_version`);
  variant(value.adapter.mapping_status, ["UNDERSTOOD", "PARTIAL", "NOT_UNDERSTOOD"], `${path}.adapter.mapping_status`);
  const understandingPath = `${path}.understanding`;
  exact(value.understanding, ["physical_record_count", "accepted_record_count", "rejected_record_count", "usable_conversation_count", "rejection_reasons", "unassessed_semantics"], understandingPath);
  for (const key of ["physical_record_count", "accepted_record_count", "rejected_record_count", "usable_conversation_count"]) integer(value.understanding[key], `${understandingPath}.${key}`);
  if (value.understanding.accepted_record_count + value.understanding.rejected_record_count !== value.understanding.physical_record_count) fail(understandingPath, "accepted + rejected must equal physical records");
  const reasons = array(value.understanding.rejection_reasons, `${understandingPath}.rejection_reasons`);
  reasons.forEach((reason, index) => {
    const reasonPath = `${understandingPath}.rejection_reasons[${index}]`;
    exact(reason, ["reason_code", "label", "count"], reasonPath);
    safeId(reason.reason_code, `${reasonPath}.reason_code`);
    text(reason.label, `${reasonPath}.label`);
    integer(reason.count, `${reasonPath}.count`, 1);
  });
  unique(reasons.map(({ reason_code }) => reason_code), `${understandingPath}.rejection_reasons.reason_code`);
  if (reasons.reduce((sum, reason) => sum + reason.count, 0) !== value.understanding.rejected_record_count) fail(`${understandingPath}.rejection_reasons`, "counts must equal rejected_record_count");
  array(value.understanding.unassessed_semantics, `${understandingPath}.unassessed_semantics`).forEach((item, index) => text(item, `${understandingPath}.unassessed_semantics[${index}]`));
}

function validateBehavior(value, path) {
  exact(value, ["derivation_kind", "membership_authority", "semantic_summary_authority", "population_claim", "groups"], path);
  variant(value.derivation_kind, ["STRUCTURAL_GROUPING"], `${path}.derivation_kind`);
  variant(value.membership_authority, ["DETERMINISTIC"], `${path}.membership_authority`);
  variant(value.semantic_summary_authority, ["MODEL_PROPOSED"], `${path}.semantic_summary_authority`);
  variant(value.population_claim, ["NOT_ESTABLISHED"], `${path}.population_claim`);
  const groups = array(value.groups, `${path}.groups`);
  groups.forEach((group, index) => {
    const groupPath = `${path}.groups[${index}]`;
    exact(group, ["group_id", "label", "summary", "support_count", "share_basis_points", "structural_pattern", "fidelity_label", "source_evidence_ids"], groupPath);
    safeId(group.group_id, `${groupPath}.group_id`);
    for (const key of ["label", "summary", "structural_pattern"]) text(group[key], `${groupPath}.${key}`);
    integer(group.support_count, `${groupPath}.support_count`, 1);
    integer(group.share_basis_points, `${groupPath}.share_basis_points`);
    if (group.share_basis_points > 10000) fail(`${groupPath}.share_basis_points`, "must be <= 10000");
    variant(group.fidelity_label, ["STRUCTURALLY_OBSERVED_MODEL_SUMMARIZED"], `${groupPath}.fidelity_label`);
    ids(group.source_evidence_ids, `${groupPath}.source_evidence_ids`, { nonempty: true });
  });
  unique(groups.map(({ group_id }) => group_id), `${path}.groups.group_id`);
}

function validateCases(cases, behaviorGroupIds) {
  array(cases, "$.cases").forEach((item, index) => {
    const path = `$.cases[${index}]`;
    exact(item, ["case_id", "title", "origin", "goal", "done_condition", "constraints", "source_basis", "why_it_exists", "behavior_group_ids", "source_evidence_ids", "simulated_user", "world_availability", "selection", "selection_reason"], path);
    safeId(item.case_id, `${path}.case_id`);
    for (const key of ["title", "goal", "done_condition", "source_basis", "why_it_exists"]) text(item[key], `${path}.${key}`);
    variant(item.origin, ["SEEN_IN_TRACES", "GROUNDED_VARIATION"], `${path}.origin`);
    const constraints = array(item.constraints, `${path}.constraints`);
    if (!constraints.length) fail(`${path}.constraints`, "expected nonempty array");
    constraints.forEach((constraint, cIndex) => text(constraint, `${path}.constraints[${cIndex}]`));
    ids(item.behavior_group_ids, `${path}.behavior_group_ids`, { nonempty: true });
    item.behavior_group_ids.forEach((id) => { if (!behaviorGroupIds.has(id)) fail(`${path}.behavior_group_ids`, `broken reference ${id}`); });
    ids(item.source_evidence_ids, `${path}.source_evidence_ids`, { nonempty: true });
    exact(item.simulated_user, ["persona_id", "persona_label", "intent_id", "intent_label", "turn_policy_id", "turn_policy_label", "authority"], `${path}.simulated_user`);
    for (const key of ["persona_id", "intent_id", "turn_policy_id"]) safeId(item.simulated_user[key], `${path}.simulated_user.${key}`);
    for (const key of ["persona_label", "intent_label", "turn_policy_label"]) text(item.simulated_user[key], `${path}.simulated_user.${key}`);
    variant(item.simulated_user.authority, ["MODEL_PROPOSED_HUMAN_REVIEWABLE"], `${path}.simulated_user.authority`);
    exact(item.world_availability, ["section_label", "status", "items"], `${path}.world_availability`);
    variant(item.world_availability.section_label, ["Case data items"], `${path}.world_availability.section_label`);
    variant(item.world_availability.status, ["READY", "NEEDS_DATA", "BLOCKED", "NOT_CHECKED"], `${path}.world_availability.status`);
    const worldItems = array(item.world_availability.items, `${path}.world_availability.items`);
    worldItems.forEach((worldItem, itemIndex) => {
      const itemPath = `${path}.world_availability.items[${itemIndex}]`;
      exact(worldItem, ["item_id", "label", "item_kind", "status", "detail"], itemPath);
      safeId(worldItem.item_id, `${itemPath}.item_id`);
      for (const key of ["label", "item_kind", "detail"]) text(worldItem[key], `${itemPath}.${key}`);
      variant(worldItem.status, ["AVAILABLE", "MISSING", "AMBIGUOUS", "NOT_CHECKED", "OUTSIDE_SCOPE"], `${itemPath}.status`);
    });
    unique(worldItems.map(({ item_id }) => item_id), `${path}.world_availability.items.item_id`);
    variant(item.selection, ["SELECTED", "EXCLUDED"], `${path}.selection`);
    text(item.selection_reason, `${path}.selection_reason`, { nullable: true });
    if (item.selection === "EXCLUDED" && item.selection_reason === null) fail(`${path}.selection_reason`, "excluded case needs reason");
    if (item.selection === "SELECTED" && item.selection_reason !== null) fail(`${path}.selection_reason`, "selected case reason must be null");
  });
  unique(cases.map(({ case_id }) => case_id), "$.cases.case_id");
  for (const key of ["persona_id", "intent_id", "turn_policy_id"]) unique(cases.map(({ simulated_user }) => simulated_user[key]), `$.cases.simulated_user.${key}`);
}

function validateRun(value, selectedCount) {
  const path = "$.run";
  exact(value, ["run_id", "recorded_state", "target", "simulator", "limits", "privacy_egress", "conversation_order"], path);
  safeId(value.run_id, `${path}.run_id`);
  variant(value.recorded_state, ["NOT_STARTED", "RUNNING", "COMPLETED", "COMPLETED_WITH_GAPS"], `${path}.recorded_state`);
  exact(value.target, ["target_id", "label", "connection_state"], `${path}.target`);
  safeId(value.target.target_id, `${path}.target.target_id`);
  text(value.target.label, `${path}.target.label`);
  variant(value.target.connection_state, ["READY", "UNAVAILABLE", "UNKNOWN"], `${path}.target.connection_state`);
  exact(value.simulator, ["provider_label", "model_label", "identity_count"], `${path}.simulator`);
  text(value.simulator.provider_label, `${path}.simulator.provider_label`);
  text(value.simulator.model_label, `${path}.simulator.model_label`);
  integer(value.simulator.identity_count, `${path}.simulator.identity_count`, 1);
  exact(value.limits, ["selected_case_count", "max_turns_per_conversation", "max_conversations", "max_http_exchanges", "max_minutes_per_conversation", "reserved_cost_ceiling_usd", "retry_policy", "repair_policy", "fallback_policy"], `${path}.limits`);
  for (const key of ["selected_case_count", "max_conversations", "max_http_exchanges"]) integer(value.limits[key], `${path}.limits.${key}`);
  for (const key of ["max_turns_per_conversation", "max_minutes_per_conversation"]) integer(value.limits[key], `${path}.limits.${key}`, 1);
  decimal(value.limits.reserved_cost_ceiling_usd, `${path}.limits.reserved_cost_ceiling_usd`);
  for (const key of ["retry_policy", "repair_policy", "fallback_policy"]) variant(value.limits[key], ["NONE"], `${path}.limits.${key}`);
  if (value.limits.selected_case_count !== selectedCount) fail(`${path}.limits.selected_case_count`, "does not match selected cases");
  exact(value.privacy_egress, ["provider", "target", "authorization"], `${path}.privacy_egress`);
  text(value.privacy_egress.provider, `${path}.privacy_egress.provider`);
  text(value.privacy_egress.target, `${path}.privacy_egress.target`);
  variant(value.privacy_egress.authorization, ["SYNTHETIC_APPROVED"], `${path}.privacy_egress.authorization`);
  ids(value.conversation_order, `${path}.conversation_order`);
}

function validateConversations(conversations, caseMap) {
  array(conversations, "$.conversations").forEach((item, index) => {
    const path = `$.conversations[${index}]`;
    exact(item, ["conversation_id", "case_id", "status", "current_turn", "turn_limit", "latest", "goal_state", "termination_reason", "turns", "tool_events", "gaps", "evidence_refs", "accounting"], path);
    safeId(item.conversation_id, `${path}.conversation_id`);
    safeId(item.case_id, `${path}.case_id`);
    if (!caseMap.has(item.case_id)) fail(`${path}.case_id`, "broken reference");
    if (caseMap.get(item.case_id).selection !== "SELECTED") fail(`${path}.case_id`, "excluded case cannot have conversation");
    variant(item.status, ["QUEUED", "RUNNING", "COMPLETE", "PARTIAL", "UNAVAILABLE", "NOT_STARTED"], `${path}.status`);
    integer(item.current_turn, `${path}.current_turn`);
    integer(item.turn_limit, `${path}.turn_limit`, 1);
    text(item.latest, `${path}.latest`);
    variant(item.goal_state, ["MET", "NOT_MET", "REVIEW_REQUIRED", "UNKNOWN"], `${path}.goal_state`);
    text(item.termination_reason, `${path}.termination_reason`, { nullable: true });
    const evidence = array(item.evidence_refs, `${path}.evidence_refs`);
    evidence.forEach((ref, refIndex) => {
      const refPath = `${path}.evidence_refs[${refIndex}]`;
      exact(ref, ["evidence_ref_id", "kind", "label"], refPath);
      safeId(ref.evidence_ref_id, `${refPath}.evidence_ref_id`);
      variant(ref.kind, ["TRACE", "CASE", "TARGET_EVENT", "SIMULATOR_TURN", "TOOL_EVENT", "LINEAGE"], `${refPath}.kind`);
      text(ref.label, `${refPath}.label`);
    });
    unique(evidence.map(({ evidence_ref_id }) => evidence_ref_id), `${path}.evidence_refs.evidence_ref_id`);
    const evidenceIds = new Set(evidence.map(({ evidence_ref_id }) => evidence_ref_id));
    const turns = array(item.turns, `${path}.turns`);
    turns.forEach((turn, turnIndex) => {
      const turnPath = `${path}.turns[${turnIndex}]`;
      exact(turn, ["turn_id", "ordinal", "role", "content", "evidence_ref_ids"], turnPath);
      safeId(turn.turn_id, `${turnPath}.turn_id`);
      integer(turn.ordinal, `${turnPath}.ordinal`, 1);
      if (turn.ordinal !== turnIndex + 1) fail(`${turnPath}.ordinal`, "turn ordinals must be contiguous from 1");
      variant(turn.role, ["USER", "AGENT"], `${turnPath}.role`);
      text(turn.content, `${turnPath}.content`);
      ids(turn.evidence_ref_ids, `${turnPath}.evidence_ref_ids`);
      turn.evidence_ref_ids.forEach((id) => { if (!evidenceIds.has(id)) fail(`${turnPath}.evidence_ref_ids`, `broken reference ${id}`); });
    });
    unique(turns.map(({ turn_id }) => turn_id), `${path}.turns.turn_id`);
    const events = array(item.tool_events, `${path}.tool_events`);
    events.forEach((event, eventIndex) => {
      const eventPath = `${path}.tool_events[${eventIndex}]`;
      exact(event, ["tool_event_id", "after_turn_ordinal", "tool_name", "status", "detail"], eventPath);
      safeId(event.tool_event_id, `${eventPath}.tool_event_id`);
      integer(event.after_turn_ordinal, `${eventPath}.after_turn_ordinal`, 1);
      if (event.after_turn_ordinal > turns.length) fail(`${eventPath}.after_turn_ordinal`, "turn reference out of range");
      text(event.tool_name, `${eventPath}.tool_name`);
      variant(event.status, ["SUCCEEDED", "ERROR", "UNKNOWN"], `${eventPath}.status`);
      text(event.detail, `${eventPath}.detail`);
    });
    unique(events.map(({ tool_event_id }) => tool_event_id), `${path}.tool_events.tool_event_id`);
    const gaps = array(item.gaps, `${path}.gaps`);
    gaps.forEach((gap, gapIndex) => {
      const gapPath = `${path}.gaps[${gapIndex}]`;
      exact(gap, ["gap_id", "reason_code", "label", "detail", "turn_ordinal", "evidence_ref_ids"], gapPath);
      safeId(gap.gap_id, `${gapPath}.gap_id`);
      safeId(gap.reason_code, `${gapPath}.reason_code`);
      text(gap.label, `${gapPath}.label`);
      text(gap.detail, `${gapPath}.detail`);
      if (gap.turn_ordinal !== null) {
        integer(gap.turn_ordinal, `${gapPath}.turn_ordinal`, 1);
        if (gap.turn_ordinal > turns.length) fail(`${gapPath}.turn_ordinal`, "turn reference out of range");
      }
      ids(gap.evidence_ref_ids, `${gapPath}.evidence_ref_ids`);
      gap.evidence_ref_ids.forEach((id) => { if (!evidenceIds.has(id)) fail(`${gapPath}.evidence_ref_ids`, `broken reference ${id}`); });
    });
    unique(gaps.map(({ gap_id }) => gap_id), `${path}.gaps.gap_id`);
    exact(item.accounting, ["http_exchange_count", "tool_call_count", "actual_cost_usd"], `${path}.accounting`);
    integer(item.accounting.http_exchange_count, `${path}.accounting.http_exchange_count`);
    integer(item.accounting.tool_call_count, `${path}.accounting.tool_call_count`);
    decimal(item.accounting.actual_cost_usd, `${path}.accounting.actual_cost_usd`, true);
    if (["QUEUED", "NOT_STARTED", "UNAVAILABLE"].includes(item.status) && turns.length !== 0) fail(`${path}.turns`, `${item.status} requires zero turns`);
    if (item.status === "PARTIAL" && (turns.length === 0 || gaps.length === 0)) fail(path, "PARTIAL requires turns and a gap");
    if (item.status === "COMPLETE" && turns.length === 0) fail(`${path}.turns`, "COMPLETE requires turns");
    if (item.current_turn !== turns.length) fail(`${path}.current_turn`, "must equal recorded turn count");
  });
  unique(conversations.map(({ conversation_id }) => conversation_id), "$.conversations.conversation_id");
  unique(conversations.map(({ case_id }) => case_id), "$.conversations.case_id");
}

function validateResults(value, report) {
  const path = "$.results";
  exact(value, ["learned", "created", "happened", "judgment", "accounting"], path);
  exact(value.learned, ["headline", "detail", "group_count", "usable_conversation_count"], `${path}.learned`);
  exact(value.created, ["headline", "detail", "selected_count", "seen_count", "variation_count", "excluded_count"], `${path}.created`);
  exact(value.happened, ["headline", "detail", "complete_count", "partial_count", "unavailable_count", "running_count", "queued_count", "not_started_count", "goal_met_count", "goal_review_required_count"], `${path}.happened`);
  exact(value.judgment, ["headline", "detail", "review_eligible_count", "reviewed_count"], `${path}.judgment`);
  exact(value.accounting, ["http_exchange_count", "tool_call_count", "actual_cost_usd", "privacy_gap_count", "retry_count", "repair_count", "fallback_count"], `${path}.accounting`);
  for (const section of [value.learned, value.created, value.happened, value.judgment]) {
    text(section.headline, `${path}.headline`);
    text(section.detail, `${path}.detail`);
    for (const [key, field] of Object.entries(section)) if (!["headline", "detail"].includes(key)) integer(field, `${path}.${key}`);
  }
  for (const key of ["http_exchange_count", "tool_call_count", "privacy_gap_count", "retry_count", "repair_count", "fallback_count"]) integer(value.accounting[key], `${path}.accounting.${key}`);
  decimal(value.accounting.actual_cost_usd, `${path}.accounting.actual_cost_usd`, true);
  const expected = {
    group_count: report.behavior.groups.length,
    usable_conversation_count: report.setup.understanding.usable_conversation_count,
    selected_count: countBy(report.cases, "selection", "SELECTED"),
    seen_count: countBy(report.cases, "origin", "SEEN_IN_TRACES"),
    variation_count: countBy(report.cases, "origin", "GROUNDED_VARIATION"),
    excluded_count: countBy(report.cases, "selection", "EXCLUDED"),
    complete_count: countBy(report.conversations, "status", "COMPLETE"),
    partial_count: countBy(report.conversations, "status", "PARTIAL"),
    unavailable_count: countBy(report.conversations, "status", "UNAVAILABLE"),
    running_count: countBy(report.conversations, "status", "RUNNING"),
    queued_count: countBy(report.conversations, "status", "QUEUED"),
    not_started_count: countBy(report.conversations, "status", "NOT_STARTED"),
    goal_met_count: countBy(report.conversations, "goal_state", "MET"),
    goal_review_required_count: countBy(report.conversations, "goal_state", "REVIEW_REQUIRED"),
    review_eligible_count: report.reviews.length,
    reviewed_count: countBy(report.reviews, "review_state", "RECORDED"),
    http_exchange_count: report.conversations.reduce((sum, item) => sum + item.accounting.http_exchange_count, 0),
    tool_call_count: report.conversations.reduce((sum, item) => sum + item.accounting.tool_call_count, 0),
  };
  for (const [key, expectedValue] of Object.entries(expected)) {
    const sections = [value.learned, value.created, value.happened, value.judgment, value.accounting];
    const section = sections.find((candidate) => key in candidate);
    if (section[key] !== expectedValue) fail(path, `${key} does not reconcile`);
  }
  for (const key of ["retry_count", "repair_count", "fallback_count"]) if (value.accounting[key] !== 0) fail(`${path}.accounting.${key}`, "must be zero");
  const conversationCosts = report.conversations.map(({ accounting }) => accounting.actual_cost_usd);
  if (conversationCosts.includes(null) && value.accounting.actual_cost_usd !== null) fail(`${path}.accounting.actual_cost_usd`, "must remain unavailable when a conversation cost is unavailable");
}

function validateReviews(reviews, conversationIds) {
  array(reviews, "$.reviews").forEach((review, index) => {
    const path = `$.reviews[${index}]`;
    exact(review, ["conversation_id", "review_state", "realism", "adaptation", "goal_completion", "scope_privacy_boundaries", "notes"], path);
    safeId(review.conversation_id, `${path}.conversation_id`);
    if (!conversationIds.has(review.conversation_id)) fail(`${path}.conversation_id`, "broken reference");
    variant(review.review_state, ["RECORDED", "UNREVIEWED"], `${path}.review_state`);
    for (const key of ["realism", "adaptation", "goal_completion", "scope_privacy_boundaries"]) variant(review[key], ["YES", "NO", "CANNOT_JUDGE", "UNANSWERED"], `${path}.${key}`);
    text(review.notes, `${path}.notes`, { nullable: true });
    const rulings = [review.realism, review.adaptation, review.goal_completion, review.scope_privacy_boundaries];
    if (review.review_state === "UNREVIEWED" && (rulings.some((value) => value !== "UNANSWERED") || review.notes !== null)) fail(path, "UNREVIEWED requires unanswered rulings and null notes");
    if (review.review_state === "RECORDED" && rulings.some((value) => value === "UNANSWERED")) fail(path, "RECORDED forbids unanswered rulings");
  });
  unique(reviews.map(({ conversation_id }) => conversation_id), "$.reviews.conversation_id");
}

function validateLimitations(limitations) {
  array(limitations, "$.limitations").forEach((item, index) => {
    const path = `$.limitations[${index}]`;
    exact(item, ["limitation_id", "title", "detail", "status", "claim_blocked"], path);
    safeId(item.limitation_id, `${path}.limitation_id`);
    for (const key of ["title", "detail", "claim_blocked"]) text(item[key], `${path}.${key}`);
    variant(item.status, ["BACKLOG", "NOT_EVALUATED", "KNOWN_GAP"], `${path}.status`);
  });
  unique(limitations.map(({ limitation_id }) => limitation_id), "$.limitations.limitation_id");
  const required = ["world-mutation", "intent-precondition", "readiness", "population", "semantic"];
  for (const term of required) if (!limitations.some((item) => `${item.limitation_id} ${item.title}`.toLowerCase().includes(term))) fail("$.limitations", `missing LABS-06 limitation ${term}`);
}

export function validateLabsReport(report) {
  scanForbiddenFields(report);
  exact(report, ["artifact_kind", "schema_version", "report_id", "title", "mode", "privacy_class", "sample_class", "sample_disclosure", "created_at", "lineage", "setup", "behavior", "cases", "run", "conversations", "results", "reviews", "limitations"], "$");
  variant(report.artifact_kind, ["labs_report"], "$.artifact_kind");
  variant(report.schema_version, [1], "$.schema_version");
  safeId(report.report_id, "$.report_id");
  text(report.title, "$.title");
  variant(report.mode, ["GENERATED_MULTI_TURN_SIMULATION"], "$.mode");
  variant(report.privacy_class, ["SYNTHETIC"], "$.privacy_class");
  variant(report.sample_class, ["PUBLIC_SYNTHETIC_REFERENCE"], "$.sample_class");
  text(report.sample_disclosure, "$.sample_disclosure");
  if (!/synthetic/i.test(report.sample_disclosure) || !/interface/i.test(report.sample_disclosure) || !/not (?:a )?(?:production|customer)/i.test(report.sample_disclosure)) fail("$.sample_disclosure", "must disclose synthetic interface sample and deny production/customer result");
  text(report.created_at, "$.created_at");
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(report.created_at) || Number.isNaN(Date.parse(report.created_at))) fail("$.created_at", "expected fixed ISO-8601 UTC timestamp");
  validateLineage(report.lineage, "$.lineage");
  validateSetup(report.setup, "$.setup");
  validateBehavior(report.behavior, "$.behavior");
  validateCases(report.cases, new Set(report.behavior.groups.map(({ group_id }) => group_id)));
  const caseMap = new Map(report.cases.map((item) => [item.case_id, item]));
  validateRun(report.run, countBy(report.cases, "selection", "SELECTED"));
  validateConversations(report.conversations, caseMap);
  const conversationIds = new Set(report.conversations.map(({ conversation_id }) => conversation_id));
  if (report.run.conversation_order.length !== report.conversations.length || report.run.conversation_order.some((id) => !conversationIds.has(id))) fail("$.run.conversation_order", "must contain every conversation exactly once");
  validateReviews(report.reviews, conversationIds);
  validateResults(report.results, report);
  validateLimitations(report.limitations);
  return report;
}

function main() {
  const args = process.argv.slice(2);
  if (args.length !== 2 || args[0] !== "--validate") {
    console.error("Usage: node scripts/build-snapshot.mjs --validate <labs-report.json>");
    process.exitCode = 2;
    return;
  }
  try {
    const path = resolve(process.cwd(), args[1]);
    const report = JSON.parse(readFileSync(path, "utf8"));
    validateLabsReport(report);
    console.log(`Validated ${report.report_id} (${report.conversations.length} conversations)`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) main();
