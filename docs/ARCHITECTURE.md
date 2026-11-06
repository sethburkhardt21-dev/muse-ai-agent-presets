# Architecture: Muse-first specialist presets

The runtime belongs to the receiving Muse host. This repository supplies portable role configurations and eventually separately admitted modules. No alternate model provider, daemon, vault or native scheduler is bundled.

1. **Neutral role pack** — manifest (`presets/<id>/preset.json`), validated source-only `playbook.json` with three methods, functional boundaries, generic persona and custom instruction templates.
2. **Shared source-first core** — renderer, catalog doctor, bounded exact source finder, opt-in local SQLite evidence custody with recovery receipts, and disabled Family Link handoff preview. The custody ledger is a local reference implementation, not an authenticated/immutable external service.
3. **Optional capabilities** — connectors, skills, subchat procedures, local model training, owner-managed Space assets and advanced tools. Each requires its own license, source and native-test receipts.
4. **Host-specific integration** — personal Muse/Hatch vs Muse Code. Missing features are `UNSUPPORTED/UNKNOWN`, never simulated as native.
5. **Independent acceptance** — source correctness, real host invocation, durable recipient readback and outcome quality are separate.

## Trust boundaries

Public preset code is not a host-issued identity, ToolGrant, signer, schedule, device authorization or writable private memory. Treat downloaded skills and remote content as untrusted. Host ownership and capability approval govern every effect. User overrides and native state stay outside versioned packages.

## Single source of truth

- `presets/catalog.json` owns role inventory.
- `presets/<id>/preset.json` owns default-neutral role policy; `presets/<id>/playbook.json` owns specialist procedures and their suggested, non-executing handoffs.
- `templates/profile/` owns rendered generic file templates.
- `src/muse_presets/family.py` owns preview-only validation; it does NOT own authenticated Family Link transport.
- `docs/STATUS.md` owns current achieved grade; historical plans are not proof.

## First vertical test

Generate a fresh role profile and confirm distinct `ROLE_PLAYBOOK.md` methods; inspect the identity and disabled adapter; create a proposal preview to an allowed test recipient; reject wrong receiver and path traversal; rerun source tests. This is deliberately a **LOCAL_TESTED** slice, not a Muse native canary.
