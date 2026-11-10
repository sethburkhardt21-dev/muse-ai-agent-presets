# Capabilities

The repository includes eleven editable specialist profiles and a growing set of runnable local tools. This page describes **the source available on current main**, not a hosted service or installed native agent. Versioned downloads may contain older source; see [Downloads](RELEASES.md).

## Choose the right starting point

| Specialist | What ships | What it does not claim |
| --- | --- | --- |
| `coordinator` | Workgraph review, independent-assertion checks, offline restart verification, portable Coordinator ZIP export | A scheduler, autonomous delegation or native worker dispatch |
| `software-engineer` | Windows/POSIX Claim Gate, disposable Git repairs with failing and passing tests, independent review, builder-delivery CLI and executable ZIP export | An OS sandbox, unattended agent or deployed application |
| `model-builder` | Small deterministic training examples, grouped held-out evaluation, model artifacts, source-kit export, transactional local install/recovery and verified model execution | GPU training, a production model service or large-model fine-tuning |
| `research-evaluator` | Exact source/excerpt validation, numerical held-out scoring and leakage checks | Authenticated publisher identity, web research retrieval or scientific proof |
| `creative-studio` | Editable media/design methods and disabled skill descriptors — **Template only** | A bundled renderer or a connected creative account |
| `adversarial-verifier` | Review methods and refusal-test patterns — **Template only** as a standalone agent | Autonomous security testing or third-party access |
| `personal-companion` | Editable identity, preference and assistance methods — **Template only** | A native assistant, live reminders or voice services |
| `garden-companion` | SQLite garden/calendar workflow with review, persistence and recovery examples | External calendar writes or authenticated owner identity |
| `learning-coach` | Source-based study sessions, local scoring and review scheduling in SQLite | Clinical approval, native tutoring or external scheduling |
| `claims-adjudicator` | Conservative claim-scope review; shared Evidence Finder and provenance tooling | An independently authenticated verdict |
| `reverse-engineering-researcher` | Comparison of supplied observation records and defensive-review methods | Live device capture, network probing or an attack engine |

The **[shared Evidence Finder](../services/evidence-finder/)** stores local findings and supports recovery after source removal. It is not a twelfth assistant.

## Run something useful

[Step-by-step workflows](WORKFLOWS.md) cover these programs:

| Task | Runnable example |
| --- | --- |
| Check research quotations | `examples/research_evaluator_demo.py` |
| Score held-out predictions | `examples/numeric_evaluation_demo.py` |
| Exercise a repository repair | `examples/software_engineer_workflow_demo.py` |
| Stage and test a disposable build | `examples/builder_delivery_demo.py` |
| Reopen a saved plan safely | `examples/continuum_checkpoint_demo.py` |
| Review an offline handoff | `examples/family_offline_handoff_demo.py` |
| Package a portable model trainer | `examples/export_model_builder_sourcekit.py` |
| Package a Coordinator | `examples/export_coordinator_sourcekit.py` |
| Package the engineering runtime | `examples/export_software_engineer_sourcekit.py` |

The `research-numeric` command returns `LOCAL_NUMERIC_HELDOUT_EVALUATED` for an admitted local case. That reports numerical checks—not the truth of a scientific hypothesis. The machine-readable [capability catalog](../presets/capabilities.json) is checked against the shipped modules and examples on every change.

## Platform and permission boundaries

Use Python **3.12+** and Git. Core source tools work on Windows, macOS and Linux. Swift typechecking requires an installed Swift toolchain on macOS; Windows reports that operation as not run. Some filesystem durability guarantees differ by OS, and unsupported tests are not counted as successful behavior.

Builder tests and reviewed repair cases run under the invoking OS account. They can access its files and network; explicit execution consent is **not a sandbox**. Model training uses small synthetic examples, not a paid provider or GPU job.

Family Link envelopes, Omnium plan previews and restart snapshots are local validation utilities. They do not authenticate another account, reserve a worker, enable a provider or deliver an external action.

[Get started](GITHUB_QUICKSTART.md) · [Workflows](WORKFLOWS.md) · [Security](SECURITY.md)

All kits remain source-only distributions. Local executable tools do not imply a hosted or authenticated native assistant.

## Standalone offline packages

| Package | Guide |
| --- | --- |
| claims-adjudicator | [Build, verify and run](kits/CLAIMS_SOURCEKIT.md) |
| garden-companion | [Build, verify and run](kits/GARDEN_SOURCEKIT.md) |
| learning-coach | [Build, verify and run](kits/LEARNING_SOURCEKIT.md) |
| reverse-engineering-researcher | [Build, verify and run](kits/REVERSE_SOURCEKIT.md) |

These packages include their local engines and tests. They do not require the repository after extraction. The supplied-observation comparison does not access live targets.
