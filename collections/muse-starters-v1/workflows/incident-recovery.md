# From Incident Records to a Bounded Recovery Handoff

Reconstruct the incident, calculate its service budget and size a measured capacity hypothesis while preserving original response authority.

1. **Reconstruct One Incident From Dated Evidence** — load `skills/incident-triage/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
2. **Calculate an Event-Based Reliability Budget** — load `skills/service-objectives/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
3. **Size Capacity With Explicit Utilization and Reserve** — load `skills/capacity-planning/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
4. **Resume Work Without Duplicating Effects** — load `skills/resume-without-replay/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.

## Finish
Return the dated incident timeline, event-ratio budget and capacity calculation with hypotheses, observed effects and a precise next authorized action.

A workflow is a sequence for Muse to follow, not a background service or dispatch permission.

## Executable local stages

Use `muse_presets.specialist_extensions.evaluate(skill_id, inputs)` with the task-specific input contract for each bound stage. These are real local calculations, not provider dispatch.

- `incident-triage` → preserve its actual returned JSON for the next relevant stage.
- `service-objectives` → preserve its actual returned JSON for the next relevant stage.
- `capacity-planning` → preserve its actual returned JSON for the next relevant stage.

## Input artifacts
- Incident events
- Eligible service counts
- Measured capacity and demand

## Output artifacts
- Timeline
- Error-budget report
- Capacity estimate

Try the authored local-stage demonstration: `python tools/muse_collection.py workflow-demo incident-recovery`. The report names unexecuted host/human handoffs and does not claim the complete external workflow ran.
