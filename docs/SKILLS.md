# Skills and local source verification

Each specialist has three method-scoped skill descriptions. These are **source-only** `SKILL.md` / `skill.yaml` configurations; native host installation and model-selected execution are not included.

| Role | Source kit |
| --- | --- |
| `coordinator` | [Open](../presets/coordinator/) |
| `software-engineer` | [Open](../presets/software-engineer/) |
| `model-builder` | [Open](../presets/model-builder/) |
| `research-evaluator` | [Open](../presets/research-evaluator/) |
| `creative-studio` | [Open](../presets/creative-studio/) |
| `adversarial-verifier` | [Open](../presets/adversarial-verifier/) |
| `personal-companion` | [Open](../presets/personal-companion/) |
| `garden-companion` | [Open](../presets/garden-companion/) |
| `learning-coach` | [Open](../presets/learning-coach/) |
| `claims-adjudicator` | [Open](../presets/claims-adjudicator/) |
| `reverse-engineering-researcher` | [Open](../presets/reverse-engineering-researcher/) |

Some roles provide local Python engines and executable examples; others provide source descriptions and review methods only. See [Capabilities](CAPABILITIES.md) for the actual distinction.

## Verify source kits

```bash
PYTHONPATH=src python3 -B examples/verify_role_packages.py --all
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
```

The role verifier tests clean local package creation, receipt consistency and synthetic source exercises. It does not confirm native host credentials or tool registration. The default `skills.yaml` registries are disabled.

For real permissions and provider APIs, use the receiving platform's documented installation and review process. Generated role/skill metadata alone is not an authorization or a successful invocation.

[Customize](CUSTOMIZE.md) · [Connectors](CONNECTORS.md) · [Extend](EXTENDING_GENERIC_AGENTS.md)
