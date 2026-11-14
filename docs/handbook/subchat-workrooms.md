# Make a subchat a useful workroom

A workroom is a focused conversation with a clear task and references. It is not automatically a separate assistant, privacy boundary, memory store or permission principal. Naming a folder after a chat does not prove that the host reads it when the chat opens.

## First useful result

Where the receiving host supports an ordinary side conversation, create or select one for a fictional project and supply this small packet through its supported interface:

```text
Workroom: North Window document review
Purpose: improve a supplied project outline.
Current task: identify the three largest evidence gaps.
Sources: project-brief-v1; outline-v1.
Selected method: claim-audit.
Output: a review table, not edits to the originals.
Do not: send, publish, schedule or change shared memory.
Next handoff: return findings and the exact source versions to the main task.
```

Ask the assistant to read the packet and perform the task. The first useful result is an evidence table tied to the supplied material, not a claim that a special subagent was installed.

## What each workroom should contain

Keep a concise purpose, current task, selected skills, source index, working notes and handoff. Keep general owner preferences in the receiving owner's existing system rather than cloning personal memory into every room. A workroom's MEMORY.md can be a manually maintained note file, but it is not proof of native indexed memory or isolation.

The existing source-kit generator creates three method-scoped drafts per role, including context, tools, a heartbeat checklist and disabled skills.yaml. These are editable starting points. Use them only through a supported host route, and verify whether they are read when needed. Avoid a large boilerplate load that crowds out the task itself.

## Verify

Ask for a concrete source-based result, then compare it with the original material. If the host exposes read/tool activity, preserve the actual events. Confirm that a handoff names the source revision, performed checks, unfinished work and one next step. Reopen the workroom and ask it to locate the prior result without replaying a consequential action.

For source-only packet checks, run `python -B quickstart.py --all`; it verifies the existing 15-role drafts. This does not prove that native conversations were created or that their startup loader used those files. Read [Resume Work Without Duplicating Effects](../../collections/muse-starters-v1/skills/resume-without-replay/SKILL.md) for interruptions.

## Failure and recovery

If a room seems unaware of its intended role, provide the current packet explicitly and verify the resulting task behavior. Do not manufacture chat IDs, add an unverified startup hook or assume that a role label controls tool access. If two workrooms edit the same file, stop parallel writes, preserve both versions and reconcile through the actual source owner.

A documented room allowlist is only a claim until the real execution boundary enforces it. Shared account tools may remain accessible elsewhere. Use the host's real permission controls, not a caller-supplied string such as controller, to authorize effects. Where isolation is unavailable, avoid putting sensitive material in a supposedly separate room.

## Scope and evidence

These workroom practices improve context and handoffs without requiring a fictional native-agent installation. Source folders, conversations, spawned workers and authenticated tool principals remain distinct. A successful local wrapper check is not native host enforcement. Continue with [Context loading](context-loading.md) and [Source versus host capabilities](source-and-host-capabilities.md).
