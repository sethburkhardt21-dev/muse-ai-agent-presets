# From Tokens and States to Interface QA

Measure supplied color pairs, find missing interaction states and review target observations before actual rendered-interface acceptance.

1. **Check Real Color Tokens Before Interface Handoff** — load `skills/design-token-audit/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
2. **Review Interface States and Recovery Paths** — load `skills/interaction-state-coverage/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
3. **Choose a Locator From Actual Target Observations** — load `skills/selector-resilience/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
4. **Inspect a Real Interface for Access Barriers** — load `skills/accessible-ui/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.

## Finish
Return contrast calculations, graph gaps and eligible locator candidates; report browser, keyboard and visual checks only when they actually ran.

A workflow is a sequence for Muse to follow, not a background service or dispatch permission.

## Executable local stages

Use `muse_presets.specialist_extensions.evaluate(skill_id, inputs)` with the task-specific input contract for each bound stage. These are real local calculations, not provider dispatch.

- `design-token-audit` → preserve its actual returned JSON for the next relevant stage.
- `interaction-state-coverage` → preserve its actual returned JSON for the next relevant stage.
- `selector-resilience` → preserve its actual returned JSON for the next relevant stage.

## Input artifacts
- Color tokens and actual pairs
- Required interaction states
- Locator observations

## Output artifacts
- Contrast report
- State coverage report
- Locator review

Try the authored local-stage demonstration: `python tools/muse_collection.py workflow-demo interface-quality`. The report names unexecuted host/human handoffs and does not claim the complete external workflow ran.
