# Triana skill — first-run language slice

Date: 2026-08-11
Status: **AUTHORIZED; ENTRY GATE FROZEN**
Parent: `internal/TRIANA_PUBLIC_RELEASE_SLICE_2026-08-11.md`

## Outcome

Make the public `onboard` skill understandable from a first-time user's point
of view. The opening request becomes only a trace path plus a short description
of what the agent does. Do not expose `provider mode`, `provider configuration`,
provider files, or CLI flags as the initial product concept.

The runtime remains `triana-preview==0.1.0a1`; no Python package or PyPI change
is authorized. Publish only a new Skills plugin version after bounded tests and
fresh-session review.

## First-run contract

The skill accepts a natural request equivalent to:

```text
Use Triana on this trace file: /path/to/traces.
This is what my agent does: <short description>.
```

It then explains in plain language that meaningful statements about what users
ask for and what the agent repeatedly does require a model to interpret
redacted excerpts. The excerpts go directly from the user's machine to the
model service the user chooses; nothing is sent to Triana. It asks only:

1. explicit permission to read and process the exact trace path locally;
2. whether it may use the model setup already configured for that project;
3. where that setup lives, without asking the user to paste a secret;
4. approval for a clearly stated maximum number of model requests.

After structural inspection reveals the trace count, the skill may propose a
conservative ceiling of `max(20, 3 * trace_count)` requests, label it as a
ceiling rather than an estimate of actual usage or cost, and require explicit
approval. It must never silently select or increase the ceiling.

If the user authorizes an existing model setup, the agent may inspect only the
exact configuration location or named variables the user identifies. It must
not discover ambient credentials, source executable configuration, print or
repeat secrets, or send anything before egress approval. It may locally derive
the runtime's private `0600` three-key file as hidden plumbing, validate its
permissions, use it for the run, and remove the derived file afterward. Failure
to map an OpenAI-compatible HTTPS base URL, API key, and explicit model becomes
a plain-language request for one secure setup step; do not guess.

The no-model path is described as an advanced structural diagnostic that cannot
produce the requested semantic behavior map. It is offered only when the user
declines model use or no authorized setup exists. Internal CLI flags remain in
the execution section for the agent, not in the opening user dialogue.

## Authority and privacy

The user owns trace-read authorization, exact configuration-location access,
model egress, and the maximum request ceiling. The model proposes semantic
labels only. Deterministic runtime code continues to own redaction, call
accounting, report lineage, and verification. Nothing in this slice weakens the
public runtime's explicit provider file, no-retry, no-fallback, or call-cap
controls.

## Change budget

Skills repository only:

- `plugins/triana/skills/onboard/SKILL.md`;
- `plugins/triana/skills/onboard/agents/openai.yaml`;
- both plugin manifests for version/description parity;
- `README.md` only if first-run copy requires parity;
- `tests/test_plugin_contract.py`.

No new file, script, dependency, runtime code, workflow change, Preview version,
trace, credential, provider call, or ABCD execution is allowed. Test author and
implementation author are independent and serial on the shared repository.

## Acceptance

1. A frozen test proves the initial dialogue uses plain model/data language and
   does not ask a first-time user for provider jargon or a secret.
2. The test proves explicit trace, config-location, egress, and request-ceiling
   authority remain intact.
3. The secure derived-file lifecycle, no-discovery rule, semantic/no-model
   distinction, and `max(20, 3 * trace_count)` proposal are explicit.
4. Existing seven repository/plugin/runtime-pin controls stay green.
5. Skill Creator and official Claude validators pass.
6. A fresh agent given only the updated public skill and the natural request
   above asks the intended human questions without reading data or calling a
   provider.

## Independent RED freeze — 2026-08-11

The independent test author changed only `tests/test_plugin_contract.py`. The
nine-case suite retains all seven prior controls and adds two first-run/security
contracts. Current skill bytes produce exactly three valid failures: both
manifests remain `0.1.0`, the opening still exposes provider jargon and lacks
the plain model explanation, and the secure existing-setup/derived-file/no-model
lifecycle is absent.

Frozen test SHA-256:

- `tests/test_plugin_contract.py`:
  `072a7767c3d04c917c122eb683285d8aa82ea8a1a2e5f9b68367ffb85090c93c`

Status: **RED FROZEN; INDEPENDENT IMPLEMENTATION AUTHOR AUTHORIZED**.

## Superseding independent RED freeze — 2026-08-11

The independent test author consolidated the two new first-run assertions into
one regression without changing their contract. The eight-case suite now has
six passing controls and exactly two valid failures: manifest version and the
first-run/security contract. This freeze supersedes only the preliminary test
hash above.

Frozen test SHA-256:

- `tests/test_plugin_contract.py`:
  `7d8f424b894bcd4c190f10c93424cd003388e91563cf4bc312df23499d88550e`

Status: **RED FROZEN; INDEPENDENT IMPLEMENTATION AUTHOR AUTHORIZED**.

## GREEN implementation evidence — 2026-08-11

The independent implementation author changed only the five authorized
production paths: the skill, its OpenAI metadata, both plugin manifests, and
README first-run copy. The plugin version is `0.1.1`; the Preview runtime stays
at `0.1.0a1`. The frozen test bytes remain exact.

Verification is GREEN: eight of eight repository contract tests, Skill Creator
validation, both official Claude plugin validations, and `git diff --check`.
The fresh-session reviewer supplied only a trace path and agent description,
did not read the path or make a call, and asked for local-read permission plus
plain model-use/setup-location permission without provider-file jargon. Its
only ambiguity—what “model setup” means—was corrected to the existing settings
the agent already uses, not a Triana account, with a one-step guided path when
the user does not know the location.

No trace, credential, provider call, Preview/PyPI change, dependency, workflow,
or ABCD execution occurred.

Status: **GREEN; PUBLICATION AUTHORIZED BY THE EXISTING RELEASE REQUEST**.

## Public release evidence — 2026-08-11

Commit `25520de34e9b47d4c0640d790429c18cf7daa5dc` is public on
`Triana-AI/triana-skills` branch `release/0.1.0a1`. The old locally configured
marketplace was replaced with that public GitHub source, and
`triana@triana-skills` version `0.1.1` is installed and enabled from the public
snapshot. No new Preview or PyPI release was required.

Status: **COMPLETE**.
