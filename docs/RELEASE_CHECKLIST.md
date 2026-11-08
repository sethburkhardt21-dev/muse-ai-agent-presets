# Release scope and next validation gates

## What public alpha 0.1.0 provides

- [x] New independent public Git history and neutral naming
- [x] Eleven generic role manifests, one separate Evidence Finder service
- [x] `AGENTS`, `SOUL`, `IDENTITY`, `USER`, `TOOLS`, `MEMORY`, `HEARTBEAT`, `PROACTIVE_PREFERENCES`, `SYSTEM_INSTRUCTIONS`, `SUBCHATS`, and `HOOKS` draft templates
- [x] Local create-only rendering and default-denied Family Link previews
- [x] Five bounded offline specialist examples using fictional data
- [x] Source regression tests across Linux and Windows, with symlink-privilege skip recorded on Windows
- [x] GitHub Actions source checks on the committed source
- [x] Documented separation of local source tests from native Muse permissions

## Post-alpha source additions (not part of the immutable alpha tag)

- [x] Source-only, distinct three-method playbooks for eleven roles and offline `render-v3` drafts
- [x] Render-v2 backward-compatible read-only inspector, with new role-policy drift checks
- [x] Read-only neutrality heuristic with explicit nonclaims and negative tests
- [ ] Manual and automated independent review of entire public Git history, licenses and release assets before any higher maturity release

- [x] Separate source-tested Garden Companion SQLite transaction demo and failure-injection regressions; native owner and database integration remain unqualified

## Not claimed in this release

- [ ] Native installation, role skill registration or original Muse invocation
- [ ] Full data/engine transfer from separately maintained private projects
- [ ] Authenticated cross-assistant Family Link messaging
- [ ] Registered heartbeat, hook, scheduler or Space artifact
- [ ] OAuth/MCP/desktop execution credentials or remote host authority
- [ ] Independent result acceptance in an unrelated Muse account
- [ ] Live medical, malware, model-training, or third-party app probing capability

## GitHub source-only release milestones — GITHUB_SOURCE_ONLY

Native host activation is optional; no personal Hatch provider login, live subchat ID or model-selected tool is needed to deliver a tested GitHub source package.

1. **T30 onboarding:** Run the zero-to-one quickstart and all eleven role INSTALL guides from an isolated clean clone, not a historical source checkout.
2. **T31 public content:** Export only the intended role/source files into a fresh, history-free ZIP; screen actual included third-party components, credentials, private names, binary assets and file hashes with the operator's private denylist kept outside public Git.
3. **T32 packages:** Independently extract and verify eleven role packages and their actual local examples on Windows/macOS, with platform skips honestly labeled.
4. **T34 publication:** Use normal, reviewed changes atop the existing public GitHub history. Never wholesale merge or force-push private development history.
5. **T35 final verification:** Read back public source, documentation, CI and package links. Mark unimplemented native, remote or model capabilities OPTIONAL/NOT_RUN, not secretly active.

## Per-feature evidence contract

Record `SOURCE_PRESENT`, `LOCAL_TESTED`, `HOST_WIRED`, `NATIVE_USED` and `INDEPENDENT_USEFUL` independently. Source tests or signed files alone never grant native permissions. Current source-run status is documented in [STATUS.md](STATUS.md); R0–R6 remain the implementation plan in [ROADMAP.md](ROADMAP.md).

## R6 Learning Coach source qualification

- Run `PYTHONPATH=src python examples/learning_session_demo.py` and confirm `LOCAL_NONCLINICAL_STUDY_DEMO_PASSED` with no external effects.
- Run `PYTHONPATH=src python -m unittest discover -s tests -p test_learning_session.py -v`, then the full suite and neutrality audit on the resulting exact source.
- Independently verify wrong-session replay denial, stale source/quote refusal, source-scope separation, no hidden draft writes, one attempt per challenge and rollback after injected SQLite failure.
- Reproduce on supported Windows/macOS hosts as available; preserve actual skip reasons and any unknown host, and do not promote source tests into a claim of native Muse use or instructional quality.
