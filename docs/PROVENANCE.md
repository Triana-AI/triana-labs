# Provenance and clean-room ledger

## Repository origin

This repository was created from scratch on 2026-07-30 at Akarsh's request.
It does not share Git history with Agentagon and contains no Agentagon
implementation.

The initial Markdown files were newly authored to preserve decisions made by
Akarsh during Triana product work. They are not a code port.

## Source policy

| Source | Status | Allowed use |
|---|---|---|
| `/Users/akarshgajbhiye/agentagon` | Restricted | Do not copy code or artifacts. Rewrite Akarsh-owned facts and accepted decisions only. |
| `/Users/akarshgajbhiye/kairos` | Permitted with ledger | Inspect, copy, or reimplement Akarsh-owned code after recording exact provenance and licenses. |
| `/Users/akarshgajbhiye/Documents/hr_ai` | Permitted with ledger (authorized by Akarsh 2026-07-31) | Inspect, copy, or reimplement Akarsh-owned code after recording exact provenance and licenses per the reuse procedure. |
| `/Users/akarshgajbhiye/agentagon/Triana demo` (package `triana-demo`, including `triana-demo-clean-video`) | Permitted with ledger (explicit Akarsh allowlist exception 2026-07-31; rest of Agentagon stays Restricted) | Inspect and adapt this UI for the Triana Labs Preview report after per-file authorship/ancestry checks and a reuse-ledger entry. |
| `/Users/akarshgajbhiye/kairos-ai` | Permitted with ledger | Inspect, copy, or reimplement Akarsh-owned code after recording exact provenance and licenses. |
| Blitz "Leo" production corpus (`~/Downloads/blitzlangsmith_*.jsonl`; `agentagon/experiments/blitz_seed/**`) | Design-partner data (letter of intent held by Akarsh, stated 2026-07-31) | Internal mining, miner validation, and persona/intent derivation permitted. No raw conversations, quotes, or PII in any public artifact or open-source repo without explicit Blitz sign-off; derived public assets must be synthetic regenerations labeled "generated, blitz-informed". |
| Triana Notion database | Permitted context | Rewrite Akarsh-owned product decisions, interviews, and research; link canonical pages. |
| Third-party repositories/packages | License-dependent | Record version, license, and usage before adoption. |

The Agentagon repository's current Git authorship cannot establish file-level
ownership because its history was reset. Do not infer eligibility from the
current commit author.

## Reuse procedure

Before a port:

1. Record source repository, path, and commit SHA.
2. Check source authorship and any third-party origin.
3. Check the source repository license and file headers.
4. Confirm that the source was not previously copied from Agentagon.
5. Decide whether to copy, adapt, or cleanly reimplement.
6. Record the destination and material changes below.
7. Add focused tests that describe Triana's contract rather than preserving
   accidental source behavior.

## Reuse ledger

| Date | Capability | Source repository/path@commit | Destination | Method | License/ownership check | Executor |
|---|---|---|---|---|---|---|
| 2026-07-30 | Initial context pack | Akarsh-authorized decisions; no source port | Repository Markdown files | Newly authored | No Agentagon code copied | Codex |
| 2026-07-30 | Triana research and specification archive | `/Users/akarshgajbhiye/.codex/attachments/15f0f993-baea-47eb-91cd-68ae5d40342d/pasted-text.txt`; `/Users/akarshgajbhiye/agentagon/internal/RELEASE_CONTROL_PLANE_MARKET_RESEARCH_2026-07-29.md`; `/Users/akarshgajbhiye/agentagon/internal/TRIANA_THESIS_INVESTIGATION_2026-07-29.md`; `/Users/akarshgajbhiye/agentagon/internal/TRIANA_SELF_SERVE_V0_FROZEN_2026-07-29.md`; `/Users/akarshgajbhiye/agentagon/internal/TRIANA_SELF_SERVE_V1_SHIP_SPEC_2026-07-29.md`; `/Users/akarshgajbhiye/agentagon/internal/TRIANA_WEDGE_V1_SPINE_2026-07-29.md`; `/Users/akarshgajbhiye/agentagon/internal/TRIANA_DEMO_VIDEO_SCRIPT.md` | `internal/research/` | Exact documentation copies explicitly authorized by Akarsh; historical context only | Documentation and founder-owned research/specification prose; no code, prompts, schemas, fixtures, UI, generated artifacts, configuration, infrastructure, or Git history copied | Codex |
| 2026-07-30 | Conversation handoff and Braintrust differentiation map | Akarsh × Codex strategic conversation through 2026-07-30 | `internal/TRIANA_RESEARCH_CONVERSATION_HANDOFF_2026-07-30.md`; `internal/BRAINTRUST_DIFFERENTIATION_MIND_MAP_2026-07-30.md` | Newly authored synthesis | Founder conversation and public-source research; no implementation port | Codex |
| 2026-07-30 | Release Change and Release Obligation clarification, discovery ask guide, worked model-upgrade example, and gated future direction | Akarsh × Codex strategic conversation through 2026-07-30; official Braintrust and OpenAI documentation used as cited conceptual context | `docs/PRODUCT.md`; `docs/ARCHITECTURE.md`; `docs/FOUNDER_CONTEXT.md`; `internal/WORKING_MEMORY.md`; `internal/SLICE_PACKET.md`; `internal/TRIANA_RESEARCH_CONVERSATION_HANDOFF_2026-07-30.md`; `internal/BRAINTRUST_DIFFERENTIATION_MIND_MAP_2026-07-30.md`; `internal/DISCOVERY_ASK_GUIDE.md`; `internal/examples/HIRING_AGENT_MODEL_UPGRADE_RELEASE_REVIEW.md`; `internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md`; `README.md` | Newly authored clarification and examples | No implementation, customer artifact, schema, fixture, prompt, UI, configuration, or Git history copied; the hiring-agent example is synthetic | Codex |
| 2026-07-30 | Shared agent governance, two-level decision memory, and versioned Git-hook workflow | `/Users/akarshgajbhiye/kairos-ai/AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/engineering-principles.md`, and `scripts/git-hooks/post-commit` at `4167194431570a91c23c72c50b5997f7af61d251`; hook origin commit `3ad465ecede2e28a1f471d54f50dc349a5ad0d4c`; Akarsh's local `~/.claude/CLAUDE.md` and `~/.claude/settings.json` inspected on 2026-07-30 | `AGENTS.md`; `CLAUDE.md`; `.claude/settings.json`; `CONTRIBUTING.md`; `docs/ENGINEERING.md`; `scripts/git-hooks/`; `scripts/install-git-hooks.sh`; `scripts/verify-governance.sh`; `.gitignore` | Clean reimplementation for Triana; no product code copied | Kairos-AI is MIT-licensed and the relevant governance commits/blame are Akarsh-authored; the source files are process guidance rather than Agentagon implementation, and inspection found no Agentagon-derived product material in the reused capability | Codex |
| 2026-07-30 | CI gates, deterministic fixtures and seeds, repeatability, tamper checks, negative architecture tests, redaction tests, and artifact-to-claim consistency practices | `/Users/akarshgajbhiye/kairos-ai/.github/workflows/ci.yml`, `pyproject.toml`, `scripts/check_published_numbers.py`, `src/kairos/eval/corpus.py`, `src/kairos/eval/harness.py`, `scripts/eval_run.py`, `tests/test_no_dropped_modules.py`, `tests/test_redaction_pattern_sync.py`, `tests/eval/test_corpus.py`, `tests/eval/test_harness.py`, and `tests/scripts/test_build_kappa_bundles.py` at `4167194431570a91c23c72c50b5997f7af61d251`; relevant source commits `78c824e621f24fb7f663cf2b334cc58c0fa7594b`, `af570f519344eea6908bad2a13aa5b878fc663d8`, `41212777970e7a8ff52019ad24aa11406a694292`, `c29593f1cbb0b8bd4bbb5e3da97463a176565c60`, `7ff4465c714284f1eb528e24a9c5f009cfd53d78`, `b29ce73e83e6196936bc6dc8c449cb54beded01a`, `0dd7288d213cd059f869e11bec1fc7b215bf8461`, `8d92aa3ffb2294ae972970ec049d6ff87c54813a`, `a9b2cd2260edb35f0aff634072c95a2348eb06ff`, and `564fe6f6effbf7d101ef0811e3554b83bdaf8605` | `AGENTS.md`; `docs/ENGINEERING.md`; `internal/SLICE_PACKET.md`; `internal/WORKING_MEMORY.md` | Practices cleanly reimplemented for Triana; no Kairos code, tests, fixtures, corpora, or schemas copied | Kairos-AI is MIT-licensed; inspected paths and relevant commits are Akarsh-authored, and no Agentagon copy/port attribution was found in those paths or relevant commit messages. This is negative ancestry evidence, not proof. Kairos coding-agent/session corpora remain outside Triana V1 acceptance truth and may be used only as labeled engineering stress tests. | Codex |
| 2026-07-30 | Braintrust HRAI dogfood cold-start report, doubt-driven falsification memo, proposed Triana Labs Preview/Guard/Learn concept, and fresh-session handoff | Triana Braintrust dogfood artifacts under `internal/research/braintrust_hrai_dogfood_2026-07-30/`; Akarsh × Codex discussion through 2026-07-30; HRAI experiment documents at observed repository commit `728f6c5058efe40a16e2aecc9b528b3353f4df4f` used as evidence only; Kairos-AI failure-memory document at `4167194431570a91c23c72c50b5997f7af61d251`; current official product sources linked in the research documents | `internal/research/BRAINTRUST_HRAI_DOGFOOD_COLD_START_2026-07-30.md`; `internal/research/BRAINTRUST_FALSIFICATION_AND_DOUBT_DRIVEN_DECISION_2026-07-30.md`; `internal/research/TRIANA_LABS_PREVIEW_GUARD_LEARN_CONCEPT_2026-07-30.md`; `internal/research/TRIANA_PREVIEW_FRESH_START_HANDOFF_2026-07-30.md` | Newly authored research synthesis; no implementation copied | HRAI is not currently an authorized source-mining repository and no HRAI code was copied; Kairos/Kairos-AI remain subject to the existing ledger procedure; public product facts are cited rather than copied as implementation | Codex and delegated research agents |
| 2026-07-31 | LABS-01 synthetic Trace Observer, acceptance suite, adversarial boundaries, and verification command | Active Triana Labs charter, canonical execution plan, and independently authored repository-local slice contract/tests; no external implementation repository inspected or mined | `triana-labs/src/triana_labs/**`; `triana-labs/tests/**`; `triana-labs/scripts/verify.sh` | Newly authored clean-room implementation and independent black-box tests | No Agentagon, Kairos, Kairos-AI, HRAI, customer corpus, external prompt, schema, fixture, or code copied; only the already approved PyPI runtime/development packages in `triana-labs/uv.lock` are used | Independent test-author agent, implementation-author agent, and Codex orchestrator |
| 2026-07-31 | LABS-02 HRAI normalized-trace-v2 reference mapping | `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/runner/run_preflight.py` and `runner/hr_bridge.py` at repository commit `728f6c5058efe40a16e2aecc9b528b3353f4df4f` | `triana-labs/examples/hrai_v2/adapter.py`; `triana-labs/examples/hrai_v2/README.md`; independently authored `triana-labs/tests/adapter_fixtures/**`, `tests/adapter_acceptance/**`, and `tests/adapter_adversarial/**` | Clean reimplementation from the owner-approved LABS-02 mapping contract; no source code or data copied | HRAI source mining is explicitly permitted; inspected files are Akarsh-owned experiment/exporter code at the recorded commit. No raw HRAI traces, prompts, generated corpora, fixtures, or implementation code entered Triana; all committed fixtures are newly authored synthetic data. | Independent test-author agent, implementation-author agent, and Codex orchestrator |
| 2026-08-01 | LABS-04 non-test Grounded Case Factory smoke input | `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/out/run_50b/normalized_traces.jsonl` at repository commit `728f6c5058efe40a16e2aecc9b528b3353f4df4f`, 50 physical lines, SHA-256 `62d0d188c05a34e346edfb0315b6348343037fcf25a94cf32d10384e5a9b6c61` | Read in place by the existing LABS-02 adapter during an authorized local smoke; only independently validated Triana outputs may enter local evidence | No copy or implementation reuse; synthetic external evidence is transformed at runtime | HRAI source mining and this smoke are owner-authorized. The file is tracked, Akarsh-owned synthetic historical-traffic output and is labeled `SYNTHETIC_EXISTING_TRACE_CORPUS`, never production, customer, Blitz, or real-user evidence. Raw HRAI data and provider payloads must not enter the Triana repository. | Akarsh authorized; Codex froze the use; implementation roles not yet started |
| 2026-08-01 | LABS-04 smoke-input correction, superseding the preceding `run_50b` smoke identity only | `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/out/run_200/normalized_traces.jsonl` at repository commit `728f6c5058efe40a16e2aecc9b528b3353f4df4f`, 200 physical lines, SHA-256 `76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b`; first 50 physical lines selected byte-for-byte, SHA-256 `4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c` | Selected outside the repository into a private temporary file and read by the existing LABS-02 adapter during the authorized smoke; only independently validated Triana outputs may enter local evidence | No copy or implementation reuse; deterministic temporary selection and runtime transformation only | Preflight proved the originally named file was legacy and incompatible (0/50 accepted). The corrected tracked v2 subset yielded 25 accepted and 25 typed source rejections. Both the correction and unfavorable denominator are preserved; raw HRAI data and provider payloads remain outside Triana. | Codex corrected the pre-worker freeze after independent preflight; Akarsh reaffirmed fail-fast/no-fallback execution |
| 2026-08-02 | LABS-04 restricted agent runtime and deterministic scale-out | Repository-local frozen contracts, independent tests, and clean-room implementation; PyPI packages LangChain 1.3.14 (MIT), langchain-openai 1.4.0 (MIT), LangGraph 1.2.9 (MIT), and OpenAI 2.52.0 (Apache-2.0) | `triana-labs/src/triana_labs/case_factory/`; corresponding tests, package metadata, and lockfile | Newly authored Triana implementation using pinned third-party packages; no external product code copied | Package metadata was inspected from the locked environment; no Agentagon, Kairos, Kairos-AI, HRAI implementation, external prompts, fixtures, or provider payloads were copied. HRAI remained runtime-only synthetic evidence under the prior ledger entry. | Independent test author, implementation author, and Codex orchestrator |
| 2026-08-02 | LABS-05 target-specific HRAI Recruiter Chat ReAct subprocess and HTTP/tool accounting design | `/Users/akarshgajbhiye/Documents/hr_ai/src/graph/workflow.py`, `src/llm.py`, `src/prompts/evaluation.py`, `experiments/historical_traffic_v0/runner/hr_bridge.py`, `runner/cost_ledger.py`, and `out/run_200/RUN_MANIFEST.json` at commit `728f6c5058efe40a16e2aecc9b528b3353f4df4f` | Planned `triana-labs/examples/hrai_recruiter_chat_v1/` target adapter plus `triana-labs/src/triana_labs/adaptive_runner/`; final exact files reconciled at exit | Clean-room Triana wire/controller/accounting implementation; runtime imports only the pinned HRAI prompt/tool packages and exposes newly authored in-memory synthetic read-only tool projections; no HRAI source, prompt, DB, fixture, trace, or provider payload is copied | HRAI is Akarsh-owned and explicitly permitted for source mining. The recorded files establish existing Recruiter Chat ReAct construction, model/prompt identity, tool capture, and accounting behavior. Git inspection at the pinned commit found no Agentagon attribution in these paths; this is negative evidence, not proof. Relevant Python/LangChain dependencies retain their existing licenses; no new dependency is added. | Codex froze the source/destination/method; independent authorship and final ancestry reconciliation pending |

## Explicit documentation allowlist

Akarsh explicitly authorized the following exact documentation sources to
cross into this repository on 2026-07-30:

1. `/Users/akarshgajbhiye/.codex/attachments/15f0f993-baea-47eb-91cd-68ae5d40342d/pasted-text.txt`
2. `/Users/akarshgajbhiye/agentagon/internal/RELEASE_CONTROL_PLANE_MARKET_RESEARCH_2026-07-29.md`
3. `/Users/akarshgajbhiye/agentagon/internal/TRIANA_THESIS_INVESTIGATION_2026-07-29.md`
4. `/Users/akarshgajbhiye/agentagon/internal/TRIANA_SELF_SERVE_V0_FROZEN_2026-07-29.md`
5. `/Users/akarshgajbhiye/agentagon/internal/TRIANA_SELF_SERVE_V1_SHIP_SPEC_2026-07-29.md`
6. `/Users/akarshgajbhiye/agentagon/internal/TRIANA_WEDGE_V1_SPINE_2026-07-29.md`
7. `/Users/akarshgajbhiye/agentagon/internal/TRIANA_DEMO_VIDEO_SCRIPT.md`

These files are preserved as historical research and rationale. They are not
implementation sources and cannot supersede `docs/PRODUCT.md`.

## Explicit exclusions at bootstrap

- Agentagon Python packages and tests;
- Agentagon trace, signal, eval, diff, and runner schemas;
- Agentagon prompts and LLM workflows;
- Agentagon fixtures, customer artifacts, and generated reports;
- Agentagon UI, demos, CSS, images, and landing-page implementation;
- Agentagon configuration and infrastructure;
- Agentagon Git history.

If Akarsh later wants a specific Akarsh-authored Agentagon file to cross, add an
explicit allowlist entry here before touching it. The entry must name the file
and why its ownership is sufficiently established.
