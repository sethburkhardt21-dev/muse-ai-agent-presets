# Get started

Choose an executable kit to run a tool, or a starter profile to customize an assistant's instructions. The published v0.4.1-alpha has eight runnable offline Python tools and eleven starter profiles. The current source has 15 profiles and 50 unique instruction procedures; its four newer roles are not included in those historical release ZIPs. External accounts are not connected by default.

## Run a standalone tool without cloning

For this Creative Studio example, you need Python 3.12+, but not Git. Software Engineer workflows may require Git; check each package's start guide.

Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), compare its SHA-256 with [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), and extract it into a new folder. Open a terminal in that folder:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

These commands also work in Windows PowerShell. The destination must be a new absolute path; choose another name if it already exists. Do not use a path containing `..`.

The demo creates production JSON, a shot-list CSV and a textual HTML storyboard from a fictional brief. It does not render a movie or connect to a model provider. A starter profile is not a model-backed autonomous assistant.

## Clone and verify the current source

Clone the source from GitHub using Python 3.12+ and Git. Run the commands below in bash or Windows PowerShell; use `python3` on macOS/Linux if that is your installed command.

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
python -B quickstart.py --all
```

No `PYTHONPATH` setting or pip install is needed for this wrapper. It creates and inspects temporary source packages for all 15 roles, with 45 subchat drafts and 120 disabled descriptor instances representing 50 unique procedures. It does not call a model, install native assistants or connect a remote account.

## Customize a profile

```bash
python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"
```

Other source-only role choices include `software-engineer`, `reverse-engineering-researcher` and the four newer specialists in [Capabilities](CAPABILITIES.md). Choose an unused absolute destination. Read the generated `INSTALL.md`; then edit your own identity, instructions and preferences under `system-profile/profile/`. Each of three subchat drafts has separate context and blank memory. Eight descriptors per role start disabled. The copy is yours to customize; do not overwrite owner memory or treat a directory as proof of host installation. See [Installation and saved data](INSTALL_AND_PERSISTENCE.md).

## Export portable instructions

```bash
python -B examples/export_portable_skills.py --plan
python -B examples/export_portable_skills.py --to "$HOME/my-portable-skills"
python -B examples/export_portable_skills.py --inspect "$HOME/my-portable-skills"
```

The create-only exporter writes 50 standard-format instruction folders; inspection checks them against the current source. It does not rename existing native-style registry IDs or install into Muse. See [Skills](SKILLS.md) for formats and failure behavior.

## Run a workflow

From the repository root, these lower-level examples use `PYTHONPATH=src`. In PowerShell, set `$env:PYTHONPATH = "src"` and use `python`:

```bash
PYTHONPATH=src python3 -B examples/garden_calendar_demo.py
PYTHONPATH=src python3 -B examples/learning_session_demo.py
PYTHONPATH=src python3 -B examples/research_evaluator_demo.py
```

The four new specialist fixtures are available through `PYTHONPATH=src python3 -B examples/specialist_engine_demo.py --role automation-engineer`; replace the role ID as documented in [Capabilities](CAPABILITIES.md). The examples use fictional inputs and local files. [Workflows](WORKFLOWS.md) covers engineering, model development, research checks and recovery in more detail.

## Common issues

| Problem | What to do |
| --- | --- |
| `ModuleNotFoundError` | Run from the repository root with `PYTHONPATH=src`. |
| Output already exists | Choose a new directory; do not delete personal files to make a command pass. |
| `PATH_TRAVERSAL_REFUSED` | Use a new absolute output path without `..`. |
| A checksum differs | Stop and check the download or source change. Do not bypass the check. |
| Connector or native skill unavailable | Configure and verify the host integration separately. |
| Platform-specific operation unsupported | Check [Capabilities](CAPABILITIES.md); an unsupported operation is not a passed test. |
| Need a ZIP instead of a clone | Use the [v0.4.1-alpha downloads](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha). |

For code changes, follow [Development](DEVELOPMENT.md). Local execution is not a sandbox; read [Security](SECURITY.md) before running untrusted code.

## Enhance an existing assistant with a task starter

You do not need a replacement identity or native enrollment to read a useful method. Run `python -B tools/muse_collection.py show daily-planner`, then export a selected starter with `python -B tools/muse_collection.py build daily-planner --to "$HOME/daily-planner.zip"`. Read or attach its instructions through your assistant's supported route and apply them to your current request. No model call or account connection happens during export. The [collection quickstart](collection/SPECIALIST_QUICKSTART.md) also demonstrates four executable offline kits and the full downloadable bundle.
