# Operational depth and practice

## Current scope

The current R4-qualified collection contains 64 depth-expanded skills, zero remaining foundation-only skills, and 192 public practice cases. The 28 R3 expansions cover everyday planning, learning, research, engineering, creative production, project/data work and practical care. Each adds five conditional branches, three repair paths and two examples. See [the R3 wave](../R3_WAVE.json) for exact identifiers and [item reviews](../R3_ITEM_REVIEWS.md) for upstream scope.

## Preserved R2 baseline

The original eight R2 skills and their 24 cases remain byte-identical. Their earlier depth is summarized below:

| Skill | Task-specific depth | Three concrete cases |
|---|---|---|
| Daily briefing | Preserve a short brief; branch into interval-aware planning only when requested | Feasible day, overloaded day, travel buffer |
| Source flashcards | Preserve source version, locators, units and conditions; hold conflicts | Literal facts, condition-sensitive fact, conflicting source |
| Claim audit | Separate artifact scope from claimed completion, and local tests from deployment | Unsupported deployment, mixed scope, historical correction |
| Bug reproduction | Classify setup failure separately from a product defect and a nonreproduction | Reproduced defect, import failure, fixed-current-source |
| Code review | Exact location, concrete counterexample, impact, minimal repair; clean control | Lost final item, correct control, empty-input crash |
| Continuity review | Track invariant vs intentional change and observation coverage | Prop-hand change, intended lighting change, missing evidence |
| Model comparison | Preserve case denominator and compare only eligible conditions | Gain over threshold, environment confound, missing prediction |
| Resume without replay | Resolve individual effect states and preserve original operation IDs | Unknown send, denied action, independently confirmed completion |

Each R2 skill has five decision branches, three failure diagnoses, one worked example and a handoff contract. R3 skills include an additional edge/recovery example and explicit domain-method and output-contract sections. Read only what helps the current task. A 30-second request should not trigger a lengthy intake interview.

## Use the practice checker

A selected starter contains relevant `practice/CASE.json` fixtures and separate `practice/answers/CASE.json` examples. From that starter's directory:

```sh
python -B practice/check_outputs.py check --case practice/daily-briefing-standard.json --output your-response.json
```

Exit 0 means the supplied output met the fixture's narrow mechanical checks. Exit 2 means a failed check or malformed input. The checker performs no model or network call. Exact-answer and fixed-source review fixtures intentionally use closed oracles; this is not a general fact-checker, a security certification or visual judgment.

The required user-facing artifact still matters. A JSON record can pass while its prose is unhelpful. Human review must check usefulness, completeness, unnecessary questions, source fidelity, clarity and actual visual quality where applicable.

## Example provenance

Positive and negative examples are authored synthetic teaching data. The toy total-function repair was exercised locally by a test: the original loses the final element in three of five cases, and the repair passes all five. Those are local code observations, not proof that Muse performed a repair.

The continuity cases use supplied textual frame observations. No screenshot, generated image, video or native Muse session is claimed by these checks.

## Scope ledger

`../DEPTH_STATUS.json` identifies 64 depth-expanded skills and zero foundation-only skills. No broad, independently reproduced Muse superiority result has been established. R3 has 25 bounded upstream entrypoint reviews across 28 mappings; their linked dependencies remain unqualified. The original six R2 item reviews are retained separately. Cross-platform tests are not independent semantic judgment.
