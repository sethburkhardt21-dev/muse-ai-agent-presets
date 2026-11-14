# Organize a Personal Cost Decision — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Compare alternatives on the same time horizon and currency. Separate recurring charges, one-time costs, refundable deposits, uncertain charges and charges already paid. A break-even calculation is meaningful only under the stated use horizon and cancellation assumptions; a lower average cost can still violate an upfront cash limit.

## Output contract

Deliver per-option upfront cash, nonrefundable cost over the chosen horizon, recurring rate, excluded or uncertain charges and feasibility against the stated cash limit. Explain sensitivity to the horizon and show a calculation trail; do not transfer money, cancel a service or offer investment advice.

## Choose the right action

### An annual subscription is cheaper per month.
Compare the actual annual upfront charge and refund terms with the use horizon and cash cap.

**Avoid:** Do not confuse an amortized monthly figure with the amount payable today.

### One option has a refundable deposit.
Include it in upfront cash, exclude it from nonrefundable cost only under an explicit refund assumption, and show that assumption.

**Avoid:** Do not call a deposit free or guaranteed refundable.

### Currencies or tax bases differ.
Use a supplied or currently sourced rate and tax basis, with date; otherwise hold the numeric ranking of incomparable totals.

**Avoid:** Do not add different currencies as though their units match.

### Charges or penalties are unknown.
Present an interval or threshold sensitivity and identify what value would change the decision.

**Avoid:** Do not silently insert zero for an unknown fee.

### An old charge was already incurred.
Separate sunk expenditure from future incremental costs unless the user explicitly asks for lifetime accounting.

**Avoid:** Do not count a past charge twice when evaluating a future choice.

## Worked example (authored, synthetic)

**Input:** For 12 months, A costs 30 per month plus 40 setup; B costs 300 upfront. Currency is identical; cash cap is 320.

**Method:** A costs 400 over the year with 70 initially; B costs 300 initially and in total.

**Result:** Both are feasible; B costs 100 less over 12 months. A retains lower upfront cash use. No transaction was performed.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The same user may stop after three months; B has no refund. The cash cap falls to 250.

**Method:** A costs 130 for three months. B still costs 300 and is outside the upfront cap.

**Result:** A is the only feasible option under the cap and costs 130 for the stated short horizon. Do not quote B as 75 by amortizing its charge.

## Failure diagnosis

### The cheapest option cannot be purchased with available cash.
**Likely cause:** The comparison optimized total cost but ignored liquidity.

**Repair:** Apply the upfront cap before ranking feasible options.

**Recheck:** Feasibility and total cost are reported independently.

### Three months of annual service are shown as one-quarter of the bill.
**Likely cause:** Accrual arithmetic replaced actual billing terms.

**Repair:** Use the full nonrefundable annual charge if the contract requires it.

**Recheck:** The cash-flow schedule reproduces the bill.

### The recommendation flips after a small fee is added.
**Likely cause:** A material unknown was hidden.

**Repair:** Compute the fee threshold at which the ranking changes and label the decision conditional.

**Recheck:** Every uncertain input remains visible in the conclusion.

## Preserve for the next turn

Keep source price dates, units, billing terms, assumptions, horizon and original decision. On resume, refresh changed quotes; preserve actual paid transactions separately from proposed changes.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `decision-budget-r3-standard`, `decision-budget-r3-edge`, `decision-budget-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.
