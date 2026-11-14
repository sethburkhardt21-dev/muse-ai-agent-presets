# Downloads and versions

**Muse Specialist Toolkit V1** brings together the existing public specialist engine source, 15 specialist profiles, 100 task starter bundles, the 75-skill/25-workflow collection plus 50 overlapping original role/shared procedures, Daily Desk and a source-pinned catalog of 151 custom connectors.

For the latest available files and current publication status, use [GitHub Releases](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases) and the [V1 first-use guide](v1/START_HERE.md). The `v1.0.0` version is the target for this product update. A checkout or merged README alone does not establish that the tag and downloadable assets have been published.

## V1 deliverables and release verification

The V1 release package is intended to include portable specialist configurations, a complete source snapshot, runnable local examples, the full connector directory and its source references, manifest digests, and start-here documentation. Inspect the tag, asset names, SHA-256 checksums and source commit before treating a package as the released version.

The 15 specialist configurations and 100 starter bundles are not 115 separately installed Muse agents. A task configuration is an option for an existing assistant. Custom connectors use the host's normal supported setup and permission flow.

## Previous download set — v0.4.1-alpha

[Historical release: v0.4.1-alpha](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) includes **eight runnable executable tools and eleven starter profile ZIPs**. The historical executable packages remain available and their checksums have not been replaced.

| Download | Use it for |
| --- | --- |
| **Executable kit** | Run one of eight runnable Python tools with local example inputs and inspectable outputs. |
| **Starter profile** | Customize one of eleven starter profiles. A starter profile is not a model-backed autonomous assistant. |
| **Complete toolkit** | Inspect the corresponding historical modules, examples and tests. |

For a Creative Studio executable, verify the published [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), extract it and run:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

The sample needs Python 3.12+ but not Git. It generates production documents and a textual storyboard, not rendered video. Other executables may require Git or optional installed components; read their included start guides.

**No native Muse agent is installed by downloading these source-only packages.** A role configuration is not a model-backed autonomous assistant. Native enrollment, credentials and external account authority stay with the receiving host. No paid API or native Muse account is required to run the local demonstrations.

## Earlier releases

- [Eleven starter profiles — v0.2.0-alpha](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.2.0-alpha).
- [Software Engineer executable archive](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/software-engineer-sourcekit-r56-alpha).
- [Initial source archive — v0.1.0-alpha](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.1.0-alpha).

Historical assets are not modified by later source commits. To select by task, see [Capabilities](CAPABILITIES.md) and [Get started](GITHUB_QUICKSTART.md). All example tools run under your invoking OS account and are not operating-system sandboxes.

## Release source and native setup

The GitHub public-source archive is built from a clean, reviewed public tree without private engineering files or history. The historical release includes 11 starter-profile ZIPs. A native Muse account is not required for local demonstrations; no native Muse installation is performed by downloading source or a ZIP.
