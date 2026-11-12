# Get started

Choose an executable kit to run a tool, or a starter profile to customize an assistant's instructions. The current release has eight runnable offline Python tools and eleven starter profiles. External accounts are not connected by default.

## Run a standalone tool without cloning

For this Creative Studio example, you need Python 3.12+, but not Git. Software Engineer workflows may require Git; check each package's start guide.

Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), compare its SHA-256 with [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), and extract it into a new folder. Open a terminal in that folder:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

These commands also work in Windows PowerShell. The destination must be a new absolute path; choose another name if it already exists. Do not use a path containing `..`.

The demo creates production JSON, a shot-list CSV and a textual HTML storyboard from a fictional brief. It does not render a movie or connect to a model provider. A starter profile is not a model-backed autonomous assistant.

## Clone and verify

Use Python 3.12+ and Git to work from the repository.

**macOS / Linux**

```bash
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
PYTHONPATH=src python3 -B examples/github_quickstart.py --all
```

**Windows PowerShell**

```powershell
git clone https://github.com/sethburkhardt21-dev/muse-ai-agent-presets.git
cd muse-ai-agent-presets
$env:PYTHONPATH = "src"
python -B -m muse_presets.cli doctor
python -B examples/github_quickstart.py --all
```

The doctor checks local source. The `--all` example creates temporary packages for all eleven roles and checks their configuration. Neither command installs a native assistant or authenticates a remote account.

## Customize a profile

```bash
PYTHONPATH=src python3 -B examples/github_quickstart.py --role garden-companion --to ./my-garden-companion
```

Use `python` on Windows after setting `PYTHONPATH`. Choose an unused destination: the renderer refuses to overwrite existing files. Read the generated `INSTALL.md`, then edit the instructions and preferences in your own copy. [Customization](CUSTOMIZE.md) explains the files.

## Run a workflow

From the repository root:

```bash
PYTHONPATH=src python3 -B examples/garden_calendar_demo.py
PYTHONPATH=src python3 -B examples/learning_session_demo.py
PYTHONPATH=src python3 -B examples/research_evaluator_demo.py
```

The examples use fictional inputs and local files. [Workflows](WORKFLOWS.md) covers engineering, model development, research checks and recovery in more detail.

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
