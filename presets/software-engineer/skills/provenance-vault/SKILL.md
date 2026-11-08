---
name: engineering-source-provenance
description: Local source custody, bounded archives, and read-only dependent-quarantine drift reviews.
version: 0.6.0
scope: software-engineer
authority: local-source-only; native-muse-not-registered; no-external-effects
---

# Source Provenance — local capability

Use only for files in an owner-admitted local workspace. This is a reviewed
local source-check candidate, not a license, attestation, native authorization,
remote source-acquisition service or deployment gate.

## Procedure

1. Confirm the exact allowed file path, source owner, task scope and source version.
   Inventory roots must be absolute, non-traversing paths: no symlinked
   root, parent or nested directory (including Windows junctions).
   On platforms with system directory aliases, first obtain an authorized
   canonical realpath (e.g. `Path(root).resolve(strict=True)`); never
   canonicalize an unapproved path to bypass the owner scope.
2. Build and parse a canonical `name@sha256:<digest>` reference. Never accept a bare mutable name.
3. Verify the local file's **actual bytes** and basename against that reference;
   reject missing paths, symbolic links, changed sources or digest mismatch.
4. For donor manifests, require every declared pin to resolve to a previously
   locally verified donor record, then hash the manifest's own exact bytes.
5. Produce a bounded, deterministic read-only source inventory with relative
   paths and source digests. Refuse links, unsupported file types, and excess size.
6. Obtain an actual, already-authorized EvidenceLedger.verify() observation
   from Evidence Finder; produce a **pure local seal** binding its scoped chain
   head to the source inventory, explicit version, and 30-day maximum expiry.
7. Reopen the same ledger and reweigh source using verify_local_source_seal().
   Expired versions, rollback, changed files, changed receipt heads, and
   asserted native/public authority must refuse.
8. From a fresh verified source snapshot, emit an **UNSIGNED** in-toto-shaped
   local Statement/v1 whose subjects are exact relative paths, sizes and hashes.
   Re-verify the statement against current source and the original Finder head.
   No DSSE signature, identity or external witness is created.
9. Prepare and re-verify a read-only, finite source adoption preview that lists
   only existing pinned members and rejects path traversal, duplicate
   members, control characters, invalid UTF-8 and overlong names, and
   unexpected bytes. Preview is never an installation or quarantine action.
10. For a separately authorized **local scratch directory only**, the host
    may pass an action-time local guard callback to
    `stage_local_adoption_quarantine(root, preview, seal, head,
    quarantine_parent=approved_parent, adoption_name="candidate-001",
    authorize_local_write=guard)`. The parent must already exist, be canonical
    and have no symlinked ancestors. The destination MUST be absent.
11. Reopen with `inspect_local_adoption_quarantine(destination)` and confirm
    a locally verified receipt. A failed or interrupted copy leaves an
    incomplete destination for manual reconciliation; never delete or retry it
    without checking the original effect.
12. For synthetic, owner-approved local quarantine only, call
    `export_local_quarantine_archive(quarantine_dir, archive_path=unused_zip,
    authorize_local_export=guard)` to create an OFFLINE local ZIP with bounded,
    uncompressed, digest-pinned members. A local checksum is not a signature.
13. Require the exact resulting SHA-256 when calling
    `inspect_local_quarantine_archive(archive, expected_sha256=digest)` or
    `restore_local_quarantine_archive(archive, restore_parent=owned_parent,
    adoption_name=original_name, expected_sha256=digest,
    authorize_local_restore=guard)`. Restore validates all archive members
    and metadata BEFORE writing; it uses exclusive create-only files.
    An unexpected archive member, ZIP symlink, compression, changed checksum,
    existing target, or interrupted write must refuse. Never auto-retry a
    directory carrying `STAGING_INCOMPLETE` or any unknown partial archive.
14. For donor-drift examination, call
    `assess_local_quarantine_dependency(root, preview, seal, fresh_head,
    quarantine_destination=existing_quarantine)`. It rechecks stored custody
    and its dependency pins, original source bytes, the Evidence Finder scope
    and chain head, and the seal's age. The result is CURRENT, a LOCAL
    INVALIDATION RECOMMENDATION for confirmed source drift, or a REVIEW HOLD
    for incomplete, expired, unknown, changed-evidence or corrupt inputs.
15. Use `review_local_dependent_quarantines(records)` for up to 32 named
    source-bound dependents. Keep current, recommended-invalidation and
    unresolved records separate. These APIs do not change any registry,
    disable a native skill, declare a legal right, delete custody bytes, or
    authenticate the caller's Evidence Finder result.
16. Hand these local observations to the true owner/Claim Gate for
    separately authorized resolution. A self-hash is not an independent
    witness; neither a local boolean guard nor a recommendation may mint
    host-issued identity, a signer or public release permission.

## Local Python usage

From a staged pack, import `runtime/provenance-vault/provenance_vault.py`
in an explicitly scoped Python process. Call `inventory_tree(root)`,
`make_local_source_seal(root, original_finder_verify_result)`, then later
`verify_local_source_seal(root, seal, fresh_finder_verify_result)`. The
Evidence Finder `EvidenceLedger` remains the ONLY persistent receipt chain;
the seal API does not write files, register a scheduler or launch an agent.
It consumes an already-verified local summary from the authorized caller,
without independently authenticating that caller or the summary.

For unsigned statement observations, call
`make_unsigned_local_statement(root, seal, head)` and
`verify_unsigned_local_statement(root, statement, seal, fresh_head)`.
For adoption membership review, call
`preview_local_adoption(root, seal, head, members=["a.txt"])` and then
`verify_local_adoption_preview(root, preview, seal, fresh_head)`.
These read-only calls do not copy files, write a registry or produce signed
attestations. The separate, opt-in `stage_local_adoption_quarantine`
function copies only preview-pinned bytes into an exclusively new local
directory and records the receipt. Inspect the result without the original
source after a restart. Never point it at an original agent's home, existing
memory store, external recipient, shared plugin installation or production
data; no native Muse effect is authorized.

## Denials

Fail on missing source, unexpected name, unverified donor, tampered digest,
symlink, unsupported path, malformed manifest or changed data. A local pin
is not a cryptographic signature. The local seal has no authenticated
threshold signers, no externally trusted anchor, and no independently
verified source ownership. The implemented create-only local quarantine
writer is NOT the original full Vault adoption authority. Local offline
ZIP export/restore does not grant redistribution rights or support native
installation. The original authenticated adoption registry, its WRITING donor
invalidation/recall protocol, signed export provenance, separate
transparency-log protocol, native host wiring, external signing and
independent authorization remain unported. A read-only drift recommendation
is not proof that a revoked adoption has actually been disabled. The local guard callback is
caller-provided and is not an authenticated security principal.

This skill is opt-in and must not enable scheduled tasks or native tools.
