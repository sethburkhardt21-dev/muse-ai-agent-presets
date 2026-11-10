"""T18 demo boundary: catalog is default; five local tests require opt-in."""
from __future__ import annotations
import unittest
from examples.role_donor_demo import demonstrate

class DonorExampleTests(unittest.TestCase):
    def test_default_is_read_only_catalog_without_work(self):
        r=demonstrate()
        self.assertEqual(r["status"],"SOURCE_CATALOG_ONLY")
        self.assertEqual(len(r["capabilities"]),6)
        self.assertFalse(r["fixture_executed"])
        self.assertFalse(r["external_effect_authorized"])
        self.assertFalse(r["animation_engine_bundled"])

    def test_explicit_opt_in_uses_five_real_local_fixtures(self):
        r=demonstrate(run_fixtures=True)
        self.assertEqual(r["status"],"FIVE_EXISTING_LOCAL_FIXTURES_PASS")
        self.assertEqual(len(r["fixtures"]),5)
        self.assertTrue(all(x["status"]=="LOCAL_SOURCE_FIXTURE_PASS"
                            for x in r["fixtures"].values()))
        self.assertFalse(r["native_agent_installed"])
        self.assertFalse(r["external_effect_authorized"])

    def test_animation_never_misrepresented_as_runnable(self):
        r=demonstrate()
        self.assertFalse(r["capabilities"]["animation"]["executable"])
        self.assertEqual(r["capabilities"]["animation"]["status"],
                         "SOURCE_LINK_ONLY_NOT_BUNDLED")
        self.assertNotIn("animation",demonstrate(run_fixtures=True)["fixtures"])

if __name__=="__main__":
    unittest.main()
