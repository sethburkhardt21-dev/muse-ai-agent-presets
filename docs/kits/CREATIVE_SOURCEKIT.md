# Creative Studio — executable offline production planner

Turn an authored creative brief into a deterministic production package: shot specifications, an exact frame timeline, asset dependencies, continuity checks, a production-task graph, revision differences, and a readable HTML board. The tool checks explicit constraints; it does not invent a story, generate images, animate characters, render video, or certify aesthetic quality.

## Capabilities and limits

| Capability | Delivery |
|---|---|
| Typed creative brief and normalization | Executable locally |
| Scene/shot IDs and frame timeline | Executable locally; IDs supplied by author remain stable |
| Asset dependency graph and production tasks | Executable planning; tasks are not executed |
| Continuity requirements and explicit state transitions | Executable symbolic checks, not visual analysis |
| JSON, CSV and textual HTML storyboard export | Executable, deterministic, create-only |
| Pinned export verification and revision comparison | Executable locally |
| Image/video/animation production | Not implemented by this kit |
| Original animation donor | Source-link-only; not bundled or invoked |
| Independent rights verification, human approval, visual QA | Not run by this tool |
| Native Muse, model, browser, scheduler or external connectors | Disabled/unbound; not installed |

The role's existing preset and playbook are included unchanged as neutral instructions. Their aspirational creative workflows do not establish an installed renderer. The executable scope is the planner described here.

## Build and verify the standalone kit

Requires Python 3.12+ in the source repository:

```bash
PYTHONPATH=src python3 -B examples/export_creative_sourcekit.py --to "$HOME/creative-studio.zip"
PYTHONPATH=src python3 -B examples/export_creative_sourcekit.py --verify ../creative-studio.zip --sha256 <separately-trusted-zip-sha256>
```

PowerShell uses `$env:PYTHONPATH='src'` and `python`. The ZIP destination must be new, under an existing safe parent. The verifier checks bounded exact canonical bytes; it does not decompress an untrusted submitted archive. Existing ZIPs are never overwritten.

After independently checking the ZIP digest, extract it into a new directory. No pip dependencies, Git, credentials, network service, or paid API are needed for the extracted planner:

```bash
python -I -B run.py --operation self-test
python -I -B run.py --operation demo --to /absolute/new/production
python -I -B run.py --operation verify --project /absolute/new/production --sha256 <brief-sha256-from-export>
```

On Windows use a new absolute Windows directory. Both the parent directory and the trusted kit must already exist; the output directory itself must not exist. Store user briefs and outputs outside the immutable kit.

The synthetic example has two scenes, three stable shot IDs, three declared original assets, and 168 frames at 24 fps. It records a lantern changing from `off` to `warm` and a courier changing from carrying `nothing` to carrying `lantern`. A later shot requiring a red coat instead of the unchanged blue coat is rejected. These are symbolic production constraints—not image recognition or proof that an actual rendered character stayed on model.

## Author a production brief

Start with the included `sample-brief.json` (repository: `examples/creative_brief.json`). Copy it outside the kit and edit your copy. JSON objects are closed schemas: unknown fields, duplicate JSON keys, nonfinite values and excessive nesting are refused.

The top-level object contains exactly:

- `schema`: `muse-presets/creative-brief-v1`.
- `project`: `id`, `title`, `summary`, `audience`, `fps`, `aspect_ratio`, `constraints`.
- `assets`: asset declarations with `id`, `kind`, `label`, `reference`, `rights`, `depends_on`, `initial_state`.
- `scenes`: authored sequence of scenes with `id`, `title`, background-asset `location`, and ordered `shots`.

Each shot contains `id`, `description`, `framing`, integer `duration_frames`, `assets`, `depends_on`, `requires`, and `changes`. Framing is `wide`, `medium`, `close`, or `detail`. Asset kinds are `character`, `prop`, `background`, `audio`, or `graphic`. Identifiers are lowercase symbolic labels, not paths or URLs.

Each asset reference is `asset:<its-id>`. No referenced media file is opened. Rights records contain `license` (`original`, `CC0-1.0`, or `CC-BY-4.0`), `credit`, `source`, and explicit `restricted:false`, `person_copy:false`. These fields are **caller declarations, not legal authentication or permission grants**. Unsupported/restricted declarations are rejected, but the software cannot prove the declarations truthful or identify a real person's likeness.

`depends_on` forms a directed acyclic graph; missing dependencies and cycles are refused. Shot dependencies must appear earlier in the authored sequence. Asset declaration order has no significance. Shot/scene order is authored chronology, not guessed by a language model.

`requires` checks the prior symbolic state of a visible asset. `changes` records an intentional state transition after that shot. State keys must already exist in the asset's initial state. An unlisted asset, unknown key, or contradicted requirement is refused with a targeted code. Initial state plus explicit changes determines the final state.

Limits: 256 KiB input; 128 assets; 64 scenes; 256 shots overall; 1,000,000 frames overall; 16 state keys per asset; 32 asset/dependency references per shot. Supported rates are 12/24/25/30/48/50/60 fps. The frame interval is start-inclusive, end-exclusive. Constraints written in prose are retained for human review; only the typed fields are mechanically enforced.

```bash
python -I -B run.py --operation compile --brief /absolute/brief.json --to /absolute/new/production
python -I -B run.py --operation diff --before /absolute/brief.json --after /absolute/revised-brief.json
```

Revision comparison is source-bound and lists added, removed and changed asset, scene and shot IDs, plus explicit scene/shot-order change flags. Timing changes shift downstream frame positions without incorrectly classifying every later authored shot as changed. It does not compare rendered media.

## Actual deliverables

The new project directory contains exactly five files:

1. `BRIEF.json`: normalized authored input and canonical provenance.
2. `PRODUCTION.json`: source digest, half-open frame timeline, asset usage, dependency tasks, symbolic final state and outstanding review gates.
3. `SHOT_LIST.csv`: portable shot table; leading spreadsheet-formula text is neutralized.
4. `STORYBOARD.html`: responsive, escaped textual board, usable offline without JavaScript, fonts or external resources. It is explicitly labeled as text, not drawn or rendered media.
5. `MANIFEST.json`: per-file SHA-256 values and scope claims; written last.

Open the HTML directly to review the shot specifications. Generated tasks remain `NOT_STARTED`; rights, story, production, visual, accessibility and consumer acceptance gates remain `NOT_RUN` until an appropriate independent workflow actually establishes them. Successful export must not be relabeled as visual or native acceptance.

Verification requires the brief SHA-256 from a separately retained export receipt. It reconstructs expected artifacts from that brief and compares exact bytes, rejecting altered artifacts even when their local manifest hashes have been recomputed. Hashes establish byte identity, not authorship, security approval, or a trusted signature.

## Failure and recovery

No overwrites, deletion, automatic retry, in-place migration or background work occurs. A mid-export write failure leaves its partial create-only directory intact and without a completion manifest. Verify reports incomplete; choose a new destination after inspecting the original failure. The tool does not erase partial evidence or user data to manufacture a clean rerun.

The runner checks source hashes, a closed file set, linked paths and import shadows before importing the engine. Inputs and artifacts are bounded regular non-hardlinked files. Native Windows junction and POSIX symlink checks apply where supported; macOS root-owned `/var`, `/tmp`, and `/etc` system aliases are recognized narrowly. Python `-I` is import isolation, **not an OS sandbox**. Hostile concurrent filesystem replacement and compromised Python/OS installations are outside this tool's guarantee.

Upgrades are new independently verified kits and new project directories. Preserve the previous kit, original briefs, digest receipts, and outputs. Recompile an existing brief into a new location to compare across versions; there is no automatic schema migration.

## Repository tests

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -p 'test_creative*.py' -v
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Full repository/source acceptance, independent Windows/macOS execution, public distribution, visual approval, and native installation remain separate evidence boundaries.
