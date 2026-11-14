# Make the right context available

A useful assistant needs the right working material, not every file you have. A saved document, a searchable document and a document actually consulted for this answer are different things. Begin with a small task packet and expand it only when the task requires more detail.

## First useful result

Create a fictional brief in an owner-controlled location, or attach it through your assistant's supported interface:

```text
Project: North Window
Goal: turn three rough notes into an outline.
Constraint: keep the original uncertainty; do not send or publish anything.
Source marker: context-demo-v1
Notes: prototype exists; testing is incomplete; next review is unscheduled.
```

Ask: **Read the supplied brief, identify the source marker, and produce a three-part outline. Separate the working prototype from the untested claims. Do not change my identity, memory settings or permissions.**

The result should use the actual provided notes, retain the incomplete testing and avoid inventing a scheduled review. This works as a reasoning task without pretending that an agent has installed a new skill or connected another account.

## Choose a manageable context packet

For repeated work, include the current goal, source names/versions, important constraints, selected methods, existing output location, unresolved questions and one next action. Point to large references rather than copying them into every message. A short index can name which source answers which question; it is not proof that all linked sources were loaded.

Keep ordinary task context separate from durable owner preferences. An experiment's temporary output format should not become a permanent personality rule. If the assistant has a supported read tool, ask it to read the exact reference it needs. Otherwise, supply the relevant material through a supported attachment or paste route. Do not invent a file-loading command for a host that does not expose one.

## Verify

Check the output against the supplied brief, not merely against the assistant's claim that it read everything. Ask for a short source-bound paraphrase or a location in the document, then inspect whether the conclusion is actually supported. When a provider exposes activity records, use the real read event as additional evidence. A correct marker alone is a small context check, not proof of broad memory, authorization or all future retrieval.

To start with existing source guidance, read [Scope a Useful Next Result](../../collections/muse-starters-v1/skills/scope-and-route/SKILL.md) and [Keep Sources and Changes Traceable](../../collections/muse-starters-v1/skills/source-and-custody/SKILL.md). Do not load all 75 procedures for a one-page outline.

## Failure and recovery

If the answer misses the brief, first check the exact attachment, path and version. Then narrow the request and explicitly supply the missing section. If the assistant cannot access a file, it should say which source is unavailable and continue any useful work supported by the supplied text. Do not treat a newly created folder or a filename such as SYSTEM_PROMPT.md as evidence that the native host injected it.

Before changing a long-running workflow, preserve the previous packet and output. Reopen the selected source after an edit and compare the relevant lines. A context-refresh test in one conversation or runtime class does not establish the behavior of all subchats, scheduled tasks or spawned workers.

## Scope and evidence

This is a practical source-use procedure, not a claim about undocumented host injection order or context-window sizes. Its source contracts are the existing collection's scope, custody and recovery methods plus the public profile generator. Native context assembly varies by receiving host; qualify it separately. For durable state, continue with [Documents that remain recoverable](durable-documents.md).
