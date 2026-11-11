"""R80 offline-only reverse comparison regression: no target/network access."""
from __future__ import annotations
import copy
import unittest
from muse_presets.reverse import compare_observed_flows

def obs(action, target, outcome):
    return {"action": action, "target": target, "outcome": outcome}

class ReverseFixtureSourceTests(unittest.TestCase):
    def test_change_add_remove_sorted_and_no_effects(self):
        before = [obs("click","save","modal"),obs("click","help","page"),obs("view","form","visible")]
        after = [obs("view","form","visible"),obs("click","export","file"),obs("click","save","toast")]
        result = compare_observed_flows(before, after)
        self.assertEqual(result["changed"], ["click:save"])
        self.assertEqual(result["added"], ["click:export"])
        self.assertEqual(result["removed"], ["click:help"])
        self.assertEqual(result["schema"], "muse-presets/reverse-fixture-diff-v1")
        for field in ("network_activity","target_accessed","native_invoked"):
            self.assertIs(result[field], False)

    def test_identical_and_empty_fixtures(self):
        fixture = [obs("scroll","results","next-page")]
        for left,right in (([],[]),(fixture,copy.deepcopy(fixture))):
            result = compare_observed_flows(left,right)
            self.assertEqual((result["added"],result["removed"],result["changed"]),([],[],[]))

    def test_input_not_modified(self):
        before=[obs("view","account","redacted")]
        after=[obs("view","account","redacted-2")]
        saved=copy.deepcopy((before,after))
        compare_observed_flows(before,after)
        self.assertEqual((before,after),saved)

    def test_rejects_duplicate_action_and_target(self):
        item=obs("click","submit","dialog")
        with self.assertRaisesRegex(ValueError,"DUPLICATE_ACTION_TARGET"):
            compare_observed_flows([item,item],[])

    def test_refuses_external_url_target(self):
        with self.assertRaises(ValueError):
            compare_observed_flows([obs("view","https://unapproved.example","ok")],[])

    def test_refuses_invalid_action_or_target(self):
        for item in (obs("execute","ok","no"),obs("click","../out","no"),
                     obs("click","a b","no"),obs("click","", "no"),obs("click","x"*65,"no")):
            with self.subTest(item=item),self.assertRaises(ValueError):
                compare_observed_flows([item],[])

    def test_refuses_unexpected_fields(self):
        with self.assertRaisesRegex(ValueError,"INVALID_OBSERVATION_SHAPE"):
            compare_observed_flows([dict(obs("click","save","ok"),password="synthetic")],[])

    def test_refuses_invalid_outcome(self):
        for outcome in ("","a"*257,None,1):
            with self.subTest(outcome=repr(outcome)),self.assertRaises(ValueError):
                compare_observed_flows([obs("click","save",outcome)],[])

    def test_refuses_oversize_or_nonlist(self):
        item=obs("view","screen","shown")
        with self.assertRaisesRegex(ValueError,"INVALID_OBSERVATIONS"):
            compare_observed_flows([item]*257,[])
        with self.assertRaisesRegex(ValueError,"INVALID_OBSERVATIONS"):
            compare_observed_flows("not-list",[])

    def test_refuses_nonobject_items(self):
        with self.assertRaisesRegex(ValueError,"INVALID_OBSERVATION_SHAPE"):
            compare_observed_flows([None],[])

if __name__=="__main__":
    unittest.main()
