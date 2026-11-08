# GitHub source release scope — November 2026

## Product deliverable

The owner is publishing eleven neutral, independently downloadable and
source-tested specialist agent kits to GitHub, with reusable local engines,
a shared Evidence Finder, configured source profiles, scoped role-method
subchats, skill descriptors and safe optional connector contracts.

The product is **GitHub source**. An authenticated personal Hatch/Muse native
host, native chat IDs, private skills.yaml activation, actual model-selected
provider tool calls and recipient readback are **not required** for this
release. Do not fabricate those capabilities: they remain NOT_RUN or OPTIONAL.

A clean-clone user may inspect, generate, export, run documented local
examples, and test the source without a Muse account. Installation in a live
Hatch environment is a separate optional integration effort.

## Release gates

- Include **11** separately buildable role kits, one shared Evidence Finder
  service, source-pinned manifests, setup docs and useful local examples.
- A clean GitHub clone, offline quickstart, reproducible source-only ZIP
  export and the tests must work on documented supported OS/Python versions.
- Verify scoped access, source hashes, role boundaries, no destructive
  owner-file mutations, and correct UNKNOWN/timeout/duplicate behavior.
- Document integrations accurately: a provider adapter marked not connected
  is not an installed Desktop Commander, browser CUA, remote shell, Space,
  calendar, plugin, scheduler or native Muse assistant.
- Keep owner-specific private memories, credentials, endpoints, live host
  identifiers and unapproved assets out of the published ZIP and public
  commit history. Create a clean distribution source tree, not a wholesale
  push of the private working repository's historical commits.
- The owner has authorized reuse of first-party Muse and Atlas source.
  Do not block on hypothetical first-party redistribution rights; review
  licenses only for actual third-party components included in the output.
- Cross-machine A/B/C testing is valuable independent SOURCE verification;
  it is not deployment or native-host acceptance. B/C detached worktrees
  are protected and not overwritten to manufacture parity.

## Asana gate mapping

T02: closed as OUT_OF_SCOPE, **not a native PASS**.

T04–T07: accepted completed source milestones; further native activation
proof is not needed to close these GitHub-source tasks.

T08–T29: implement useful, precise source adapters and role-specific
capabilities. No empty file or decorative prompt is sufficient to claim a
working local engine. Unsupported providers must be labeled and default off.

T30: verify setup, configuration, troubleshooting and extension instructions
by actually running commands from a clean clone.

T31: validate public content, privacy, known implementation safety, actual
third-party dependencies and clean source history.

T32: now **GitHub clean-clone acceptance**: reproducible role ZIPs,
documented platform tests and truthful local functionality, not native Muse
skill invocation.

T33: optional integration fixtures and interruption behavior, only for
adapters shipped as working local source.

T34: guarded public GitHub release after accepted source, documentation,
privacy, CI and artifact checks. No destructive force push or private-history
copy.

T35: confirm the eleven role packages are independently usable and the
public repository links and artifacts can be read back.

## No false completion labels

Distinguish LOCAL_SOURCE_TESTED, ROLE_DEMO_VERIFIED, CLEAN_CLONE_ACCEPTED,
GITHUB_PUBLISHED, and NATIVE_HOST_UNVERIFIED. A locally generated prompt,
a registered text descriptor, a simulator, and a live deployed agent are not
interchangeable. Source release can be complete while native activation
remains unverified because native is not part of the selected product.

## Continuation

Resume from the exact last private commit, task checkpoint and source pins.
Prefer existing first-party engine adapters over broad recoding. Perform
targeted red-green regression, full relevant tests, independent A/B/C source
review when supported, guarded private-main fast-forward, then update the
same Asana task. Do not reopen settled native-host or owner-rights debates.
