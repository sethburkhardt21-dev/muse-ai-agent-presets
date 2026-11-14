# Know what a capability can actually do

Choose an operation by its real mechanism and expected output. A workflow description, a runnable local function, a native tool, an authenticated connector and a verified external effect are different products of evidence. Keeping those distinctions visible lets you do useful work now without pretending unavailable integrations are installed.

## First useful result

Run a harmless local example from the source repository:

```sh
python -B tools/muse_collection.py demo automation-engineer
python -B tools/muse_collection.py workflow-demo pipeline-validation
```

These commands need Python 3.12+ in the source tree, not a connected account. Inspect the returned JSON. The specialist example runs actual bounded calculations on authored input records. The workflow example identifies local stages that ran and the host or human handoffs that did not. `external_actions_performed` remains false and `full_workflow_executed` remains false for the multi-stage workflow.

## Read the capability label

| Label | What it establishes |
| --- | --- |
| Source instruction | A method is available to read and adapt. |
| Local implementation | Code exists for a stated input/output contract. |
| Local test result | Particular cases ran against exact source. |
| Host discovery | A receiving host actually exposed the descriptor or tool. |
| Authenticated invocation | An available provider accepted a call under real permissions. |
| Observed effect | The intended recipient or service returned evidence of the outcome. |

No row automatically establishes the next. A task acceptance ID is not an answer; a completed background task may not have saved the expected artifact; a screenshot of a button is not evidence its action worked.

## Verify

For each real operation record the source/version, actual tool, allowed scope, request identity, expected outcome and readback. Check an original activity or result record where the provider exposes it. If an action may have run but its answer was lost, reconcile its original status before retrying. A caller-provided owner ID, role name or receipt flag cannot substitute for authenticated authority.

Use `python -B tools/collection_compatibility.py` to check this collection's relationship to the original profile methods. It explicitly leaves the combined unique-capability total unset: the 75 task procedures and the preserved 50 role/shared procedures overlap. Tests, role counts and shared descriptors are not measures of native assistant quality.

## Failure and recovery

When a connector is unavailable, finish useful reasoning from supplied material and explain the missing observation. Do not recreate a provider API from a guessed endpoint, ask for raw tokens, or switch to a different account to bypass a denial. When a local program refuses malformed input, that is a local validation result—not proof that a native host refused a permission.

For a Space, verify the runtime that is actually serving the page. A source SDK method or successful type check is not a deployed host capability. Preserve durable operation IDs, result writes and reopen checks before displaying success. For a device or Watch workflow, distinguish capture acknowledgment from task completion and test the actual device route separately.

## Scope and evidence

These boundaries are built into the existing collection exports and their offline result contracts. They do not claim native Muse installation, a universal agent API, live account access or comparative superiority. See [Host compatibility](../HOST_COMPATIBILITY.md), [the specialist quickstart](../collection/SPECIALIST_QUICKSTART.md) and [connector guidance](../CONNECTORS.md). Select only the capabilities needed for the current task; reading a useful method should not become an unnecessary setup project.
