# Architecture

The toolkit separates assistant instructions, local programs and host integrations. You can run a local program without installing an assistant, or adapt a role profile to a host you configure separately.

## Role profiles

`presets/catalog.json` lists the eleven roles. Each role has a `preset.json` for its settings and a `playbook.json` for its working methods. The files in `templates/profile/` provide editable instructions, preferences and memory placeholders.

The renderer creates a new folder rather than replacing an existing assistant. Its receipt records the source and output hashes so later inspection can distinguish unchanged files, personal edits and missing files. A receipt is an integrity record, not proof of identity or permission.

## Local tools

`src/muse_presets/` contains the executable Python modules. The `examples/` directory demonstrates how to use them, and `tests/` covers normal operation, refusals and recovery.

| Component | Responsibility |
| --- | --- |
| Coordinator | Check supplied task plans, dependencies and completion evidence. |
| Software Engineer | Stage reviewed code, track local claims and run repair exercises in disposable repositories. |
| Model Builder | Run small-model examples and check development and held-out results. |
| Research Evaluator | Match excerpts to source text and calculate metrics from supplied predictions and labels. |
| Evidence Finder | Preserve findings and their local receipt history for other tools to read. |
| Role packaging | Combine profiles, working methods and supported local tools into inspectable packages. |

These responsibilities are separate. A plan reviewer does not dispatch workers; a quotation match does not establish scientific truth; and an evidence record does not authorize an external action.

## Host integration

A host supplies the model, authenticated identity, tool permissions and live service connections. The repository's host and connector checks help inspect those boundaries, but do not grant access or register an assistant. Generated profiles are not installed agents. Skills, hooks and connectors are disabled until an integration explicitly enables them.

Personal Muse/Hatch and Muse Code are distinct targets. A manifest for one does not prove compatibility with the other. Read [Host compatibility](HOST_COMPATIBILITY.md) before attempting an integration.

## Data and permissions

Keep personal memory, credentials and host configuration outside the repository. The package owns its defaults; you own your working copies; the host owns its authentication and registrations. Do not merge these into one shared file.

Local programs run under your operating-system account. The toolkit is **not a sandbox**. Review code before execution and validate permissions again at the point of any external action. Hash checks detect changed bytes; they do not provide authentication.

## Where to make a change

Edit a role's playbook for its methods, profile templates for generated instructions, and Python modules for executable behavior. Add a regression test for each changed behavior. Keep the role catalog, package documentation and actual examples consistent.

[Get started](GITHUB_QUICKSTART.md) · [Installation and saved data](INSTALL_AND_PERSISTENCE.md)
