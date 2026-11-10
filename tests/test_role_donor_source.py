"""T18: source-pinned optional donor adapters, not native owner engines."""
from __future__ import annotations
import copy,hashlib,json,os
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch

from muse_presets.donor_source import (
    donor_catalog,inspect_donor,run_donor_fixture,
)

ROOT=Path(__file__).resolve().parents[1]
CAPS={"animation","evaluation","garden","study","claims","security"}
EXECUTABLE=CAPS-{"animation"}

class DonorSourceTests(unittest.TestCase):
    def test_exact_six_source_capabilities_without_seventh_agent(self):
        catalog=donor_catalog(ROOT)
        self.assertEqual(catalog["schema"],"muse-presets/optional-donor-source-v1")
        self.assertEqual(set(catalog["capabilities"]),CAPS)
        self.assertFalse(catalog["native_agent_installed"])
        self.assertFalse(catalog["external_effect_authorized"])
        self.assertEqual(catalog["provider_credentials_embedded"],False)
        for role in catalog["capabilities"].values():
            self.assertFalse(role["external_effect_authorized"])
            self.assertFalse(role["provider_authenticated"])

    def test_animation_not_silently_replaced_by_fake_engine(self):
        item=inspect_donor(ROOT,"animation")
        self.assertEqual(item["status"],"SOURCE_LINK_ONLY_NOT_BUNDLED")
        self.assertFalse(item["executable"])
        self.assertFalse(item["actual_animation_rendered"])
        with self.assertRaisesRegex(ValueError,"DONOR_NOT_IMPORTED"):
            run_donor_fixture(ROOT,"animation",allow_reviewed_fixture=True)

    def test_no_implicit_execution_and_exact_status_per_available_role(self):
        for cap in EXECUTABLE:
            with self.subTest(cap=cap):
                x=inspect_donor(ROOT,cap)
                self.assertEqual(x["status"],"SOURCE_PIN_MATCH")
                self.assertTrue(x["executable"])
                self.assertFalse(x["source_owner_authenticated"])
                self.assertFalse(x["native_tool_invoked"])
                self.assertFalse(x["external_effect_authorized"])
                self.assertTrue(x["files_sha256"])

    def test_fixture_requires_exact_optin(self):
        for cap in EXECUTABLE:
            with self.subTest(cap=cap):
                for opt in (False,None,1,"true",[]):
                    with self.assertRaisesRegex(ValueError,"EXPLICIT_DONOR_FIXTURE_OPTIN_REQUIRED"):
                        run_donor_fixture(ROOT,cap,allow_reviewed_fixture=opt)

    def test_unknown_capabilities_and_malicious_types_refused(self):
        for cap in ("unknown","remote-exec","../../secrets",{"role":"garden"},[],None,True,13):
            with self.subTest(cap=repr(cap)):
                with self.assertRaises(ValueError):
                    inspect_donor(ROOT,cap)
                with self.assertRaises(ValueError):
                    run_donor_fixture(ROOT,cap,allow_reviewed_fixture=True)

    def test_real_evaluation_fixture_preserves_truth_limit(self):
        out=run_donor_fixture(ROOT,"evaluation",allow_reviewed_fixture=True)
        self.assertEqual(out["status"],"LOCAL_SOURCE_FIXTURE_PASS")
        result=out["fixture_result"]
        self.assertEqual(result["research_evaluator"]["source_count"],2)
        self.assertTrue(result["research_evaluator"]["tampered_source_refused"])
        self.assertFalse(result["research_evaluator"]["scientific_hypothesis_proven"])
        self.assertFalse(out["external_effect_authorized"])

    def test_real_garden_sqlite_approval_recovery(self):
        out=run_donor_fixture(ROOT,"garden",allow_reviewed_fixture=True)
        self.assertEqual(out["status"],"LOCAL_SOURCE_FIXTURE_PASS")
        self.assertEqual(out["fixture_result"]["status"],"LOCAL_SQLITE_DEMO_PASSED")
        self.assertTrue(out["fixture_result"]["lost_ack_recovered"])
        self.assertFalse(out["fixture_result"]["host_authenticated"])

    def test_real_study_sqlite_owner_review_and_reopen(self):
        out=run_donor_fixture(ROOT,"study",allow_reviewed_fixture=True)
        self.assertEqual(out["status"],"LOCAL_SOURCE_FIXTURE_PASS")
        self.assertEqual(out["fixture_result"]["status"],"LOCAL_NONCLINICAL_STUDY_DEMO_PASSED")
        self.assertTrue(out["fixture_result"]["receipt_reopened"])
        self.assertTrue(out["fixture_result"]["review_due_after_24h"])
        self.assertFalse(out["fixture_result"]["clinical_release_ready"])

    def test_existing_claims_engine_used_without_upgraded_attestation(self):
        out=run_donor_fixture(ROOT,"claims",allow_reviewed_fixture=True)
        self.assertEqual(out["status"],"LOCAL_SOURCE_FIXTURE_PASS")
        self.assertEqual(out["fixture_result"]["disposition"],"OVERCLAIM")
        self.assertFalse(out["fixture_result"]["independent_verified"])
        self.assertFalse(out["fixture_result"]["effect_authorized"])

    def test_existing_safe_security_trace_uses_no_network_or_device(self):
        out=run_donor_fixture(ROOT,"security",allow_reviewed_fixture=True)
        self.assertEqual(out["status"],"LOCAL_SOURCE_FIXTURE_PASS")
        self.assertEqual(out["fixture_result"]["changed"],["click:sample_button"])
        self.assertFalse(out["fixture_result"]["network_activity"])
        self.assertFalse(out["fixture_result"]["native_invoked"])
        self.assertFalse(out["fixture_result"]["target_accessed"])

    def test_repeat_same_fixture_output_deterministic(self):
        for cap in EXECUTABLE:
            with self.subTest(cap=cap):
                a=run_donor_fixture(ROOT,cap,allow_reviewed_fixture=True)
                b=run_donor_fixture(ROOT,cap,allow_reviewed_fixture=True)
                self.assertEqual(a,b)

    def test_source_manifest_missing_or_bad_hash_refused(self):
        with tempfile.TemporaryDirectory() as td:
            fake=Path(td)
            (fake/"src/muse_presets").mkdir(parents=True)
            original=json.loads((ROOT/"src/muse_presets/donor_sources.json").read_text())
            tampered=copy.deepcopy(original)
            tampered["capabilities"]["claims"]["files_sha256"]["src/muse_presets/claims.py"]="0"*64
            (fake/"src/muse_presets/donor_sources.json").write_text(
                json.dumps(tampered),encoding="utf-8")
            with self.assertRaises(ValueError):
                inspect_donor(fake,"claims")

    def test_symlinked_root_refused_if_supported(self):
        with tempfile.TemporaryDirectory() as td:
            link=Path(td)/"link"
            try:link.symlink_to(ROOT,target_is_directory=True)
            except (OSError,NotImplementedError):self.skipTest("OS symlink creation restricted")
            with self.assertRaises(ValueError):
                inspect_donor(link,"garden")

    def test_source_inspection_does_not_write_repo_or_snapshot(self):
        targets=[ROOT/"src/muse_presets/donor_sources.json",
                 ROOT/"src/muse_presets/claims.py",
                 ROOT/"src/muse_presets/reverse.py"]
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in targets}
        donor_catalog(ROOT)
        for cap in CAPS:inspect_donor(ROOT,cap)
        self.assertEqual({str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in targets},before)

if __name__=="__main__":
    unittest.main()
