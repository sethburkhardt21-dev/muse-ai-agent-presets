# Skills and local source verification

Each of fifteen source roles has three distinct role-method skills plus five reusable shared source procedures: **50 distinct source skill procedures**. Each exported role contains eight disabled source descriptors (three specific + five shared), not eight live skills. These are **source-only** `SKILL.md` / `skill.yaml` configurations; native host installation and model-selected execution are not included.

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
| `data-engineering-architect` | [Open](../presets/data-engineering-architect/) |
| `infrastructure-reliability-engineer` | [Open](../presets/infrastructure-reliability-engineer/) |
| `automation-engineer` | [Open](../presets/automation-engineer/) |
| `product-interface-designer` | [Open](../presets/product-interface-designer/) |

Some roles provide local Python engines and executable examples; others provide source descriptions and review methods only. See [Capabilities](CAPABILITIES.md) for the actual distinction.

## Five shared source skills

[Evidence Audit](../skills/shared/evidence-audit/SKILL.md), [Safe Resume](../skills/shared/safe-resume/SKILL.md), [Research Verification](../skills/shared/research-verification/SKILL.md), [Consent And Effects](../skills/shared/consent-and-effects/SKILL.md), [Quality Handoff](../skills/shared/quality-handoff/SKILL.md). These are original source guidance, disabled until the receiving host grants real permissions.

## Verify source kits

```bash
PYTHONPATH=src python3 -B examples/verify_role_packages.py --all
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
```

The role verifier tests clean local package creation, receipt consistency and synthetic source exercises. It does not confirm native host credentials or tool registration. The default `skills.yaml` registries are disabled.

For real permissions and provider APIs, use the receiving platform's documented installation and review process. Generated role/skill metadata alone is not an authorization or a successful invocation.

[Customize](CUSTOMIZE.md) · [Connectors](CONNECTORS.md) · [Extend](EXTENDING_GENERIC_AGENTS.md)

## Portable instruction library

Native-style descriptor IDs use underscores for compatibility with their receiving registry. They are **not** automatically valid Agent Skills folder names. Use the separate standard-format exporter for other compatible assistants:

```bash
python -B examples/export_portable_skills.py --plan
python -B examples/export_portable_skills.py --to "$HOME/my-portable-skills"
python -B examples/export_portable_skills.py --inspect "$HOME/my-portable-skills"
```

No PYTHONPATH setting, dependency install or account is needed. The new directory contains 50 unique hyphen-named folders, each with matching name/description frontmatter and a license declaration. It contains instruction text, not installed native tools or model weights. The exporter preserves all existing owner files and refuses reuse of a destination. Import or read one skill through the receiving assistant's supported flow and verify a harmless task; persistence, routing and native permissions remain host-specific. Standard-format inspection is not evidence that a model selected or executed a skill.

The source [donor ledger](donors/DONOR_RESEARCH.json) records exact primary files and the compatibility decision. No external donor code is executed or redistributed by the exporter.
