# Reconcile a Spreadsheet to Its Source Records — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Reconciliation proves how source records become workbook values. Match stable record identities before totals, preserve currency and sign conventions, and distinguish a duplicate transaction from a legitimate repeated amount. Use exact decimal or integer-minor-unit arithmetic for monetary fixtures. A total can agree while individual rows are wrong, so compare row completeness and formulas as well as aggregates.

## Output contract

Deliver a reconciliation table with source row IDs, workbook references, matched/missing/duplicate/conflicting records, totals by currency, formula or range findings and proposed corrections. Preserve originals and require the actual requested authority before changing a live workbook.

## Choose the right action

### Two equal amounts have different transaction IDs.
Treat them as distinct unless source evidence establishes a duplicate.

**Avoid:** Do not deduplicate by amount alone.

### The same transaction ID appears twice.
Compare payloads; mark exact repeats separately from conflicting versions.

**Avoid:** Do not sum both or silently choose one conflicting value.

### Currencies differ.
Reconcile separate currency totals or use an explicitly supplied conversion basis and date.

**Avoid:** Do not add unlike currencies as though they were the same unit.

### A formula omits the final source row.
Show the exact range omission and propose the narrow formula correction.

**Avoid:** Do not replace the formula with a hard-coded total merely to make it match.

### The workbook is read-only or external changes are not authorized.
Return a cell-specific correction proposal and keep actual changes not performed.

**Avoid:** Do not claim a workbook was repaired from a report alone.

## Worked example (authored, synthetic)

**Input:** Source transactions A=10.10 USD, B=20.20 USD and C=-5.05 USD should appear once each. Workbook rows contain A,B,B,C.

**Method:** Match IDs before summing; the source total is 25.25 USD and the workbook total 45.45 USD.

**Result:** Report duplicate B and a20.20 USD overstatement. Propose removing the duplicate occurrence only after confirming it is not a separate transaction.

## Edge or recovery example 1 (authored, synthetic)

**Input:** A second source contains A=10 USD and B=10 EUR. The workbook reports 20 USD.

**Method:** Keep totals by currency rather than assuming an exchange rate.

**Result:** The reconciled totals are 10 USD and 10 EUR; the 20 USD aggregate is unsupported without a stated conversion basis.

## Failure diagnosis

### The grand total matches but a row is missing and another doubled.
**Likely cause:** Only aggregate checks were performed.

**Repair:** Reconcile record identities and row amounts before trusting the total.

**Recheck:** Completeness and uniqueness pass independently of the grand total.

### A small monetary discrepancy appears inconsistently.
**Likely cause:** Binary floating-point or mixed rounding rules obscured exact values.

**Repair:** Use integer minor units or Decimal with an explicit rounding policy.

**Recheck:** The same source values produce reproducible totals.

### A repaired workbook still shows the old value.
**Likely cause:** The edit was not committed or readback used a stale sheet version.

**Repair:** Inspect the original provider revision and affected cell before retrying.

**Recheck:** The authoritative workbook reflects the intended change without duplicate edits.

## Preserve for the next turn

Keep source versions, matching keys, original cell references, exact amounts, currency/sign rules and proposed/applied changes. Resume with authoritative readback of the affected rows, not a wholesale workbook rewrite.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `spreadsheet-reconcile-r3-standard`, `spreadsheet-reconcile-r3-edge`, `spreadsheet-reconcile-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.
