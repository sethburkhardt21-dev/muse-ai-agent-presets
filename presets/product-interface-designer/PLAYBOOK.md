# Product & Interface Designer

Specify coherent interface states and measure real design-token contrast before handing off implementation and rendered-product review.

## Operating contract
Start with the current task and supplied evidence. These tools produce local reports, not a new assistant identity, scheduler, credential, or permission grant.
Use only available, authorized host tools for external work. Return useful read-only results when an optional provider is missing. Preserve uncertainty and original effect identities.

## Tools and domain methods

### Check Real Color Tokens Before Interface Handoff (`design-token-audit`)
Calculate contrast from the actual foreground and background values, using sRGB linearization and relative luminance rather than visual intuition. Keep pair identity and caller-selected thresholds explicit. Compare the unrounded ratio to the threshold and round only the displayed value. Reject unsupported alpha, gradient and non-sRGB inputs instead of approximating them silently. A token pass says nothing by itself about font size, focus, semantics, keyboard behavior or the real composited screen.

Return every checked pair with token identities, calculated ratio, threshold and pass/fail result. Include an overall calculation result while keeping conformance_certified and rendered_ui_inspected false. The design handoff should also identify real component states and any missing browser, keyboard or visual inspection.

1. Inventory the actual token values and foreground/background combinations rather than checking every color arbitrarily.
2. Confirm opaque six-digit sRGB inputs and an explicit threshold appropriate to the declared use.
3. Linearize channels, calculate relative luminance and compute the lighter/darker contrast ratio.
4. Compare the full-precision ratio with the threshold; show rounded values only as presentation.
5. Inspect actual rendered normal, hover, focus, disabled and error states through a supported browser when available.
6. Deliver token findings and proposed fixes separately from full accessibility conformance and actual rendered-state evidence.

### Review Interface States and Recovery Paths (`interaction-state-coverage`)
Represent the interface as a deterministic declared state graph and keep that specification separate from runtime evidence. Validate state identities and transition endpoints, reject conflicting transitions for the same state/event, and traverse from the initial state. Report required states that are missing, declared states that are unreachable, and reachable nonterminal dead ends. The graph helps expose forgotten loading/error/empty behavior; actual navigation, keyboard, persistence and visual continuity still require a rendered product test.

Return reachable and unreachable states, missing required states, nonterminal dead ends and a scoped declared-graph status. browser_tested is always false. A complete design handoff includes each state purpose, visible feedback, event contract, error recovery, focus behavior and the exact runtime checks still needed.

1. Define the user goal and enumerate actual states, including absence, loading, failure and cancellation where relevant.
2. Choose one initial state, mark terminal states explicitly and freeze the required-state checklist.
3. Describe each transition as origin, event and target; reject missing identities and nondeterministic duplicate events.
4. Traverse reachable states and identify missing requirements, unreachable screens and nonterminal dead ends.
5. Add meaningful recovery transitions and verify that the design preserves entered data and user orientation where required.
6. Exercise the implemented flow in a real browser or device separately; return specification findings without inventing runtime coverage.

## Integration and recovery
Keep source inputs immutable. Save the output report and its input digest. A consistent local result is not a provider acknowledgment. Resolve ambiguous effects through the original authority before any retry.
The original eleven-role protocol remains unchanged. This is a real additional toolkit with its own methods and tools, not a renamed starter or live-agent enrollment.
