# Reconcile a Data Pipeline Before Delivery

Review schema evolution, reconcile a versioned batch and inspect a supplied query plan without modifying a production database.

1. **Review a Schema Change Before Migration** — load `skills/schema-evolution/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
2. **Reconcile Versioned Events Without Resurrection** — load `skills/incremental-pipeline/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
3. **Read a Query Plan Before Changing Indexes** — load `skills/query-plan-review/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
4. **Test Data Transformations Against Explicit Invariants** — load `skills/data-quality-review/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.

## Finish
Return the schema decision, reconciled candidate state, conflict ledger and query-plan evidence; retain production transaction and retention obligations.

A workflow is a sequence for Muse to follow, not a background service or dispatch permission.

## Executable local stages

Use `muse_presets.specialist_extensions.evaluate(skill_id, inputs)` with the task-specific input contract for each bound stage. These are real local calculations, not provider dispatch.

- `schema-evolution` → preserve its actual returned JSON for the next relevant stage.
- `incremental-pipeline` → preserve its actual returned JSON for the next relevant stage.
- `query-plan-review` → preserve its actual returned JSON for the next relevant stage.

## Input artifacts
- Current/proposed schema
- Prior state and source event batch
- Original query plan

## Output artifacts
- Schema report
- Candidate state
- Query-plan review

Try the authored local-stage demonstration: `python tools/muse_collection.py workflow-demo pipeline-validation`. The report names unexecuted host/human handoffs and does not claim the complete external workflow ran.
