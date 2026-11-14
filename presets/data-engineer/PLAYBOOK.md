# Data Engineering & Database Architect

Design safe data contracts, reconcile incremental records and review query access paths with reproducible offline tools.

## Operating contract
Start with the current task and supplied evidence. These tools produce local reports, not a new assistant identity, scheduler, credential, or permission grant.
Use only available, authorized host tools for external work. Return useful read-only results when an optional provider is missing. Preserve uncertainty and original effect identities.

## Tools and domain methods

### Review a Schema Change Before Migration (`schema-evolution`)
Separate logical compatibility from operational migration safety. Compare column identity, type and nullability before considering a deployment strategy. A nullable addition can be logically additive while still requiring engine-specific lock and application review. For nonempty tables, a new required value needs an explicit backfill contract. Expand, backfill, validate and contract are separate checkpoints; defaults and indexes are not inferred from column names.

Produce added, removed, retyped and nullability-tightened columns; list required backfills; state the observed row count and the limits of a logical-only review. Include a migration sequence, validation queries to be reviewed by the owner, consumer compatibility notes and a rollback boundary. The tool returns a comparison, not executed DDL.

1. Read both schema versions and reject duplicate column identities before comparison.
2. Classify additions, removals, type changes and tighter nullability independently; a rename is not assumed from similar names.
3. Determine whether current rows need values for newly required columns; keep zero-row and nonempty-table cases distinct.
4. Trace application readers and writers, defaults, indexes, foreign keys and engine-specific locking outside the small logical checker.
5. Draft expand/backfill/validate/contract phases with explicit source and target versions; test a disposable database when authorized.
6. Deliver the logical report and actual test evidence separately from migration approval or deployment status.

### Reconcile Versioned Events Without Resurrection (`incremental-pipeline`)
Treat source version as business order and deletion as a durable versioned fact. Group all state and batch records by key/version before changing the candidate state. Equal-version unequal payloads hold the entire batch; identical repeats contribute no extra row. A higher-version tombstone prevents a later-arriving lower version from resurrecting data. Report order-independent batch counts, and distinguish a pure in-memory reconciliation from transactional writes and checkpoint persistence.

Return a newly calculated state, applied keys, stale-event count, duplicate-event count and any conflicting keys. Conflict returns the original state without partial application. Preserve source and batch digests, version semantics and deletion retention requirements for a real pipeline owner. External writes remain false.

1. Freeze the previous state and incoming batch without mutating either supplied object.
2. Validate key uniqueness in the state, integer versions and null-valued tombstones.
3. Detect contradictory same-key/same-version records across the full batch before applying any candidate change.
4. For nonconflicting input select the highest source version, preserving deletion markers as state.
5. Calculate duplicate and stale-event counts independent of arrival order and reconcile every applied key.
6. Hand off the candidate state and conflicts to the existing transaction owner; never mark a database commit from a pure calculation.

### Read a Query Plan Before Changing Indexes (`query-plan-review`)
Separate table scans, index scans, selective searches and temporary sorting from measured cost. A SCAN over a covering index still traverses records, while a SEARCH indicates constrained access; neither alone proves acceptable latency. Preserve unrecognized plan rows rather than classifying them optimistically. Compare candidate indexes using the same data, parameters and measurement conditions, including write overhead and storage. Plan text is version-dependent and must not become an unqualified universal parser.

Return classified supplied plan rows and retained unclassified rows; propose a concrete measurement and index hypothesis only where source evidence supports it. Include exact SQL/parameter identity, engine version, cardinality, before/after latency and write-cost tradeoffs when those are actually observed. performance_proven and query_executed remain false for text-only inspection.

1. Read the actual query, schema and plan from the same engine version; reject an empty plan.
2. Classify recognized SQLite access rows without rewriting or dropping the original text.
3. Distinguish full table access from a covering-index scan, selective search and temporary B-tree sorting.
4. Locate selective predicates, join order, ordering and covering opportunities in the actual SQL.
5. Test one justified index change in an authorized disposable database with representative parameter values.
6. Return observed timings and query correctness separately from the plan classification; retain unknown rows and failed hypotheses.

## Integration and recovery
Keep source inputs immutable. Save the output report and its input digest. A consistent local result is not a provider acknowledgment. Resolve ambiguous effects through the original authority before any retry.
The original eleven-role protocol remains unchanged. This is a real additional toolkit with its own methods and tools, not a renamed starter or live-agent enrollment.
