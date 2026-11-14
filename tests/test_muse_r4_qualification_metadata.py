"""C100 R4 qualification metadata, not a live Muse benchmark."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"collections/muse-starters-v1"
R4_LANDED_SHA="82abced781e2603a022e1c378a486b5a2e49cf7e"

class R4QualificationMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counts=json.loads((C/"COUNTS.json").read_text(encoding="utf-8"))
        cls.wave=json.loads((C/"R4_WAVE.json").read_text(encoding="utf-8"))

    def test_depth_and_catalog_ids_still_match_source(self):
        skills=json.loads((C/"skills.json").read_text(encoding="utf-8"))
        starters=json.loads((C/"starters.json").read_text(encoding="utf-8"))
        workflows=json.loads((C/"workflows.json").read_text(encoding="utf-8"))
        self.assertEqual((len(starters),len(skills),len(workflows)),(100,75,25))
        self.assertEqual(sum(bool(x.get("depth")) for x in skills),75)
        self.assertEqual(len({x["id"] for x in skills}),75)
        self.assertEqual(len(self.wave["selected_skill_ids"]),28)
        self.assertEqual(self.counts["foundation_skills_awaiting_depth"],0)

    def test_r4_source_qualification_is_no_longer_marked_candidate(self):
        self.assertEqual(self.counts["r4_acceptance"],"PRIVATE_MAIN_SOURCE_QUALIFIED")
        self.assertEqual(self.wave["state"],"PRIVATE_MAIN_SOURCE_QUALIFIED")
        self.assertEqual(self.counts["r4_acceptance_commit"],R4_LANDED_SHA)
        self.assertEqual(self.wave["r4_acceptance_commit"],R4_LANDED_SHA)
        self.assertEqual(self.counts["r4_ci_run_id"],43262169201)

    def test_historical_qualification_counts_are_truthful_and_scoped(self):
        self.assertEqual(self.counts["r4_focused_test_cases_at_qualification"],397)
        self.assertEqual(self.counts["r4_parent_test_cases_at_qualification"],2041)
        self.assertIn("A_B_C",self.counts["source_test_count_status"])
        self.assertIn("SOURCE_TESTED",self.wave["source_qualification"])
        self.assertEqual(self.counts["paired_muse_comparisons_executed"],0)
        self.assertEqual(self.wave["actual_muse_comparisons"],0)
        self.assertEqual(self.counts["independent_upstream_reviews"],0)

    def test_current_r4_docs_describe_source_accepted_not_runtime_superiority(self):
        for path in (C/"README.md",C/"ROADMAP.md",ROOT/"docs/collection/MUSE_CURATED_COLLECTION.md"):
            with self.subTest(path=path):
                text=path.read_text(encoding="utf-8")
                self.assertIn("## R4 source qualification",text)
                self.assertNotIn("This is a candidate state until",text)
                self.assertIn("not",text.lower())
        self.assertFalse((C/"R4_WAVE.json").read_text(encoding="utf-8").find("LOCAL_CANDIDATE_NOT_INTEGRATED")>=0)

if __name__=="__main__":
    unittest.main()
