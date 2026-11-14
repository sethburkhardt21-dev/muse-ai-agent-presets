# Prepare an Automation Without Losing Control of Effects

Check a dependency plan, review unique observed targets and reconcile uncertain prior operations before handing off to the existing executor.

1. **Review a Bounded Automation Plan Before Execution** — load `skills/automation-contract/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
2. **Choose a Locator From Actual Target Observations** — load `skills/selector-resilience/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
3. **Reconcile an Uncertain Operation Without Replaying It** — load `skills/effect-reconciliation/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
4. **Review Against the Actual Brief** — load `skills/bounded-review/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.

## Finish
Return a source-bound execution proposal and concrete blockers; do not dispatch, authenticate supplied evidence or authorize retries.

A workflow is a sequence for Muse to follow, not a background service or dispatch permission.

## Executable local stages

Use `muse_presets.specialist_extensions.evaluate(skill_id, inputs)` with the task-specific input contract for each bound stage. These are real local calculations, not provider dispatch.

- `automation-contract` → preserve its actual returned JSON for the next relevant stage.
- `selector-resilience` → preserve its actual returned JSON for the next relevant stage.
- `effect-reconciliation` → preserve its actual returned JSON for the next relevant stage.

## Input artifacts
- Target-scoped step graph
- Current locator observations
- Original operation evidence

## Output artifacts
- Plan review
- Target review
- Effect-reconciliation report

Try the authored local-stage demonstration: `python tools/muse_collection.py workflow-demo automation-readiness`. The report names unexecuted host/human handoffs and does not claim the complete external workflow ran.
