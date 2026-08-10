# Triana agent skills

This package exposes one canonical local onboarding skill to Codex and Claude
Code. It prepares operator-authorized conversational traces for a private,
digest-pinned Triana Preview image. It does not include the Behavior Map engine,
credentials, customer data, telemetry, or a public image.

Codex reads `plugins/triana/skills/onboard/`. Claude Code installs the local
marketplace and invokes `/triana:onboard`. Both surfaces call the same
standard-library script and use the same adapter contract.

The included release manifest is deliberately unpublished. Replace it only
with a separately authorized manifest for an immutable private image digest.
