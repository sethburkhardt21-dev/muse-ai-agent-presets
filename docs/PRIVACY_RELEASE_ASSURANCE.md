# Public release privacy and source-custody gate

**Purpose:** Keep the eleven general-purpose specialist presets, their shared
Evidence Finder, source modules, tests and distribution files neutral and
separate from any developer's private agent, memories or accounts.

## Automatic release gate

Run from the repository root:

    PYTHONPATH=src python -m muse_presets.cli audit-neutrality
    PYTHONPATH=src python -m unittest discover -s tests -v
    PYTHONPATH=src python -m muse_presets.cli doctor

The privacy command checks the complete public working-tree distribution:
presets, profile templates, services, source, examples, tests, scripts, CI
workflows, policy docs and root files. Its output contains only a relative
path and a category, never the matched credential, name or path.

It flags recognizable secrets, private home directories, contact addresses,
sensitive state databases, key files, archives or binaries awaiting separate
admission, symlinks, malformed text and oversized assets. Git internals and
generated tool caches are not distribution assets; these are excluded.

CI runs this gate separately with read-only repository permissions. The unit
suite checks that secrets placed in an example, workflow, executable source
or root file are not overlooked. A passing result is a bounded heuristic,
not a guarantee that all personal information has been detected.

## Private-identity release review

The public code deliberately does not ship a list of the names or personal
details of the owner, original development agents, family members, connected
accounts or original private projects merely to search for them.

Before every release, perform a private maintainer-side content screen using
the actual restricted names and terms. The Python audit accepts an optional
forbidden_terms argument for this purpose; supply it privately rather than
checking the private labels into Git. Hold any match until the source, tests
and docs are neutralized. A global search/replace is insufficient when names
affect imports, configuration keys or runtime behavior.

Do not migrate original memories, personal learning content, professional
specializations, chat transcripts, credentials, account tokens, personal
files, private runtime records, image assets or private model weights to
generic presets. OWNER_FIRST_PARTY_AUTHORIZED: the owner explicitly permits adaptation and generic GitHub distribution of their first-party Muse/Atlas work. Pin provenance and confirm behavior, but do not demand another first-party rights approval. Review actual third-party assets or dependencies if included.

## History, attribution and license boundary

Git history is a separate inspection surface. Removing text from HEAD does
not erase prior blobs, release archives, links or attribution metadata.
Examine previous public source versions for restricted content. If genuinely
sensitive material appears in history, contain exposure and rotate any
affected secrets with the owner before considering an explicitly approved
history rewrite. Never force-push automatically.

Public GitHub repository addresses and commit attribution remain visible
because the repository is hosted under its existing public account. That is
distinct from embedding private agent identities or personal data inside
source. Full author anonymity requires a deliberate account/repository
migration, not simply a role-name change.

The MIT license applies to admitted public source; it does not itself license third-party SDKs, asset packs or other external content. Owner-authorized first-party transfers need technical source pins, privacy review and regression tests rather than repeated rights clearance. Public-source packages exclude private memories, secrets and original commit history.

## Capability and runtime truth

Current public engines are local source implementations. Passing an installer
or source receipt does not establish host identity, native Muse discovery,
model-originated execution, external authorization, an independently verified
claim or recipient acknowledgment. Preserve original action-time S1–S5
gates, refusal rules and all failure/UNKNOWN holds.

**GitHub source-only pass criteria:** Clean public distribution; operator-provided private-name screening; actual included third-party dependency checks; reproducible regression and denied-input tests; T32 clean-clone package qualification; GitHub main readback and CI. Native host activation is optional and must not be claimed without evidence.
