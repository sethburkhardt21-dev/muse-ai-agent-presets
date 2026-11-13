# Installation and saved data

Choose whether you want to run a tool or customize a profile. An executable package contains runnable Python code; a starter profile contains instructions and configuration for an assistant you connect separately. Extracting either package does not install a native Muse agent.

## Run a downloaded tool

Download an executable ZIP, check it against the release's `SHA256SUMS.txt`, and extract it into a new directory. Follow its `START_HERE.md` or `INSTALL.md`. Requirements vary: use Python 3.12+, and install Git for workflows that operate on repositories.

The [quickstart](GITHUB_QUICKSTART.md) gives a complete Creative Studio example. Keep generated output and personal data outside the extracted package so you can replace code without losing your work.

## Create a complete source kit

```bash
python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"
```

Use `python3` where appropriate. The wrapper loads local source itself and refuses an existing destination. It creates three separately inspected components:

| Folder | What to customize or inspect |
| --- | --- |
| `system-profile/profile/` | `AGENTS.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, `MEMORY.md`, `OPINION.md`, `VOICE.md`, `SYSTEM_PROMPT.md`, tool and engine guidance. |
| `subchat-scopes/subchats/` | Three role-method drafts with their own context, `MEMORY.md`, tools and disabled `skills.yaml`. |
| `role-skills/` | Three role-specific and five shared descriptors; the proposed registry starts disabled. |

These are source drafts. A memory file is not verified native persistence, a prompt file is not a loaded system message, and a subchat directory is not a registered conversation. Use the [host guide](HOST_COMPATIBILITY.md) for the separate acceptance boundary.

## Create a lightweight profile

The lower-level renderer creates just a profile, not the complete three-component kit above. From the repository root, choose a destination that does not already exist:

```bash
PYTHONPATH=src python3 -B -m muse_presets.cli render --preset learning-coach --to ./my-learning-coach --name "My Learning Coach"
PYTHONPATH=src python3 -B -m muse_presets.cli inspect --path ./my-learning-coach
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. The renderer creates local files only. `inspect` is read-only and reports:

| Result | Meaning |
| --- | --- |
| `LOCAL_MATCH` | Files match the recorded local hashes. |
| `OWNER_CUSTOMIZED` | Personal or instruction files have changed. Your edits are preserved. |
| `REVIEW_REQUIRED` | Files are missing or policy/source content differs from its recorded baseline. |
| `LEGACY_UNVERIFIABLE` | An older receipt cannot establish the baseline. Do not guess or overwrite it. |

The receipt includes preset, playbook, template and generated-file hashes. It can detect changes, but someone able to replace both the files and receipt can forge that match. A hash match does not prove publisher identity, host loading or successful execution.

## Stage an engineering package

```bash
PYTHONPATH=src python3 -B -m muse_presets.engineering_pack --to ./my-engineering-pack
```

This creates a profile, runtime files, skill descriptions and an integrity receipt in a new directory. The local locking implementation supports Windows and POSIX; filesystem durability and retention limits still vary by platform. Read the [Software Engineer guide](../presets/software-engineer/INSTALL.md) before running code or pruning state.

## Preserve personal changes

Keep a copy of the original package and a separate working copy. Perform a three-way comparison of the original files, the new package and your edits before updating. Resolve conflicts deliberately rather than copying a new tree over personal memory, credentials or active configuration.

`AGENTS.md`, `USER.md`, `MEMORY.md`, instructions and preferences serve different purposes. A saved `HEARTBEAT.md` is not an active schedule, a script is not an enabled hook, and a generated chat ID is not a registered conversation. The receiving host decides what it loads and executes.

## Recovery and removal

Keep incomplete-operation evidence until you know whether an action occurred. An unknown external outcome must not be retried automatically. Stop only processes you started and remove only package-owned files whose paths and ownership you have verified.

Updating or removing local code does not cancel remote jobs or remove host registrations. Handle those through the original provider with explicit permission.

[Architecture](ARCHITECTURE.md) · [Host compatibility](HOST_COMPATIBILITY.md)
