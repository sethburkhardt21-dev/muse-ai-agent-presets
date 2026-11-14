# Evaluate the result, not a fictional installation

The comparison unit is **a real task performed by the user's existing Muse assistant**. There is no requirement to deploy a separate autonomous system or obtain a nonexistent enrollment certificate.

## Three conditions

1. Baseline: the task and its source material, without the candidate specialization.
2. Upstream: the same task with the relevant legally usable reference instructions, identified by exact revision and item path.
3. Candidate: the same task with this collection's relevant skill and starter.

Use matched model/tool availability, source files, time and cost budgets. Keep conditions in separate contexts where practical, record any unavoidable differences, and avoid leaking one answer into another. Distinguish a run repeated by the same evaluator from genuinely independent review. Label outputs before review so the evaluator is not told which is ours when feasible.

## Score the artifact

For each case, rate correctness, completeness, usefulness, source fidelity, unnecessary questions, effect/permission handling and recovery. Use observable criteria and retain the actual output. Record tool errors, abstentions and costs instead of deleting inconvenient cases. A run that reaches its budget is not automatically a completed task.

`evaluation_cases.json` contains 64 initial task specifications, adverse conditions and rubrics. These are starting points, not a validated benchmark dataset. The current `depth_cases.json` contains 192 concrete public fixtures across all 64 skills. These positive and negative development examples are not hidden holdouts; unseen independently authored cases remain necessary before broad performance claims. The current result fields are null. No source test fills them in automatically.

## First pilot

Start with Daily Planner, Lecture Navigator, Bug Fixer, Research Librarian, Creative Director, Spreadsheet Reconciliation Partner, Truthful Resume Partner and Garden Observation Partner. Use one realistic fixture and one failure/ambiguity fixture for each. Keep a useful unchanged-Muse control. Do not expand a weak pattern merely because it is easy to generate more files.

Promote an improvement only when its actual outputs support the claim. Preserve ties, regressions and uncertain results. An instruction can be source-complete while awaiting this quality comparison; that is not a demand to recreate Muse.


## Concrete comparison packets

There are 192 public cases across 64 skills. Export one without exposing its answer:

```sh
python tools/muse_collection.py challenge daily-briefing-standard --arm plain --to ./plain.zip
python tools/muse_collection.py challenge daily-briefing-standard --arm upstream --to ./upstream.zip
python tools/muse_collection.py challenge daily-briefing-standard --arm candidate --to ./candidate.zip
```

The `TASK.json` bytes are identical in all three packets. Candidate packets omit worked-example answers, evaluator oracles and negative answers. The upstream packet contains pinned references, **not a claim that its required skill package was loaded**: complete its linked dependency set before running. An unqualified upstream arm is missing evidence, not a loss.

Use normal starter packs for everyday work and practice; they intentionally include worked examples and answer files. Do not give those answer-bearing packs to comparison participants. The cases are public development regressions, not secret tests.

A managed Muse interface may not disclose the underlying model. Do not invent it or require a nonexistent installation certificate. Record `model_visibility: "managed-opaque"`, `model: null` and the observed `visible_model_setting`. Such a record can support a **host-matched, model-opaque** comparison, with that limitation stated. The metadata checker cannot authenticate the provider or establish unchanged hidden model weights.

Use separate fresh contexts and identical case ordering within a repetition; randomize the order of the three arms before running. Repeat the same cases in further repetitions, preserve all results, and inspect raw outputs independently before promotion. No scheduled run or provider call is made by this tooling.

Hash the actual supplied input/context pack as `supplied_context_sha256`. Record `memory_mode_observed` from visible settings or explicitly state that no control is exposed. This is not a hash of hidden provider state. Preserve any unavoidable personal-memory differences in the report.

If sampling temperature is not exposed, record `temperature_visibility: "managed-opaque"` and `temperature: null`. Comparison is then limited to observed host settings. The time/output budgets are requested test limits unless their enforcement was actually observed; neither field proves a hidden provider setting.


## R2/R3/R4 comparison scope

There are 192 public concrete cases across 64 skills: 24 R2 cases, 84 R3 cases and 84 R4 cases. Each new skill has a standard, edge and recovery case. Exported plain/upstream/candidate packets share identical task bytes. Both worked examples and semantic adjudication oracles stay outside the candidate challenge. The original 64 broad evaluation specifications remain an inventory, not 64 extra executions.

These cases are public development exercises, not hidden holdouts. A paired Muse run must record actual outputs, visible host settings, source version, permitted tools and any memory differences. An upstream arm needs its pinned complete required context, not an unreviewed partial prompt. No scores or superiority conclusion are prefilled. When no authenticated supported session exists, record NOT_RUN and finish independent source work.
