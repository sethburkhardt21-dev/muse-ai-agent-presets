# Optional connectors and Family Link

The toolkit ships **disabled connection contracts**, not a connected shell, browser or cross-account service. Proposed actions are local data until an actual owner-authorized provider is configured.

## Supported source categories

`terminal`, `desktop-commander`, `browser-cua` and `ssh` can be described in role playbooks. They are **not connected** by this repository. GitHub source checkout does not enroll a machine, share a token, start a model or grant tool execution.

The source allowlist covers all fifteen source kits:

`coordinator` · `software-engineer` · `model-builder` · `research-evaluator` · `creative-studio` · `adversarial-verifier` · `personal-companion` · `garden-companion` · `learning-coach` · `claims-adjudicator` · `reverse-engineering-researcher` · `data-engineering-architect` · `infrastructure-reliability-engineer` · `automation-engineer` · `product-interface-designer`.

Their enabled categories depend on each role's existing playbook; the list above does not grant every connector to every role.

## Offline proposal example

```bash
PYTHONPATH=src python3 -B -m muse_presets.cli family-preview --from-role garden-companion --to-role evidence-finder --request-id example-001 --capability find
```

This reports a role-scoped proposal only. There is no native cross-account message, credential exchange, remote recipient acknowledgement or automatic retry.

The offline connector fixture can validate supplied observations and detect changed source hashes. It cannot independently authenticate the observation's author or prove a provider executed it.

## Connecting a real service

Configure provider access separately, obtain the owner's consent and verify the original operation outcome. Do not replay an operation with an unknown effect just because its local receipt is absent. Owner authentication, permission scoping and recipient readback belong to the real receiving platform.

[Customize](CUSTOMIZE.md) · [Source capabilities](CAPABILITIES.md) · [Security](SECURITY.md)
