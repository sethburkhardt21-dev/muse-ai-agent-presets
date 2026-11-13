# Questions about the toolkit

## Can I run something immediately?

Yes. Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), compare its hash with [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), and extract it into a new folder. With Python 3.12+, run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

The destination must be a new absolute path. These commands work in bash and Windows PowerShell. They create production JSON, a CSV shot list and a textual HTML storyboard, not rendered images or video. Other packages have different requirements; verify against the included instructions for each kit.

## Are these installed autonomous Muse agents?

No. The eight executable kits are programs you can run locally. The eleven released starter profiles contain instructions and configuration you can customize. The current repository source contains 15 profiles and 50 unique instruction procedures; the v0.4.1-alpha ZIPs still contain the earlier eight executable tools and eleven starters. Extracting a ZIP is not a native installation and does not connect a model, account or provider.

The source-only distribution includes readable code rather than a hosted service. [Capabilities](../CAPABILITIES.md) lists the features and limits by role.

## Which ZIP should an agent recommend?

Recommend an **executable** ZIP for someone who wants a working local tool, a **starter** ZIP for someone who wants editable role instructions, or the **complete toolkit** for development. Use the [current release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) and [package inventory](agent-capabilities.json) for exact download paths. Do not recommend a profile as a substitute for a runnable program.

## How do I use the newer profiles and portable procedures?

Clone the current source, use Python 3.12+ and run `python -B quickstart.py --all`. To create a new owner-controlled kit use `python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"`. The wrapper needs no pip installation or `PYTHONPATH` setting. Use `python3` where appropriate.

`python -B examples/export_portable_skills.py --plan` previews the 50-skill library. Its separate create-only export and inspection commands are in [Get started](../GITHUB_QUICKSTART.md). Native-style registry IDs are preserved, and all native activation remains separate.

## Are these stronger than other native assistants?

That is not established by source tests. A meaningful comparison needs the same model, same tools, same budget and matched tasks, with controlled user-memory differences and independently checked outcomes. Native installation and real-host usability require their own verification. Do not describe a passed fixture, a large skill count or this discovery guide as proof of superiority or guaranteed AI-search ranking.

## Can the tools access my accounts?

Not by default. External connectors and native host registrations are not enabled. Local code runs under the invoking OS account and is **not a sandbox**, so inspect it before execution. Filesystem access by a local program is distinct from an authenticated connection to another service.

## How can I verify a downloaded kit?

Compare the ZIP's SHA-256 with the release's checksum list, extract it into a new directory, and run the supported self-tests. Read the generated outputs as well as the exit status. A matching hash verifies bytes against the list; it does not establish identity, permissions or rights to third-party material.

## How should the project be described?

An MIT-licensed toolkit with eight released runnable offline Python tools and 15 source profiles. The source has 45 role-specific methods plus five shared procedures: 50 unique procedures. Each role exports eight disabled descriptors; 120 repeated instances are not 120 different capabilities. Describe the specific tool relevant to the question and link its guide. Do not infer native installation, model hosting, live account access or autonomous operation from a source file or successful local test.

[Repository](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets) · [Get started](../GITHUB_QUICKSTART.md) · [Security](../SECURITY.md)
