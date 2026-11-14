# Read a Query Plan Before Changing Indexes — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Separate table scans, index scans, selective searches and temporary sorting from measured cost. A SCAN over a covering index still traverses records, while a SEARCH indicates constrained access; neither alone proves acceptable latency. Preserve unrecognized plan rows rather than classifying them optimistically. Compare candidate indexes using the same data, parameters and measurement conditions, including write overhead and storage. Plan text is version-dependent and must not become an unqualified universal parser.

## Output contract

Return classified supplied plan rows and retained unclassified rows; propose a concrete measurement and index hypothesis only where source evidence supports it. Include exact SQL/parameter identity, engine version, cardinality, before/after latency and write-cost tradeoffs when those are actually observed. performance_proven and query_executed remain false for text-only inspection.

## Choose the right action

### A small table is scanned once.
Check actual row count and latency before recommending another index.

**Avoid:** Do not equate the word SCAN with an automatic performance defect.

### The plan uses a covering index but still scans it.
Record index scan rather than table scan and measure how much of the index is visited.

**Avoid:** Do not relabel a full index traversal as a selective search.

### A temporary B-tree is used for ordering.
Examine ordering requirements, cardinality and whether an existing index can serve the exact order.

**Avoid:** Do not add an index without checking sort semantics and write overhead.

### A plan detail row is unfamiliar or from another version.
Retain it under unclassified and consult that engine version before drawing a conclusion.

**Avoid:** Do not silently treat unknown plan text as a pass.

### A new index makes one benchmark faster but slows writes.
Report both measurements and decide against the actual workload objective.

**Avoid:** Do not publish a universal speedup from a single query sample.

## Worked example (authored, synthetic)

**Input:** Plan rows include SCAN users, SEARCH orders USING INDEX order_id, and a temporary ordering B-tree.

**Method:** Classify each original detail row and identify the missing cardinality and timing evidence.

**Result:** The report contains one table scan, one search and one temporary sort; performance is not declared proven.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A plan contains SCAN tags USING COVERING INDEX tag_name plus an unknown future-format row.

**Method:** Keep the first as an index scan and the second as unclassified.

**Result:** Neither row is dropped, and no execution or latency improvement is claimed.

## Failure diagnosis

### An index recommendation does not change the actual plan.
**Likely cause:** The predicate or collation differs from the indexed expression, or statistics and parameters differ.

**Repair:** Reopen the exact query and plan under the tested version and inspect selectivity.

**Recheck:** The proposed access path appears in the actual rerun or the hypothesis is rejected.

### A supposedly optimized query returns different rows.
**Likely cause:** The rewrite altered filtering, join multiplicity or ordering semantics.

**Repair:** Compare result sets and null/duplicate behavior before accepting latency gains.

**Recheck:** Correctness invariants and representative query outputs are preserved.

### Latency claims cannot be reproduced.
**Likely cause:** The before and after runs used different data, cache state or parameters.

**Repair:** Freeze the workload and record repeated measurements and limitations.

**Recheck:** The comparison cites matching inputs and actual timed runs, not plan labels alone.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return classified supplied plan rows and retained unclassified rows; propose a concrete measurement and index hypothesis only where source evidence supports it. Include exact SQL/parameter identity, engine version, cardinality, before/after latency and write-cost tradeoffs when those are actually observed. performance_proven and query_executed remain false for text-only inspection.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `query-plan-review-r5-standard`, `query-plan-review-r5-edge`, `query-plan-review-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.
