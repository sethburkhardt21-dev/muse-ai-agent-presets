# Review Interface States and Recovery Paths — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Represent the interface as a deterministic declared state graph and keep that specification separate from runtime evidence. Validate state identities and transition endpoints, reject conflicting transitions for the same state/event, and traverse from the initial state. Report required states that are missing, declared states that are unreachable, and reachable nonterminal dead ends. The graph helps expose forgotten loading/error/empty behavior; actual navigation, keyboard, persistence and visual continuity still require a rendered product test.

## Output contract

Return reachable and unreachable states, missing required states, nonterminal dead ends and a scoped declared-graph status. browser_tested is always false. A complete design handoff includes each state purpose, visible feedback, event contract, error recovery, focus behavior and the exact runtime checks still needed.

## Choose the right action

### A required empty or error state is absent.
Report the missing state and define its content, available actions and recovery before claiming complete coverage.

**Avoid:** Do not treat a happy-path success screen as sufficient for every outcome.

### A declared state has no path from the initial state.
Inspect whether a transition is missing or the state is obsolete and reconcile the specification.

**Avoid:** Do not count an unreachable screen as covered simply because it is named.

### A reachable nonterminal state has no outgoing transition.
Identify the blocked user journey and add a deliberate recovery or terminal classification.

**Avoid:** Do not let users become stuck without an intentional completion boundary.

### The same state and event lead to two targets.
Reject the ambiguity and model the guard condition explicitly before implementation.

**Avoid:** Do not let list order decide user-visible behavior.

### Every declared state and transition is consistent.
Report a complete declared graph while retaining browser and accessibility checks as separate work.

**Avoid:** Do not translate graph consistency into a claim of an executed end-to-end test.

## Worked example (authored, synthetic)

**Input:** A flow declares idle, loading, success and error, but only connects idle to loading and loading to success; empty is required.

**Method:** Traverse from idle and compare the declared set with the required checklist.

**Result:** The report identifies missing empty and unreachable error; browser_tested remains false.

## Edge or recovery example 1 (authored, synthetic)

**Input:** Add failure from loading to error and retry from error to idle, with success as a terminal state.

**Method:** Check that every required state is reachable and every reachable nonterminal has a way forward.

**Result:** The declared graph is complete, but real rendering, keyboard behavior and actual network failure still need execution evidence.

## Failure diagnosis

### A failed submission leaves the interface permanently loading.
**Likely cause:** The implementation or specification omitted a failure transition and recovery action.

**Repair:** Add the error path and verify preserved input and a usable retry boundary.

**Recheck:** The error state is reachable and the user has an explicit recovery transition.

### Designers and developers disagree about the same button event.
**Likely cause:** The transition contract contains multiple targets without modeled guards.

**Repair:** Name distinct events or guard outcomes and make the state/event mapping deterministic.

**Recheck:** Each declared state/event pair has one unambiguous transition.

### A complete diagram still produces a broken keyboard flow.
**Likely cause:** Specification coverage was mistaken for runtime and accessibility evidence.

**Repair:** Run the actual keyboard/focus sequence and capture the failing rendered state.

**Recheck:** The final report keeps declared graph checks and observed browser checks separately labeled.

## Preserve for the next turn

Preserve the exact supplied input and tool version, the returned report, any unresolved source assumptions and the next authorized check. Return reachable and unreachable states, missing required states, nonterminal dead ends and a scoped declared-graph status. browser_tested is always false. A complete design handoff includes each state purpose, visible feedback, event contract, error recovery, focus behavior and the exact runtime checks still needed.

## Practice and mechanical checks

Three authored public exercises cover a standard input, an edge condition and changed evidence or recovery. Expected outputs are development examples, not hidden model evaluations.

Practice case IDs: `interaction-state-coverage-r5-standard`, `interaction-state-coverage-r5-edge`, `interaction-state-coverage-r5-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original first-party source and supplied-input calculations. No native Muse performance or superiority claim follows from the source examples.
