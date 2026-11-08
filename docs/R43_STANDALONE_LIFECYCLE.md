# R43 / T07 — Standalone source pack staging, export and lifecycle review

**Status:** LOCAL SOURCE-ONLY. No native Muse account, subchat, skill registry,
tool, connector, scheduler, model, remote machine or owner memory is modified.

T07 composes three existing independent, already tested source components:
T04 system profiles, T05 scoped role-method subchats and T06 disabled skill
descriptors. It does **not** fork their content or create another controller.

## Start from an empty, disposable directory

Use Python 3.10+, from the repository root, with PYTHONPATH=src.

    python -B -m muse_presets.cli dropin-install-plan --preset software-engineer
    python -B -m muse_presets.cli dropin-stage --preset software-engineer --to ./new-engineer-agent --profile-source-sha256 SHA_FROM_PLAN
    python -B -m muse_presets.cli dropin-inspect --path ./new-engineer-agent
    python -B -m muse_presets.cli dropin-upgrade-preview --candidate ./new-engineer-agent --target ./existing-owner-agent
    python -B -m muse_presets.cli dropin-export --path ./new-engineer-agent --to ./generic-engineer-source.zip
    python -B -m muse_presets.cli dropin-uninstall-plan --path ./new-engineer-agent

The parent must already exist. The destination must not exist. No command
accepts a provider owner/chat ID or applies files to a live Hatch host.

Each standalone role contains exact source-pinned system-profile/,
subchat-scopes/ and role-skills/ trees, plus INSTALL_RECEIPT.json. The
receipt binds all three source-component manifests, the same T04 profile
source SHA, the canonical role and its exact three method/skill IDs.
All activation booleans are false. Self-reported receipt hashes do not
represent signatures or permission grants.

## Installation and upgrade semantics

The package stage is **create-only**, with STAGING_INCOMPLETE written
before the first child. The existing component stagers refuse occupied
paths and unsafe symlinks/junctions. Interruption or changed source
leaves a fenced incomplete directory; it is not deleted automatically
and cannot be replayed into the same destination.

Inspect reloads the original source, rechecks the exact closed tree,
all component receipts and the authoritative source-derived policy
bytes. It returns LOCAL_STANDALONE_MATCH, OWNER_CUSTOMIZED,
SOURCE_DRIFT, INCOMPLETE_STAGE or REVIEW_REQUIRED. The last two
are not candidates for activation or export.

Upgrade preview is **read-only** and classifies each existing target file
as CREATE, UNCHANGED, PRESERVE_OWNER_EDIT or REVIEW_CONFLICT.
It preserves receiving-owner identity, memory and preferences. It
does not merge, overwrite, install, or remove anything; unknown
owner files are outside its write scope. A real upgrade requires
authenticated owner approval, provider-supported installation and
verified rollback in T02/T32.

## Export and uninstall

dropin-export creates a deterministic clean SOURCE_ONLY ZIP only from
a pristine, uncustomized source pack and into a new target path. It
rejects duplicate, traversal, symlink, unexpected executable and
source/policy changes. It does not export real receiving-owner memory;
an owner-controlled private-state backup is a separate authorized
operation.

dropin-uninstall-plan is intentionally **non-destructive**. It checks
the package and reports whether owner customizations require a
protected export, but can_delete remains false and owner approval
is mandatory. It does NOT represent a complete uninstall of a
native Muse installation. For a safe rollback, retain the original
source ZIP, its SHA-256 and separately verified owner-state backup,
then stage into another empty temporary directory for comparison.
There is no automatic removal or replacement of a live profile.

This division is deliberate: a local receipt can be forged, and
a filesystem tool has no independent authenticated Hatch identity,
recipient readback, or authority to delete an owner's configuration.

## Verification and remaining acceptance

Source gates: exact 11 independent role packages, every child inspection,
source drift and fabricated native claims refused, occupied destination
and interrupted stage protected, owner memory untouched, preview and
uninstall plan read-only, sanitized export, cross-OS regressions,
A/B/C source parity and private GitHub-main checkpoint.

Native gates still NOT_RUN: supported authenticated personal Hatch
API discovery, actual provider-issued owner/chat/skill IDs, host-loaded
system prompt, model-selected invocation, wrong-owner denial, restart
persistence, recipient readback, and authorized safe upgrade/uninstall.
Source-only GitHub release does not require those live-provider checks.
Do not advertise an installed or natively callable Muse agent until
actual supported provider gates have independently passed.

The owner's first-party source reuse is already authorized. Do not
restart generic redistribution rights debate. Only actual third-party
software/assets, private memory, secrets, history sanitization and
native functionality need appropriate qualification.
