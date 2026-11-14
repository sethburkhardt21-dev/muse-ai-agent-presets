# A Verified Small Repair

Reproduce an owned-code defect, repair it and inspect the changed behavior.

1. **Reproduce a Defect Before Repairing It** — load `skills/bug-reproduction/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
2. **Repair the Smallest Causal Boundary** — load `skills/minimal-repair/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.
3. **Review a Change for Concrete Failure Paths** — load `skills/code-review/SKILL.md` for this step, carry forward the previous step's real output, and stop before any unapproved external effect.

## Finish
Return the narrow patch and real regression results; preserve any unrun integration checks.

A workflow is a sequence for Muse to follow, not a background service or dispatch permission.
