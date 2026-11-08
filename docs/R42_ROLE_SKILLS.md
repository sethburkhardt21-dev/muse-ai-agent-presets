# R42 / T06: role-scoped skill registry proposals for eleven generic agents

**Status: SOURCE_ONLY, not a native Muse/Hatch install.**

This capability extends the existing T04 source-profile and T05 scoped subchat
contracts. It creates, inspects, and previews **three exact role-method
custom-skill descriptors per agent**, totaling **33** across eleven roles. The
shared Evidence Finder remains a service, not a twelfth agent.

## Run the source commands

Run Python 3.10+ at the repository root with PYTHONPATH=src. On PowerShell
set $env:PYTHONPATH='src' first.

    python -B -m muse_presets.cli role-skills-plan --preset software-engineer
    python -B -m muse_presets.cli role-skills --preset software-engineer --to ./new-role-skills --profile-source-sha256 SHA_FROM_PLAN
    python -B -m muse_presets.cli role-skills-inspect --path ./new-role-skills
    python -B -m muse_presets.cli role-skills-preview --path ./new-role-skills --target ./actual-owner-config

The parent must exist; the requested destination must be absent.
Staging never installs into a live original agent. An interrupted operation
leaves STAGING_INCOMPLETE and is not automatically removed or retried.
The source SHA is verified before any destination is created; a change
during staging is fenced. Owner configuration remains unmodified.

## Source package contents

Every individual role package contains:

- custom-skills/ROLE_METHOD/SKILL.md: the actual trigger, steps, evidence,
  stop condition, proposed next role, and a statement that it is not installed.
- custom-skills/ROLE_METHOD/skill.yaml: an exact source-defined title,
  description, name, and include_in_prompt: false. No executable is bundled.
- config/skills.yaml: a strict version-one status catalog containing only
  that role's three method skills with status: disabled.
- config/subchat-skills.json: exact method-to-skill allowlist, linked
  to the T04 profile source SHA and T05 method scopes, with all host tool
  identities and native loading flags disabled or null.
- config/local-code-links.json: source SHA-256 references to existing working
  local engines for Coordinator, Software Engineer, and Model Builder.
  These are references, not executable copies or model-selected invocations.
- config/host-binding.json: owner, agent and session IDs null; any grant,
  skill installation, external side effect or recipient verification false.
- ROLE_SKILL_RECEIPT.json: a local source-pinned closed-tree manifest; **not**
  a publisher signature, provider receipt or native permission.

Current generic roles: coordinator, software-engineer, model-builder,
research-evaluator, creative-studio, adversarial-verifier, personal-companion,
garden-companion, learning-coach, claims-adjudicator,
reverse-engineering-researcher.

Existing source-tested execution remains available via the separately
implemented role bundles. Those qualified binaries and engines are not
implicitly copied into all 33 guidance skills. In particular, creating a
SKILL.md file does not make an unavailable runtime callable.

## Safety and technical acceptance

The source inspector re-generates exact expected bytes and uses the existing
custom-skill catalog parser to ensure the resulting skill descriptors and
version-one registry are well-formed. It rejects wrong-role methods, duplicate
registry entries, malformed descriptors, missing bodies, forged host grants,
extra executables, unlisted files, symlinks, source drift, local manifest
forgery and any change to status: available or status: connected.

The preview is read-only and reports CREATE, UNCHANGED or REVIEW_CONFLICT
without opening unrelated owner memory or writing the target. can_apply is
always false. The package cannot dispatch a worker, create a provider chat,
start cron, send a Family Link message, change another owner account or execute
an unreviewed helper script.

Existing T04 source profile and T05 scoped subchats are reused, not cloned into
another competing controller or scheduler. Claims requiring original native
owner identities, signed plugin permissions, registration, model-selected tool
invocation, recipient readback, effective profile precedence or persistent
subchat state remain separate T02/T07/T32 host gates.

## Exact native qualification required later

Use a supported, authenticated personal Hatch owner session and a disposable
recipient. Discover provider-issued owner/agent/subchat and skill IDs; require
explicit owner approval before installing descriptors or changing its actual
skills.yaml. Prove source hash, native skill search, model selection, execution,
recipient readback, wrong-owner refusal and restart. Do not equate Muse Code
developer plugin behavior with personal Hatch skill selection.

The user has authorized adaptation of their first-party Muse/Atlas code. Do
not invent first-party redistribution obstacles. Preserve owner memories and
credentials, actual third-party terms where applicable, fresh clean public
history, and separate native-usefulness proof. This R42 source work makes no
public-release or host-execution claim.
