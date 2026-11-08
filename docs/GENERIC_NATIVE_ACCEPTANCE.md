# Generic native host acceptance — 11 portable specialist packages

**Scope:** The deliverables here are **generic roles**, not the original live
assistants that inspired them. Existing agents may inform contract research;
their live user identities, skills registries, memories, tasks, credentials and
runtime databases are never a deployment target for this repository.

The public and private R32 trees target **11 distinct portable specialists**
using the catalog under `presets/`. This module implements a reusable,
create-only, offline acceptance packet for each of the 11 roles and each of two
different host profiles, `personal-hatch` and `muse-code`.

## What is implemented

- `native_canary.make_canary`: validates one neutral role and host profile,
  sources immutable-in-the-packet SHA-256 pins from `preset.json` and
  `playbook.json`, and creates an ephemeral correlation challenge.
- `native_canary.stage_canary`: writes **only a fresh destination** with
  `GENERIC_CANARY.json`, `NATIVE_HANDOFF.md`, and `SOURCE_RECEIPT.json`.
  It refuses symlink/junction ancestors, literal parent traversal, and any
  existing destination. It does **not** create owner files or register skills.
- `native_canary.inspect_canary`: reads the closed tree and current source
  pins; unexpected files, duplicate JSON keys, altered instructions or
  fabricated authority flags trigger `REVIEW_REQUIRED`.
- `native_canary.assess_fixture_transcript`: verifies exact session, skill,
  challenge, invocation and readback correlations in **synthetic test data**.
  Even complete correlated fixture events only yield
  `FIXTURE_CONSISTENT_ONLY`, never real provider/recipient authority.
- `unsupported_native_invoke`: explicit fail-closed default.
  No binary, local shell, browser, socket, Muse Code session or alternative
  model transport is selected as an implicit fallback.

## Run anywhere with the repository and Python 3.10+

```sh
PYTHONPATH=src python -B -m muse_presets.cli generic-native-canary \
  --preset software-engineer --host personal-hatch \
  --to ./new-disposable-personal-hatch-packet

PYTHONPATH=src python -B -m muse_presets.cli generic-native-inspect \
  --path ./new-disposable-personal-hatch-packet

PYTHONPATH=src python -B -m muse_presets.cli generic-native-canary \
  --preset garden-companion --host muse-code \
  --to ./new-disposable-muse-code-packet
```

Use a **new absolute destination** with an existing parent directory. These
commands neither contact a provider nor request owner consent. They only
prepare artifacts. Their exit code 0 means successful **local source**
operation, never a native auth grant. All 11 role IDs come from the existing
catalog, not a donor VM.

## Assemble all eleven portable profiles in one source-only fleet

`generic-native-fleet` is a create-only assembler: it stages the neutral
`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`,
`MEMORY.md`, `HEARTBEAT.md`, `SUBCHATS.md`, `HOOKS.md`, role playbook,
and remaining profile files for **all eleven** existing generic roles.
Every role also has both a personal-Hatch and Muse Code disposable handoff.

```sh
PYTHONPATH=src python -B -m muse_presets.cli generic-native-fleet \
  --to ./new-generic-fleet
PYTHONPATH=src python -B -m muse_presets.cli generic-native-fleet-inspect \
  --path ./new-generic-fleet
```

The result includes 11 profile drafts, 22 host handoffs and a closed-tree
`FLEET_RECEIPT.json` with source/packet hashes. A partial operation retains
`STAGING_INCOMPLETE` for explicit recovery; no existing destination is
overwritten. The resulting `LOCAL_FLEET_MATCH` is **source integrity**,
not proof that any model loaded the profiles, used the skills, or shared
memory across devices. This source-only fleet must not be installed onto
reference or donor accounts.

## What the two host profiles mean

| Profile | Confirmed generic source contract | Native binding |
| --- | --- | --- |
| `personal-hatch` | Separate first-party client/owner principal, selected skill and host callback, runtime and scope authority to prove | Not exposed to this generic source package; `UNVERIFIED` |
| `muse-code` | Separate developer session, `skill/list` and `read_skill` per official SDK, host plugin/approval route | Not installed or authenticated by this source package; `NOT_RUN` |

These are **different products and sessions**. Documented Muse Code
`skill/list` and `read_skill` do not attest an existing personal Muse agent.
A Space action with a typed viewer or invocation ID is not evidence that
a model has autonomously selected and executed a native personal skill.

## Necessary external provider port (not implemented or inferred)

The receiving **owner-approved host integration**, rather than this Python
library, must implement and expose:

1. **D1 Discover:** authenticated principal and session from the host,
   provider-issued skill discovery event and exact advertised skill ID.
2. **D2 Bind:** approved disposable skill registration and owner grant,
   recorded against the exact admitted source digest.
3. **D3 Invoke:** fresh model-selected **read-only** skill invocation,
   provider event ID, same owner/session and challenge, no shell stand-in.
4. **D4 Deny:** provider-enforced refusal by a *different, separately
   consented disposable principal* for the same scoped resource.
5. **D4 Read back:** original authorized recipient independently fetches
   the provider-created result, with session/event correlation, correct
   source pin and restart/recovery evidence where applicable.

An event bundle made by the model, a JSON field claiming authentication,
a local registry entry, an HMAC held by the project, or a fixture receipt
cannot satisfy these requirements. Stop as `HOST_UNSUPPORTED` or
`NATIVE_UNVERIFIED` if the authentic provider interface is missing.
Never install into, use a wrong-owner identity from, or modify an original
reference agent as an alternative.

The current readiness grade is **EXISTS + locally CORRECT for the generic
canary package**. Native WIRED, USED, USEFUL and provider L1–L5 are NOT_RUN.

## Hard boundaries

- No public release of originally derived engine components without the
  separate source-rights clearance.
- No paid service, model training, cloud deployment, network call or live
  installation in this workflow.
- No owner memory, identity, subchat or connector changes to any existing
  account.
- Native permission checks are enforced at the actual host action entrypoint,
  not in this standalone preflight or a caller-controlled simulation.
- Retain source hashes, exact test exits, cross-OS skips and independent
  readback before promoting maturity status.
