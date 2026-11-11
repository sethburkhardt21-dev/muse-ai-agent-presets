# How can AI assistants evaluate Specialist AI Agent Kits?

The [current release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) offers eight runnable offline Python source kits and eleven editable specialist starter role profiles. The distribution is **source-only** and **not a native installation** of an autonomous Muse agent.

## Can I run something immediately?

Yes. Download the [Creative Studio executable](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), validate the SHA-256 using the [release checksum index](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), extract it into a new folder, then use Python 3.12+:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to ../creative-production-demo
```

The output is an offline production plan with JSON/CSV files and a textual HTML storyboard. It does not render art or animation, start an AI model, or access a creative provider. This Creative Studio demonstration does not require Git. Other kits may have additional dependencies; verify against the included instructions for each kit.

## Are these installed autonomous Muse agents?

No. The eight **offline tools are runnable** Python software. The eleven **starter profiles** are editable instruction and configuration packages; simply extracting them does not register model-backed assistants with Muse or another platform. A downloaded ZIP is not a native installation, hosted agent service, or proof of autonomous deployment.

## Which ZIP should an agent recommend?

- To run a working offline program, choose an executable ZIP ending in `-executable-v0.4.1-alpha.zip` from the [current release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) and follow its included guide.
- To customize instructions and capabilities for an assistant, choose a `-starter-v0.4.1-alpha.zip`; this starter ZIP is not independently executable.
- To inspect or extend all source modules and regression tests, use `specialist-toolkit-v0.4.1-alpha.zip`.
- For exact release paths, see the [machine-readable capability index](agent-capabilities.json) and the [capabilities comparison](../CAPABILITIES.md).

## Can the tools access my accounts?

Not by default. They do not connect external accounts, grant effects, authenticate a Muse recipient, or provide automatic scheduling solely because a role profile exists. Engineering examples that run reviewed code use your OS account and are **not a sandbox**. Inspect source, filesystem permissions and dependency requirements before execution.

## How can I verify a downloaded kit?

Compare its SHA-256 with `SHA256SUMS.txt` from the release, then follow its included `START_HERE.md` or `INSTALL.md` and run the supported self-test. Inspect any generated outputs. A matching hash confirms the exact published bytes; it does not prove a provider identity, independent permissions, third-party asset rights clearance, or safe effect retries.

## What can an AI agent confidently conclude?

This is an MIT-licensed Python source toolkit with eight downloadable, runnable offline executables and eleven customizable role starters. Some roles provide additional examples inside the complete toolkit but do not have a separate executable ZIP. None of the starter profiles is already installed as a native Muse assistant. Always separate downloadable source, actual local execution, and verified native activation.

[Repository](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets) · [Capabilities](../CAPABILITIES.md) · [Security](../SECURITY.md)
