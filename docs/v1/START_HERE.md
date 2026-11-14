# Start here — Muse Specialist Toolkit

**Your Muse. Your Specialists. Your Possibilities.**

Pick your goal. This toolkit combines **15 specialist configurations**, **100 task-focused starters**, a library of skills/workflows, working Python specialist tools, **151 custom connectors**, and Personal Companion's persistent Daily Desk.

Local repository examples use Python 3.12+ on Windows, macOS or Linux. Use `python3` where appropriate. No paid API or signed-in Muse account is needed for local example runs.

## 1. Use with Muse

Explore the [specialist catalog](../collection/SPECIALIST_CATALOG.md) or [100 starter configurations](../../collections/muse-starters-v1/CATALOG.md). A selected starter adds methods to your existing Muse assistant; it preserves your existing identity, memory and access permissions.

From the repository root:

```bash
python -B tools/muse_collection.py specialists
python -B tools/muse_collection.py show frontend-partner
python -B tools/muse_collection.py build frontend-partner --to "$HOME/frontend-partner.zip"
python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"
python -B quickstart.py --all
python -B examples/export_portable_skills.py --plan
```

Read the exported playbook or SKILL.md files and apply the relevant instructions through your Muse's supported customization flow. The source exporter does not sign in, install native agents or change live account settings.

## 2. Run specialist tools

Run a real deterministic tool and inspect its output:

```bash
python -B tools/muse_collection.py check
python -B tools/muse_collection.py demo data-engineer
python -B tools/muse_collection.py workflow-demo pipeline-validation
python -B tools/muse_collection.py kit data-engineer --to "$HOME/data-engineer.zip"
```

The portable kit includes its own runner and example data. It declares which local stages executed and which external or human steps remain. Outputs are reproducible; your current host determines any online integrations.

For a no-clone historical executable, see [release downloads](../RELEASES.md). Git may be required for some engineering executables; Creative Studio's simple local example needs Python 3.12+, but not Git.

## 3. Open Personal Companion

Daily Desk is the working local full-stack Personal Companion workspace: tasks, notes, revision-checked edits, persisted reopen and checked backup/restore into a new store.

Run the entire disposable first-use flow:

```bash
python -B examples/daily_desk.py
```

Expected result: `DAILY_DESK_VERTICAL_SLICE_PASS`, including three tasks, two notes, edited records and a successful restored copy.

To open its actual browser UI on this computer, choose an absolute database path in an existing private directory:

```bash
python -B examples/daily_desk.py --serve --database "$HOME/daily-desk.sqlite"
```

The foreground launcher prints a loopback URL and temporary local-session token. Open that URL on **the same computer**, enter the token and work with your records. On Windows use a real absolute Windows path. For backup and recovery, follow the [Daily Desk guide](../spaces/DAILY_DESK.md). SQLite files and exported archives are plaintext, and this local web interface is not a deployed native Muse Space.

## 4. Explore connectors

[Browse all 151 connectors on GitHub](../connectors/CATALOG.md). To search the directory interactively, open `docs/connectors/index.html` from a checkout or a downloaded toolkit, keeping `app.css` and `app.js` alongside it.

Search by name, service, category or specialist. Each card includes the original version-pinned guide, access prerequisites, and a copy-ready setup message.

Connect through Muse's supported secure custom-connector workflow, not by sharing credentials in chat. Review service permissions and approve important actions when requested. [Full connector guide](../connectors/README.md).

## Troubleshooting

Confirm the Python version, current working directory and writable output directory. Create-only exporters refuse existing paths. A configuration is not account authorization; the receiving host determines which operations are available. Consult the [capability guide](../CAPABILITIES.md), [full repository quickstart](../GITHUB_QUICKSTART.md), or the [issue tracker](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/issues).

After the release, review the [30-day adoption assessment](POST_RELEASE.md) before expanding the catalog or commissioning fourteen more specialist workbenches.
