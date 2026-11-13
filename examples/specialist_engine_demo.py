"""Fictional offline examples for the four source-expanded specialist roles."""
from __future__ import annotations
import argparse
import json
from muse_presets.specialist_engines import ROLES, run_fixture

FIXTURES = {
    "data-engineering-architect": {"rows": [
        {"id": "item-a", "value": 3}, {"id": "item-a", "value": 4},
        {"id": "item-b", "value": None}], "key": "id"},
    "infrastructure-reliability-engineer": {
        "events": [True, True, False, True], "target": "0.99"},
    "automation-engineer": {"steps": [
        {"id": "test", "deps": ["build"]}, {"id": "build", "deps": []}]},
    "product-interface-designer": {"screens": [
        {"id": "home", "controls": [
            {"id": "save", "label": ""}, {"id": "cancel", "label": "Cancel"}]}]},
}

def main(argv=None):
    parser = argparse.ArgumentParser(description="Four strictly offline specialist demonstrations")
    parser.add_argument("--role", choices=sorted(ROLES), required=True)
    args = parser.parse_args(argv)
    result = run_fixture(args.role, FIXTURES[args.role])
    if (result["grade"] != "OFFLINE_FIXTURE_ONLY"
            or result["external_effect_authorized"]
            or result["native_registered"]):
        raise ValueError("UNSAFE_LOCAL_RESULT")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
