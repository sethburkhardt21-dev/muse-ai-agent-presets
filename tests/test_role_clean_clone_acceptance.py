"""T32 source acceptance: per-role local functionality, never native-host claims."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io
from contextlib import redirect_stdout
import os

from examples import verify_role_packages as verify
from muse_presets.catalog import load_registry
from muse_presets.standalone_pack import stage_standalone_pack, inspect_standalone_pack


class RoleCleanCloneAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[1]
        cls.report=verify.verify_all(cls.root,load_registry()["presets"])

    def test_all_eleven_distinct_packages_source_checked(self):
        result=self.report
        self.assertEqual(result["status"],"CLEAN_CLONE_ROLE_MATRIX_SOURCE_ONLY")
        self.assertEqual(result["role_count"],11)
        self.assertEqual(set(result["roles"]),set(load_registry()["presets"]))
        self.assertEqual(result["subchats"],33)
        self.assertEqual(result["disabled_skills"],33)
        self.assertFalse(result["native_installed"])
        self.assertFalse(result["public_git_pushed"])
        self.assertFalse(result["provider_connected"])
        for role,item in result["roles"].items():
            self.assertEqual(item["source_inspection"],"LOCAL_STANDALONE_MATCH",role)
            self.assertEqual(item["source_export"],"LOCAL_EXPORT_CREATED",role)
            self.assertRegex(item["role_zip_sha256"],r"^[0-9a-f]{64}$")
            self.assertTrue(item["role_zip_file_count"]>20)
            self.assertEqual(item["subchats"],3)
            self.assertEqual(item["disabled_skills"],3)
            self.assertFalse(item["external_effects_authorized"])
            self.assertFalse(item["native_installed"])
            self.assertFalse(item["provider_connected"])

    def test_coordinator_and_model_builder_execute_real_local_demo(self):
        for role in ("coordinator","model-builder"):
            item=self.report["roles"][role]
            self.assertEqual(item["local_demo_grade"],"LOCAL_ENGINE_DEMO_PASSED")
            self.assertTrue(item["local_engine_executed"])
            self.assertTrue(item["demo_exit_code"]==0)

    def test_garden_and_learning_execute_real_local_sqlite_examples(self):
        for role in ("garden-companion","learning-coach"):
            item=self.report["roles"][role]
            self.assertEqual(item["local_demo_grade"],"LOCAL_ENGINE_DEMO_PASSED")
            self.assertTrue(item["local_engine_executed"])
            self.assertEqual(item["demo_exit_code"],0)

    def test_claims_and_reverse_are_only_local_micro_slices(self):
        for role in ("claims-adjudicator","reverse-engineering-researcher"):
            item=self.report["roles"][role]
            self.assertEqual(item["local_demo_grade"],"LOCAL_SLICE_DEMO_PASSED")
            self.assertTrue(item["local_engine_executed"])
            self.assertFalse(item["independent_adjudicator_or_live_capture"])

    def test_three_other_roles_do_not_fabricate_engines(self):
        for role in ("creative-studio","adversarial-verifier","personal-companion"):
            item=self.report["roles"][role]
            self.assertEqual(item["local_demo_grade"],"SOURCE_TEMPLATE_ONLY")
            self.assertFalse(item["local_engine_executed"])
            self.assertIsNone(item["demo_exit_code"])

    def test_research_evaluator_executes_only_source_trace_slice(self):
        item=self.report["roles"]["research-evaluator"]
        self.assertEqual(item["local_demo_grade"],"LOCAL_SLICE_DEMO_PASSED")
        self.assertTrue(item["local_engine_executed"])
        self.assertFalse(item["independent_adjudicator_or_live_capture"])
        self.assertFalse(item["external_effects_authorized"])

    def test_software_engineer_cross_platform(self):
        item=self.report["roles"]["software-engineer"]
        self.assertEqual(item["local_demo_grade"],"LOCAL_ENGINE_DEMO_PASSED")
        self.assertTrue(item["local_engine_executed"])
        self.assertFalse(item["native_installed"])

    def test_shared_evidence_finder_is_not_twelfth_agent(self):
        item=self.report["shared_services"]["evidence-finder"]
        self.assertEqual(item["local_demo_grade"],"LOCAL_ENGINE_DEMO_PASSED")
        self.assertEqual(item["demo_exit_code"],0)
        self.assertNotIn("evidence-finder",self.report["roles"])

    def test_wrong_role_rejected_before_effects(self):
        with self.assertRaisesRegex(ValueError,"INVALID_ROLE"):
            verify.verify_one(self.root,"../../not-a-role")
        with self.assertRaisesRegex(ValueError,"INVALID_ROLE"):
            verify.verify_one(self.root,"unknown-role")

    def test_existing_role_package_policy_forgery_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"role"
            stage_standalone_pack(path,"garden-companion")
            wrong=path/"role-skills"/"config"/"skills.yaml"
            wrong.write_text(wrong.read_text(encoding="utf-8").replace("disabled","connected",1),
                             encoding="utf-8")
            self.assertEqual(inspect_standalone_pack(path)["status"],"REVIEW_REQUIRED")

    def test_cli_json_is_source_only(self):
        buffer=io.StringIO()
        with patch.object(verify,"verify_all",return_value=self.report):
            with redirect_stdout(buffer):
                self.assertEqual(verify.main(["--all"]),0)
        parsed=json.loads(buffer.getvalue())
        self.assertEqual(parsed["role_count"],11)
        self.assertFalse(parsed["native_installed"])
        self.assertFalse(parsed["public_git_pushed"])

    def test_docs_show_real_demo_vs_template(self):
        docs=(self.root/"docs/CAPABILITIES.md").read_text(encoding="utf-8")
        for role in load_registry()["presets"]:
            self.assertIn(role,docs)
        for key in ("Template only","Windows","source-only"):
            self.assertIn(key,docs)
        self.assertIn("source-only",docs.lower())


if __name__=="__main__":unittest.main()
