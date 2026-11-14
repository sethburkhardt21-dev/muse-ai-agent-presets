# From Product Contract to Verified Handoff

Turn a bounded product request into interface, data and automation contracts that an existing implementation owner can execute.

1. **Review a Bounded Automation Plan Before Execution** — load `skills/automation-contract/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
2. **Review Interface States and Recovery Paths** — load `skills/interaction-state-coverage/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
3. **Review a Schema Change Before Migration** — load `skills/schema-evolution/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
4. **Check a Release Without Confusing Build and Delivery** — load `skills/release-readiness/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.

## Finish
Deliver the inert dependency review, declared state graph, schema-risk report and exact remaining implementation/release checks; never claim deployment.

A workflow is a sequence for Muse to follow, not a background service or dispatch permission.

## Executable local stages

Use `muse_presets.specialist_extensions.evaluate(skill_id, inputs)` with the task-specific input contract for each bound stage. These are real local calculations, not provider dispatch.

- `automation-contract` → preserve its actual returned JSON for the next relevant stage.
- `interaction-state-coverage` → preserve its actual returned JSON for the next relevant stage.
- `schema-evolution` → preserve its actual returned JSON for the next relevant stage.

## Input artifacts
- Approved product scope
- Current interface and data contracts

## Output artifacts
- Step review
- State coverage report
- Schema compatibility report
- Implementation handoff

Try the authored local-stage demonstration: `python tools/muse_collection.py workflow-demo product-to-implementation`. The report names unexecuted host/human handoffs and does not claim the complete external workflow ran.
