# Keep documents useful and recoverable

Treat five states separately: **saved, indexed, consulted, backed up and restored**. A chat acknowledgment proves none of them by itself. Important documents should have a stable owner-controlled home and a recoverable history, rather than existing only as an expiring attachment link or a remembered summary.

## First useful result

Use fictional content for your first check. Ask the assistant, through an actually available file or document tool, to save a brief as a new version in a location you control. Then reopen that exact document and compare its title, three distinctive lines and version. Record the actual path or provider-issued document reference returned by the tool; do not invent one.

Make a second version with one small edit. Keep the first version. Export or back up through the supported provider, then restore the exported copy to a **new** destination and compare the contents. If you cannot restore it, call the backup untested rather than treating the export receipt as disaster recovery.

## A small document record

For each important artifact retain a logical ID, title, source version, last verified time, canonical location, content digest when available, attachment references, ownership and retention preference. Keep search/index status separate from the file's existence. A useful short memory entry can point to this record without duplicating the entire document.

User preferences, private source text, host-managed records and immutable shipped templates are different ownership classes. Keep your working documents outside the repository's managed source files. Never place credentials or private conversations in a public update or source ZIP.

## Verify

A filesystem copy can be checked with an actual hash from the copied bytes; a hosted document needs the provider's original readback and export semantics. A digest proves byte consistency, not author identity, permission or semantic correctness. Reopen after closing the client, and describe the result as a client-reopen test unless a broader restart was actually performed.

For source kits, `python -B tools/collection_compatibility.py` verifies packaged source consistency; it does **not** inspect your own documents or certify host persistence. The [source-and-custody method](../../collections/muse-starters-v1/skills/source-and-custody/SKILL.md) gives a reusable evidence procedure. Do not overwrite managed source simply to place a personal note where the source checker expects a file.

## Failure and recovery

If saved content disappears from an answer, first distinguish a missing file from a retrieval failure. Reopen the canonical document directly using an approved tool. If the original is present but not indexed, give the assistant its exact reference; do not rewrite it to force discovery. If it is missing, preserve the error and recover a verified copy into a new location.

During upgrades use a three-way comparison: the previous template, the new template and your current edited bytes. Preserve unknown files and unresolved conflicts. Do not replace a long-lived MEMORY.md, database or notebook with a fresh template. Concurrent writers and background curation need owner coordination; a folder name is not a durability guarantee.

## Scope and evidence

This guide is an owner-controlled verification procedure, not a guarantee about undocumented VM replacement or service retention. The repository's create-only exporters protect existing destinations; real document service backups, access controls and deletion policies remain provider-specific. [Installation and persistence](../INSTALL_AND_PERSISTENCE.md) explains existing profile behavior. The [Daily Desk design](daily-desk-design.md) turns these requirements into a future structured app contract.
