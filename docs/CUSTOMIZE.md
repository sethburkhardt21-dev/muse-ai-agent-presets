# Customize an assistant

A role kit is a starting point, not a fixed persona. Copy it into a **new** folder before editing. Keep your original assistant files and private memory outside this repository.

## What you can change

- **Name and identity:** adjust the blank profile and user-facing identity fields.
- **Methods:** refine the role playbook to match the tasks you actually want completed.
- **Preferences and memory:** add only your own data in your private working copy.
- **Subchats:** use the three method-scoped source contracts as patterns for focused tasks.
- **Tools:** choose optional connectors explicitly; the default is disconnected.

The source includes method and skill descriptions, not live native registrations. A native chat ID must come from an authorized receiving host—not a generated template.

## Build a separate role copy

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role coordinator --to "$HOME/my-coordinator"
```

Read the new folder's `INSTALL.md` and editable configuration. The command refuses an occupied destination, so owner memory and existing agent state are not overwritten.

## Subchats and skills

A kit contains three **source-only** scoped subchat methods, each with a distinct context and source-linked skills. The role index remains the source of truth for generated drafts. These folders do not create a native Muse subchat or install an executable skill.

For local skill inspection, see [Skills](SKILLS.md). To add actual source logic, follow [Extend the toolkit](EXTENDING_GENERIC_AGENTS.md).

## Personalization boundaries

- Do not commit private conversations, secrets, addresses or owner-specific IDs to public GitHub.
- A local receipt or file hash does not prove native owner authentication.
- Native installation, remote connectors and scheduling are **optional**, separately authorized integrations.
- Never equate a successful local fixture with a message delivered to another account.

[Get started](GITHUB_QUICKSTART.md) · [Capabilities](CAPABILITIES.md) · [Security](SECURITY.md)
