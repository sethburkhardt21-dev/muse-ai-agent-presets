# R46 — Clean GitHub source export and independent privacy gate

This is an **offline public-source snapshot builder**, not a GitHub publisher,
installer, credential issuer or native Hatch/Muse agent deployment.

## Why a separate export?

The private working repository contains internal review-controller source
and historical evidence. Earlier private commits also carried operator
environment details. Publishing that Git history wholesale is unnecessary
for eleven reusable, generic source packages.

The exporter omits the private control/ directory and the six test modules
that require private review-control or donor-custody files. It keeps the eleven consumer
roles, source packages, examples, shared services, documentation, tests,
MIT license and GitHub Actions workflow. It includes no .git history,
host mapping, original agent memory, credentials or runtime session state.

## Create a clean snapshot

From a **frozen and independently verified source checkout/archive**, run:

    python -B scripts/build_public_source.py --root . --to ../generic-agent-public-source.zip

For the owner's release review, pass an operator-controlled denylist file
that is stored OUTSIDE the repository and public ZIP:

    python -B scripts/build_public_source.py --root . --to ../generic-clean-source.zip --forbidden-terms-file ../operator-private-terms.txt

The file contains one exact private identity/host marker per line.
The adapter scans the intended public payload with those private rules,
emits only categorical refusal reasons, and never includes the list or
its values in output files. Do not commit the operator file.

The destination must be new and outside the source tree; overwriting is
refused. It contains PUBLIC_SOURCE_MANIFEST.json listing the SHA-256
digest of every other included file. The ZIP is deterministic for identical
source bytes and excludes metadata from private commit history.

An already extracted public snapshot may be re-exported without changing its
contents: its PUBLIC_SOURCE_MANIFEST.json is reopened and all file hashes
checked before replacement by the freshly computed manifest. A stale or
modified manifest is rejected; if extending source deliberately, update the
package from the canonical GitHub repository rather than trusting a stale
external manifest.

The command accepts source files only from the fixed public allowlist:
README/CHANGELOG/CONTRIBUTING/LICENSE/SECURITY, .gitignore/.gitattributes,
.github, docs, examples, presets, scripts, services, src, templates and
consumer tests. Internal control plus internal-only tests are never copied.
Unexpected top-level directories, symlinks, sensitive filenames, binary
assets, oversized files, private-source-control references and
pre/post-read source changes are refused.

The export reuses the repository's existing public-tree neutrality auditor
over the **actual intended exported files**, not just the working repository.
This is still a heuristic security gate: the release operator must review
all included source, dependencies, examples, names, public Git history,
actual third-party content and CI output before publication.

## Verify the exported source

1. Verify archive SHA-256 and reopen the ZIP with Python's zipfile testzip.
2. Read PUBLIC_SOURCE_MANIFEST.json and verify SHA-256 of every entry.
3. Extract into a new empty, nonshared directory using a path-safe extractor.
4. Run the built-in CLI from the clean export:

       PYTHONPATH=src python -B -m muse_presets.cli list
       PYTHONPATH=src python -B -m muse_presets.cli doctor
       PYTHONPATH=src python -B -m muse_presets.cli audit-neutrality
       PYTHONPATH=src python -B -m unittest discover -s tests -q

   On Windows PowerShell first set $env:PYTHONPATH="src" and use python -B.

5. Run documented local role examples and the create-only
   dropin-install-plan/stage/inspect/export commands in disposable directories.
6. Confirm that no real host provider, model, cron, external connector or
   original agent data was used. Tested local engines are distinct from
   template-only role methods.
7. Compare the frozen candidate on independent Windows/macOS source hosts,
   then land only the approved clean source into the existing public GitHub
   repository as a normal, nonforce commit based on its **own** public
   main branch. Do not merge the private repository history.

## Audit statuses

CLEAN_GITHUB_SOURCE_EXPORTED means only that the chosen source payload
passed packaging and privacy heuristics. It does **not** imply
CLEAN_CLONE_ACCEPTED, GITHUB_PUBLISHED or NATIVE_HOST_VERIFIED.

The current package's source-only status is valid for the owner's
GitHub distribution goal. Native personal Muse/Hatch installation is
optional, NOT_RUN and not a publication blocker. The user has authorized
reuse of their first-party Atlas and Muse code, but actual included
third-party dependencies must still satisfy their own redistribution terms.

T31 owns the clean public-content export gate; T30 owns executable
zero-to-one onboarding documentation; T32 owns eleven role clean-clone
source tests; T34 owns guarded public GitHub publication and independent
readback. These are separate outcomes.
