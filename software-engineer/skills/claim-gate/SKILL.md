---
name: engineering-claim-gate
description: Atomic local claim, replay refusal, fenced leases, approval holds and UNKNOWN recovery for authorized engineering tasks.
version: 1.1.0
scope: software-engineer
authority: source-only-owner-boundary-required
---

# Engineering Claim Gate

This is a locally runnable component of the Software Engineer pack, NOT proof of native Muse registration. Original-source derived claim state machinery is included and is executable on Windows and POSIX Python hosts.

## Five-seam procedure

1. S1 Source: identify exact task, allowed workspace, source SHA and original payload bytes.
2. S2 Authority: require the host-issued owner, role, task scope, current lease and action-time permission. A local claim is not an authorization.
3. S3 Execution: only a separately authorized host executor may perform the external task. The public CLI never executes the effect.
4. S4 Recovery: one claim per task; changed-byte replay refuses; UNKNOWN stays held until original read-only reconciliation. Use target-side fencing to refuse stale owners.
5. S5 Outcome: independently verify original recipient readback. Never infer success from local claim-state files.

## Local example (Windows/POSIX Python 3.12+)

Create a fresh local state and synthetic source directory first. Then run:

    python3 -I -B runtime/claim-gate/engineering_claim_gate.py --state-dir ./state --scope engineering --claim-id sample-001 claim --source-root ./fixtures --payload patch.txt

Read without re-executing:

    python3 -I -B runtime/claim-gate/engineering_claim_gate.py --state-dir ./state --scope engineering --claim-id sample-001 inspect

For uncertainty, use hold-unknown with a short reason and investigate original receipts; never replay the effect blindly.

## Pruned-history protection (local, not externally signed)

After an operator explicitly prunes terminal Claim Gate records, the
source-only engine writes a per-scope digest-log anchor before removing each
terminal claim. A torn, deleted, empty, unreadable or checksum-mismatched
retention log is held as UNKNOWN and must not authorize a new claim. Do not
automatically migrate or repair an old unanchored retention log. The local
anchor is just a self-hash, **not independent evidence** against someone who
can delete or rewrite both records. Production exact-once effects additionally
require an owner-controlled durable external receipt/fence or disabling
destructive pruning.

All staging and CLI source/state roots reject arbitrary symbolic-link and
Windows-junction ancestry. On macOS only verified /var, /tmp, /etc system
aliases are recognized; this does not constitute owner approval.

## Limits

The source engine uses PORTABLE_LOCAL_FILE_LOCK (Windows msvcrt or POSIX flock).
On Windows, destructive pruning is disabled and power-loss directory persistence
is NOT independently attested. It is not a consensus authority by itself, and no native Muse model, identity, signed source owner, permission, recipient, approval or external effect is verified. Real resource writes must enforce fencing independently. No source-only skill can bypass the actual host permission boundary.

All connectors, subchats, hooks, schedulers, and real effects remain disabled by default. Never overwrite recipient memories.

## R55 reviewed-code engineering workflow

The source-pinned engineering_workflow.py and workflow_worker.py extend this
local engine with an actual disposable Git repository RED -> PATCH -> GREEN
and separately pinned review replay. Keep all three existing host skills
DISABLED until genuine receiving-host admission; this adds no native grant.

Use engineering_workflow.py --help for execute, review and complete. Absolute
paths, exact case/candidate digests, non-test editable-file allowlists and
reviewed-code admission are mandatory. Tests and test IDs remain frozen.
A timeout, incomplete test observation or claimed unfinished operation means
UNKNOWN_EFFECT_HOLD, never blind retry. A successful local demonstration is
GREEN_TESTED, not independently complete. Two original review receipts and
separately observed host/SHA/reviewer bindings are required for COMPLETE.

This runs explicitly reviewed Python code with the operating account's
permissions. It is NOT an OS security sandbox for hostile code and cannot
prove absence of arbitrary test-code file/network effects. Never derive
operator approval or reviewer identity from the candidate's own assertions.
