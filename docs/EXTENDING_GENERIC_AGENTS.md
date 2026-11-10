# Extend a specialist kit

Each kit is intentionally editable. Start with a new role package and preserve the original files when experimenting.

## Project structure

- `presets/catalog.json` indexes the eleven available roles.
- `presets/ROLE/playbook.json` represents the methods and optional tool categories for a chosen role. Replace `ROLE` with a real slug such as `garden-companion`.
- `src/muse_presets/role_skills.py` stages and inspects local skill descriptions.
- `src/muse_presets/portable_connectors.py` describes disabled provider contracts and offline observations.
- `src/muse_presets/` contains the executable modules supplied by the toolkit.
- `tests/` contains examples of positive and refusal tests.

## A safe extension workflow

1. Create a new source folder using [Get started](GITHUB_QUICKSTART.md). Never overwrite an owner's saved data.
2. Define one method, its inputs, outputs, default-denied effects and an explicit stopping condition.
3. Add a narrow local function only if the capability needs executable source. A skill description by itself does not install a tool.
4. Add a test with a valid fixture and at least one negative case (changed hash, invalid scope, replay or unsupported platform).
5. Run the doctor and complete test suite, then inspect the resulting package.
6. Keep source changes and recovery instructions in your development workspace; publish only clean, supported files.

## Skills, subchats and connectors

Source kits include editable role profiles, three method-scoped subchat contracts and disabled skill descriptors. They do not have native chat IDs or provider access. The [skills reference](SKILLS.md) explains local validation. The [connector guide](CONNECTORS.md) explains why a proposed call cannot be treated as a successful external action.

For an actual host integration, configure and authenticate it separately. Only enable an external action after verifying the receiving owner, tool permissions and result. There is no default cron scheduler or auto-deployment.

## Validate the extension

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -q
PYTHONPATH=src python3 -B -m muse_presets.cli doctor
PYTHONPATH=src python3 -B -m muse_presets.cli audit-neutrality
```

On Windows PowerShell, set `$env:PYTHONPATH = "src"` and use `python`. Keep private memory, credentials, machine paths and temporary recovery receipts out of public packages. See [security](SECURITY.md) and [releases](RELEASES.md).
