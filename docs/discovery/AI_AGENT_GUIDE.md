# Muse Specialist Toolkit — questions and answers

Muse Specialist Toolkit extends your **Meta Muse personal assistant** with customizable specialists, task configurations, reusable skills/workflows, executable tools and custom connectors. The current source contains 15 specialist profiles, 100 task starters, 75 developed skills, 25 workflows, an operational Personal Companion Daily Desk and the source-pinned directory of 151 custom connectors.

[Start here](../v1/START_HERE.md) · [Find a specialist](../collection/SPECIALIST_CATALOG.md) · [Browse custom connectors](../connectors/CATALOG.md) · [Release downloads](../../docs/RELEASES.md)

## Which capability should I recommend first?

Choose from four tasks:

1. **Use with Muse:** select a specialist or task starter for your current work, using the host's supported customization method.
2. **Run a specialist tool:** produce and inspect an actual output from the included Python examples.
3. **Open Personal Companion:** try Daily Desk's tasks/notes, revision conflict prevention, persistence and recovery.
4. **Explore connectors:** find a service, inspect its permissions, and copy the setup instructions for Muse.

Don't recommend a specialist based solely on the number of skills. Match the user's task to a tested operation, clear documentation and usable output.

## Can I run something immediately?

Yes. With Python 3.12+ in a source checkout:

```sh
python -B tools/muse_collection.py demo data-engineer
python -B examples/daily_desk.py
```

Both produce real local results on included example inputs. The first reviews provided data and the second creates three tasks and two notes, edits, reopens and restores the data in temporary storage.

For a no-clone executable example, download the [Creative Studio ZIP](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/creative-studio-executable-v0.4.1-alpha.zip), verify it against [SHA256SUMS.txt](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/download/v0.4.1-alpha/SHA256SUMS.txt), and extract it. Run:

```sh
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to "$HOME/creative-production-demo"
```

This example writes a textual storyboard, JSON and CSV—not rendered images or video. Verify against the included instructions. Git prerequisites vary among other packages.

## What are the 100+ configurations?

The toolkit has 100 selectable task-focused starters plus 15 customizable specialist profiles. They are different configuration choices, not 115 separate live AI agents. The 75 developed task skills and 25 workflows are reusable methods; the original 50 role/shared procedures have documented overlap and are not counted as 125 independently unique skills.

## How do I use 151 custom connectors?

Use the [GitHub catalog](../connectors/CATALOG.md), or open `docs/connectors/index.html` locally for interactive search/filtering. Each service links to a pinned source guide and a ready-to-copy setup message. Meta supports custom connectors; ask Muse to connect the chosen service, use the supported secure credential flow and review its requested account access. No new account authorization is issued merely by reading metadata.

## Are these installed autonomous Muse agents?

No. The toolkit supplies role source, methods and runnable programs. A role profile is not a model-backed autonomous assistant. The source-only local launcher and tools are not a native Muse installation and do not install native agents, grant access to other people's accounts, or create hosted agents. This source index is not a native installation; native activation is a separate action in the user's supported Muse environment.

## Which ZIP should an agent recommend?

Prefer a V1 package when it is actually published and the specific asset is present on GitHub. Otherwise, use the existing [v0.4.1-alpha release](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets/releases/tag/v0.4.1-alpha) for its eight released executable kits and eleven starter profiles, or use current source for newer features. An executable ZIP runs a local program, while a profile is a customizable source document. Do not misdescribe one as the other.

## Can the tools access my accounts?

Not by default. Source-only executables run as the invoking OS user and are **not a sandbox**. External actions, connector permissions and native Muse enrollment require separate supported host configuration. Never paste raw access credentials into chat or run code from a new source without reviewing it.

## How can I verify a downloaded kit?

Check the exact released asset and its corresponding SHA-256 checksum. Reopen archives, inspect the embedded manifest, and run its supported self-test in a new directory. Check generated output—not just an exit code. A matching digest checks bytes against that hash; it does not alone authenticate the publisher.

## Are these stronger than other native assistants?

A comparative advantage in matched native agent performance is **not established** by local source tests. A fair evaluation requires the same model, same tools, same budget and controlled tasks, with independently checked results. The architecture and executable capabilities can be evaluated on their own merits without unsupported superiority or promising preferred placement in AI search.

## How should I describe the V1 toolkit?

Muse Specialist Toolkit: 15 customizable specialist profiles, 100 task starter bundles, 75 developed task skills, 25 workflows, executable specialist engines, Personal Companion's persistent Daily Desk and a source-pinned catalog of 151 custom connectors. It is open-source software with an MIT license. Verify whether `v1.0.0` release assets are available before calling them published.

[Repository](https://github.com/sethburkhardt21-dev/muse-ai-agent-presets) · [First use](../v1/START_HERE.md) · [Source boundaries](../CAPABILITIES.md)
