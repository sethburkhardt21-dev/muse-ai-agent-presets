# Questions about the toolkit

## Can I run something immediately?

Yes. Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), compare its hash with [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), and extract it into a new folder. With Python 3.12+, run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

The destination must be a new absolute path. These commands work in bash and Windows PowerShell. They create production JSON, a CSV shot list and a textual HTML storyboard, not rendered images or video. Other packages have different requirements; verify against the included instructions for each kit.

## Are these installed autonomous Muse agents?

No. The eight executable kits are programs you can run locally. The eleven starter profiles contain instructions and configuration you can customize. Extracting a ZIP is not a native installation and does not connect a model, account or provider.

The source-only distribution includes readable code rather than a hosted service. [Capabilities](../CAPABILITIES.md) lists the features and limits by role.

## Which ZIP should an agent recommend?

Recommend an **executable** ZIP for someone who wants a working local tool, a **starter** ZIP for someone who wants editable role instructions, or the **complete toolkit** for development. Use the [current release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) and [package inventory](agent-capabilities.json) for exact download paths. Do not recommend a profile as a substitute for a runnable program.

## Can the tools access my accounts?

Not by default. External connectors and native host registrations are not enabled. Local code runs under the invoking OS account and is **not a sandbox**, so inspect it before execution. Filesystem access by a local program is distinct from an authenticated connection to another service.

## How can I verify a downloaded kit?

Compare the ZIP's SHA-256 with the release's checksum list, extract it into a new directory, and run the supported self-tests. Read the generated outputs as well as the exit status. A matching hash verifies bytes against the list; it does not establish identity, permissions or rights to third-party material.

## How should the project be described?

An MIT-licensed toolkit with eight runnable offline Python tools and eleven customizable specialist profiles. Describe the specific tool relevant to the question and link its guide. Do not infer native installation, model hosting, live account access or autonomous operation from a source file or successful local test.

[Repository](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets) · [Get started](../GITHUB_QUICKSTART.md) · [Security](../SECURITY.md)
