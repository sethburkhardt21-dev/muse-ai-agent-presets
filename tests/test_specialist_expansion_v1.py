"""Source-only four-role expansion contract. No native host activation."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

from muse_presets.catalog import ROOT, load_registry, validate_catalog
from muse_presets.playbooks import load_playbook, validate_playbook
from muse_presets.standalone_pack import (plan_standalone_pack, stage_standalone_pack,
                                          inspect_standalone_pack)

NEW_ROLES = (
    "data-engineering-architect",
    "infrastructure-reliability-engineer",
    "automation-engineer",
    "product-interface-designer",
)
SHARED = ("evidence_audit", "safe_resume", "research_verification",
          "consent_and_effects", "quality_handoff")


class SpecialistExpansionContract(unittest.TestCase):
    def test_all_fifteen_roles_keep_existing_order_and_add_four(self):
        names = load_registry()["presets"]
        self.assertEqual(len(names), 15)
        self.assertEqual(len(set(names)), 15)
        self.assertEqual(names[-4:], list(NEW_ROLES))
        self.assertEqual(validate_catalog(), [])

    def test_four_methods_are_distinct_and_have_evidence_refusals(self):
        for role in NEW_ROLES:
            with self.subTest(role=role):
                from muse_presets.catalog import load_preset
                config = load_preset(role)
                book = load_playbook(role)
                self.assertEqual(validate_playbook(book, config), [])
                self.assertEqual(len({x["id"] for x in book["methods"]}), 3)
                for m in book["methods"]:
                    self.assertGreaterEqual(len(m["evidence"]), 2)
                    self.assertTrue(m["stop_rule"])
                    self.assertIn(m["handoff_to"], config["family_link"]["suggested_receivers"])

    def test_role_packages_include_full_agent_home_and_isolated_subchat_memory(self):
        for role in (*NEW_ROLES, "coordinator"):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / "new-role"
                pin = plan_standalone_pack(role)["profile_source_sha256"]
                stage_standalone_pack(target, role, expected_profile_source_sha256=pin)
                summary = inspect_standalone_pack(target)
                self.assertEqual(summary["status"], "LOCAL_STANDALONE_MATCH")
                self.assertFalse(summary["native_installed"])
                profile = target / "system-profile" / "profile"
                for doc in ("AGENTS.md", "IDENTITY.md", "SOUL.md", "MEMORY.md",
                            "USER.md", "OPINION.md", "VOICE.md", "TOOLS.md",
                            "HEARTBEAT.md", "SYSTEM_INSTRUCTIONS.md",
                            "SYSTEM_PROMPT.md", "DOORS.md", "ENGINE_MATRIX.md"):
                    self.assertTrue((profile / doc).is_file(), f"{role}: {doc}")
                rooms = target / "subchat-scopes" / "subchats"
                self.assertEqual(len(list(rooms.iterdir())), 3)
                for room in rooms.iterdir():
                    for name in ("AGENTS.md", "MEMORY.md", "CONTEXT.md",
                                 "TOOLS.md", "skills.yaml", "HEARTBEAT.md"):
                        self.assertTrue((room/name).is_file())
                    self.assertIn("version: 1", (room/"skills.yaml").read_text())
                skills = list((target/"role-skills"/"custom-skills").iterdir())
                self.assertEqual(len(skills), 8)
                for skill in skills:
                    body = (skill/"SKILL.md").read_text(encoding="utf-8")
                    self.assertTrue(body.startswith("---\n"), skill)
                    self.assertIn("description:", body)
                    descriptor = (skill/"skill.yaml").read_text(encoding="utf-8")
                    self.assertIn("include_in_prompt: false", descriptor)
                registry = (target/"role-skills"/"config"/"skills.yaml").read_text()
                self.assertEqual(registry.count("status: disabled"), 8)
                self.assertNotIn("native_installed: true", registry)
                with self.assertRaises(FileExistsError):
                    stage_standalone_pack(target, role)

    def test_50_unique_sourced_skills_not_120_distinct_promises(self):
        from muse_presets.role_skills import plan_role_skills, skill_id
        names = load_registry()["presets"]
        skill_ids = set(SHARED)
        for role in names:
            for m in load_playbook(role)["methods"]:
                skill_ids.add(skill_id(role, m["id"]))
            plan = plan_role_skills(role)
            self.assertEqual(set(plan["shared_skill_ids"]), set(SHARED))
            self.assertEqual(len(plan["skill_ids"]), 3)
        self.assertEqual(len(skill_ids), 50)

    def test_four_executable_offline_engines_and_adverse_inputs(self):
        from muse_presets.specialist_engines import run_fixture
        fixtures = {
            "data-engineering-architect": ({"rows": [{"id": "a", "value": 1}, {"id": "a", "value": 2}],
                                            "key": "id"}, "duplicate_count", 1),
            "infrastructure-reliability-engineer": ({"events": [True, True, False, True],
                                                      "target": "0.99"}, "failures", 1),
            "automation-engineer": ({"steps": [{"id": "build", "deps": []},
                                              {"id": "test", "deps": ["build"]}]}, "order", ["build", "test"]),
            "product-interface-designer": ({"screens": [{"id": "home", "controls": [
                 {"id": "save", "label": ""}]}]}, "missing_control_labels", 1),
        }
        for role, (payload, field, expected) in fixtures.items():
            with self.subTest(role=role):
                actual = run_fixture(role, payload)
                self.assertEqual(actual["grade"], "OFFLINE_FIXTURE_ONLY")
                self.assertEqual(actual[field], expected)
                self.assertEqual(actual, run_fixture(role, payload))
                self.assertFalse(actual["external_effect_authorized"])
                with self.assertRaises(ValueError):
                    run_fixture(role, [])
        with self.assertRaises(ValueError):
            run_fixture("automation-engineer", {"steps": [{"id": "a", "deps": ["b"]},
                                                           {"id": "b", "deps": ["a"]}]})
        with self.assertRaises(ValueError):
            run_fixture("data-engineering-architect", {"rows": [{"id": "a"}], "key": "../x"})
        with self.assertRaises(ValueError):
            run_fixture("infrastructure-reliability-engineer", {"events": [True], "target": "1.5"})
        with self.assertRaises(ValueError):
            run_fixture("product-interface-designer", {"screens": [{"id": "a", "controls": [
                {"id": "x", "label": "Ok"}, {"id": "x", "label": "Ok"}]}]})

    def test_donor_ledger_records_source_identity_and_no_vendored_code(self):
        doc = json.loads((ROOT/"docs"/"donors"/"DONOR_RESEARCH.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(doc["sources"]), 5)
        for source in doc["sources"]:
            self.assertEqual(len(source["commit_sha"]), 40)
            self.assertTrue(source["url"].startswith("https://github.com/"))
            self.assertTrue(source["observed_license"])
            self.assertEqual(source["disposition"], "PATTERN_ONLY_NO_IMPORTED_CODE")
        self.assertFalse(doc["external_code_executed"])


if __name__ == "__main__":
    unittest.main()
