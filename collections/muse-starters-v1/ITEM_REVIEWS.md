# Item-level curation — R2

Six pinned entrypoints were read in full through the GitHub connector. This is a bounded review, not an audit of six whole repositories. Upstream code was not run; no upstream item is vendored or admitted. The current implementer performed this review, not an independent judge.

The first network retrieval attempt in the isolated container failed DNS resolution. Those failed attempts are preserved separately and do not count as reviewed items.

## aicodedecode/awesome-muse-skills / skills/daily-briefing/SKILL.md

Revision `faf37c0859ebf627bfcb5225e8057d088691e0ae`; blob `d1b33aeabd516852bd15accdcf0914d9c575bf55`.

[Pinned source](https://github.com/aicodedecode/awesome-muse-skills/blob/faf37c0859ebf627bfcb5225e8057d088691e0ae/skills/daily-briefing/SKILL.md)

**Keep:** A compact morning ritual combines calendar context, important messages and three priorities, with user-adjustable preferences.

**Do not overclaim:** The inspected entrypoint is a conversational briefing, not a scheduling solver. Its explicit separation of briefing from planning is useful and should be preserved.

**Our authored refinement:** Add an optional feasibility branch for requests that actually ask for a day plan: durations, deadlines, fixed events and travel buffers, with explicit overload and deferrals. Reuse known context rather than requiring repeated setup prompts.

**How to compare:** Compare both on an ordinary short briefing as well as an overloaded schedule; a richer schedule is not automatically a better briefing.

## Israelmusondaayliffe/muse-skills / skills/continuity-vault/SKILL.md

Revision `6e9d95c5780df8627f1aae808c3a4776ea3b4ab7`; blob `c3d036db944062cbe09d57e0b748de9d55bb98ef`.

[Pinned source](https://github.com/Israelmusondaayliffe/muse-skills/blob/6e9d95c5780df8627f1aae808c3a4776ea3b4ab7/skills/continuity-vault/SKILL.md)

**Keep:** Distinct handoff, extraction, audit and recall routes preserve source authority and let a new session resume from files rather than memory claims.

**Do not overclaim:** It includes linked validators and a local fallback that were not executed here. Its named host paths and instruction hierarchy cannot become authority in our package.

**Our authored refinement:** Use explicit completed/unknown/not-started/denied effect states and original operation IDs. Hold only ambiguous effects while continuing independent work. Keep the handoff short enough to execute.

**How to compare:** Run a partial-send case with an ambiguous acknowledgement and an unrelated chart task; inspect both no-replay behavior and continued useful work.

## Israelmusondaayliffe/muse-skills / skills/model-evaluation-lab/SKILL.md

Revision `6e9d95c5780df8627f1aae808c3a4776ea3b4ab7`; blob `8b72599e35d0e5afd7d6192a12f44c6b76247c6e`.

[Pinned source](https://github.com/Israelmusondaayliffe/muse-skills/blob/6e9d95c5780df8627f1aae808c3a4776ea3b4ab7/skills/model-evaluation-lab/SKILL.md)

**Keep:** Artifact-state routing reuses frozen plans and recorded outputs, preserves denominators and treats incompatible runs as no decision.

**Do not overclaim:** The entrypoint explicitly relies on judgment for an environment mismatch in its example. Its linked normalization scripts were not reviewed, so no absence claim is made about the full upstream package.

**Our authored refinement:** Provide a narrow executable checker for supplied fixture metrics and comparison metadata; preserve partial cases in denominators and allow explicitly limited host-matched comparison when a managed model is opaque.

**How to compare:** Compare decisions on a real gain, a mismatched-dataset result and an incomplete output set. Review explanation quality separately from arithmetic.

## msitarzewski/agency-agents / engineering/engineering-code-reviewer.md

Revision `8ae6164602c95ca78828b148b9052460ee426885`; blob `fb93291f4b94a8d5687aa1cc0d05741c3352dd22`.

[Pinned source](https://github.com/msitarzewski/agency-agents/blob/8ae6164602c95ca78828b148b9052460ee426885/engineering/engineering-code-reviewer.md)

**Keep:** Actionable review prioritizes correctness, security, maintainability, performance and testing instead of style preferences.

**Do not overclaim:** The inspected persona attributes extensive past experience without evidence. A role description must not become a claim that this assistant has actually conducted those reviews.

**Our authored refinement:** Require exact source locations, a concrete failing example, impact and a minimal repair suggestion; include a clean control to detect false positives and state when review independence is not established.

**How to compare:** Use both faulty and correct small programs with the same contract; a reviewer must find the defect without inventing findings on the control.

## Israelmusondaayliffe/muse-skills / skills/ai-film-studio/SKILL.md

Revision `6e9d95c5780df8627f1aae808c3a4776ea3b4ab7`; blob `22724d62affebcf77836ab73771351fc290d140a`.

[Pinned source](https://github.com/Israelmusondaayliffe/muse-skills/blob/6e9d95c5780df8627f1aae808c3a4776ea3b4ab7/skills/ai-film-studio/SKILL.md)

**Keep:** Deep production stations cover performance, geography, shot direction, reusable asset records and causal iteration while preserving approved creative decisions.

**Do not overclaim:** This is a much broader planning package than our current continuity-review skill. Its linked film advisor, templates and reference closure have not been executed or fully reviewed here.

**Our authored refinement:** For the narrower continuity task, separate intended changes from identity/prop invariants, classify missing observation coverage honestly, and limit repair requests to affected shots. Preserve the upstream depth as an unmet benchmark for the wider Creative Studio family.

**How to compare:** The current text-record fixtures are not visual acceptance. A serious comparison needs actual frames and a complete film brief/shot-packet task with independent visual review.

## obra/superpowers / skills/systematic-debugging/SKILL.md

Revision `22f0b463e7a5e579904dd6211a520321035526f7`; blob `62fc752aaef59a8bbed5d305f4cadc60f8ae07ed`.

[Pinned source](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/systematic-debugging/SKILL.md)

**Keep:** Root-cause tracing, an unaffected control, one hypothesis at a time and reproduction before repair provide a strong general debugging discipline.

**Do not overclaim:** Host-specific examples and an unsupported numerical assertion in the entrypoint must not be inherited as universal facts. Supporting reference techniques were not separately executed here.

**Our authored refinement:** Add exact revision/input/result records and distinct setup-blocked, not-reproduced and reproduced states. Preserve completed tests and use causal evidence rather than a fixed ceremonial sequence for every tiny task.

**How to compare:** Separate a true assertion failure from an import/setup failure and a report no longer reproducible at the current revision; then run the actual owned toy repair.
