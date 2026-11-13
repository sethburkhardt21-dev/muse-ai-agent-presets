"""The full generic fleet is a create-only source package, never a live install."""
import json
import tempfile
import unittest
from pathlib import Path

from muse_presets.catalog import load_registry
from muse_presets.native_fleet import stage_generic_fleet, inspect_generic_fleet


class GenericNativeFleetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def stage(self):
        path=self.root/"neutral-fleet"
        result=stage_generic_fleet(path)
        self.assertEqual(result["status"],"LOCAL_FLEET_STAGED_ONLY")
        return path

    def test_all_eleven_generic_agents_have_profile_and_two_host_packets(self):
        p=self.stage()
        result=inspect_generic_fleet(p)
        self.assertEqual(result["status"],"LOCAL_FLEET_MATCH")
        self.assertEqual(result["profile_count"],15)
        self.assertEqual(result["native_canary_count"],30)
        self.assertFalse(result["native_installed"])
        self.assertFalse(result["external_effect_authorized"])
        roles=load_registry()["presets"]
        for name in roles:
            with self.subTest(name=name):
                self.assertTrue((p/"roles"/name/"profile"/"AGENTS.md").is_file())
                self.assertTrue((p/"roles"/name/"profile"/"SUBCHATS.md").is_file())
                self.assertTrue((p/"roles"/name/"personal-hatch"/"GENERIC_CANARY.json").is_file())
                self.assertTrue((p/"roles"/name/"muse-code"/"GENERIC_CANARY.json").is_file())
        receipt=json.loads((p/"FLEET_RECEIPT.json").read_text())
        self.assertEqual(receipt["schema"],"r32/generic-fleet-v1")
        self.assertEqual(set(receipt["roles"]),set(roles))
        self.assertFalse(receipt["native_installed"])

    def test_added_unlisted_file_refused(self):
        p=self.stage()
        (p/"unauthorized.py").write_text("print('not approved')")
        self.assertEqual(inspect_generic_fleet(p)["status"],"REVIEW_REQUIRED")

    def test_malformed_host_canary_refused(self):
        p=self.stage()
        doc=p/"roles"/"coordinator"/"personal-hatch"/"GENERIC_CANARY.json"
        text=doc.read_text()
        doc.write_text(text.replace('"native_authenticated": false','"native_authenticated": true'))
        self.assertEqual(inspect_generic_fleet(p)["status"],"REVIEW_REQUIRED")

    def test_incomplete_stage_marker_refused(self):
        p=self.stage()
        (p/"STAGING_INCOMPLETE").write_text("failure")
        self.assertEqual(inspect_generic_fleet(p)["status"],"INCOMPLETE_STAGE")

    def test_refuses_existing_directory_and_preserves_sentinel(self):
        p=self.root/"neutral-fleet"
        p.mkdir()
        sentinel=p/"owner-file.txt"
        sentinel.write_text("preserve")
        with self.assertRaises((ValueError,FileExistsError)):
            stage_generic_fleet(p)
        self.assertEqual(sentinel.read_text(),"preserve")

    def test_no_implicit_parent_directory_creation(self):
        with self.assertRaises((ValueError,FileNotFoundError)):
            stage_generic_fleet(self.root/"not-created"/"fleet")
        self.assertFalse((self.root/"not-created").exists())


if __name__=="__main__":
    unittest.main()
