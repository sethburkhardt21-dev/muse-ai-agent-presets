# R33 Coordinator — independent generic native-format source bundle

The Coordinator is the **second role with a real local executable component**.
It reviews externally supplied workgraphs and evidence assertions. It does
not compile missions, choose worker machines, schedule jobs, delegate across
accounts, send Family Link messages or grant permissions.

This package is independent of every original Muse agent. All profiles,
memory files, skills, role contracts and test data are neutral and newly
created. No original host, persona, personal memory or credential is copied.

## Stage and inspect

From the repository root (Python 3.10+):

    PYTHONPATH=src python -B -m muse_presets.cli coordinator-dropin --to ./new-coordinator
    PYTHONPATH=src python -B -m muse_presets.cli coordinator-dropin-inspect --path ./new-coordinator

The destination must **not exist** and its parent must already exist.
The stager writes only local files; an interrupted stage retains
STAGING_INCOMPLETE and is never silently cleaned or retried.

The inspector compares all runtime, policy and skill contents against the
repository's current source, checks the packaged disabled registry and
subchat contracts, and rejects added executables and forged host flags.
Its LOCAL_COORDINATOR_MATCH classification is a source integrity result,
not publisher authentication or Muse-native installation.

## What actually runs

The standalone Python source module runtime/coordinator_review.py implements
two bounded, deterministic source-only operations.

1. **Workgraph review:** validates a supplied task graph (1–32 tasks),
   consistent role IDs, explicit task sources, 1–64-unit budget, independent
   reviewers, prerequisites and cycle freedom. It returns a deterministic
   topological order and holds all external-effect tasks. This is an
   **advisory review**, not an Omnium mission compiler or dispatch authority.
2. **Evidence assertion review:** compares explicitly supplied actor and
   reviewer claims with the same source graph and source digests.
   Completion assertions remain UNATTESTED_ASSERTIONS_ONLY even when
   internally consistent. UNKNOWN_EFFECT requires HOLD; a forged examiner
   PASS cannot advance it. No original provider or recipient was contacted.

Run the self-contained synthetic example on Windows, Linux or macOS:

    python -I -B ./new-coordinator/custom-skills/coordinator_workgraph/run.py --operation demo

Expected result is LOCAL_COORDINATOR_DEMO_PASSED, an ordered two-task graph,
and one held external-effect task. All host/effect flags remain false.

To validate an owner-approved offline graph, provide JSON through
standard input, never via a hidden network tool:

    python -I -B ./new-coordinator/custom-skills/coordinator_workgraph/run.py --operation review < example-workgraph.json

The separate evidence skill accepts a JSON object containing exactly
graph and assertions, via --operation evidence. It limits inputs
to 65,536 bytes, checks duplicate JSON keys and refuses unsafe shapes.
No importer runs caller-provided code.

## Source package contents

- profile/: default-neutral profile files from the existing generic renderer.
- system-files/: independent AGENTS, SOUL, IDENTITY, USER, TOOLS,
  MEMORY, HEARTBEAT, SYSTEM_INSTRUCTIONS, plus CONNECTORS/BROWSER/VOICE
  policy drafts. Nothing in an existing receiving account is overwritten.
- runtime/: runnable graph-review Python code and a snapshot of the
  11 generic role IDs required by the reviewer. No donor runtime.
- custom-skills/: two usable **local** skill scripts with SKILL.md/skill.yaml.
  The package-local skills.yaml entries are all disabled.
- subchats/: intake, dependency-review and acceptance-review folders
  with distinct ROLE, CONTEXT, MEMORY, TOOLS and SUBCHAT.json.
  Native chat IDs are NULL, and no subchat has been spawned.
- hooks/HOOKS.json: disabled. No heartbeat scheduling or cron starts.
- config/host-binding.json: no owner identity or session.
- scripts/doctor.py: standalone **self-hash** readback, not a signed source
  attestation. Re-run the repository inspector for trusted source comparison.
- receipts/COORDINATOR_RECEIPT.json: closed-tree local source hashes and
  explicit native/effect refusals.

## Platform, licensing and native availability

The local reviewer uses Python standard-library only and is intended for
Windows, Linux and macOS. Cross-platform qualifications must be recorded
at an exact source commit with independent source equality and test exits.
This cleanly authored local component does not confer redistribution
rights to any separately sourced engine, connector or model weights.

Native Muse/Hatch and Muse Code are separate host targets. Installing a
file locally or writing status: available to skills.yaml is not proof
that a genuine model selected a skill. Fresh receiving-owner authorization,
actual host registration, model-selected invocation and independent
recipient readback are separate R33.E2E gates. The whole fleet remains
PARTIAL until those are proven.

## Operations and rollback

Use only an absent, disposable directory for staging. On inspection failure,
preserve the exact partial tree and investigate; do not delete existing
host files to obtain a clean result. Upgrade/rollback/uninstall for a
receiving owner's actual Muse profile is not implemented by this pack.
It must be implemented with the supported authenticated host API and
explicit original-owner consent.

The primary next improvement is composing this local review component
with the qualified shared Omnium mission-plan and Continuum recovery
adapters **without duplicating their authority**, and then verifying
original host tool and recipient outcomes in a fresh authorized account.
