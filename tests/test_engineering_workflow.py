"""R55 real disposable-repository workflow and fail-closed boundary tests."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "presets/software-engineer/runtime/claim-gate"
sys.path.insert(0, str(ENGINE))

BUG = '''def clamp(value, low, high):
    if low > high:
        raise ValueError("invalid bounds")
    return min(max(value, low), high - 1)
'''
FIX = BUG.replace("high - 1)", "high)")
TESTS = '''import unittest
from bounds import clamp

class BoundaryTests(unittest.TestCase):
    def test_upper_inclusive(self):
        self.assertEqual(clamp(10, 0, 10), 10)
    def test_interior(self):
        self.assertEqual(clamp(5, 0, 10), 5)
    def test_lower(self):
        self.assertEqual(clamp(-2, 0, 10), 0)
    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            clamp(1, 3, 2)
'''
IDS = ["test_bounds.BoundaryTests." + x for x in
       ("test_upper_inclusive", "test_interior", "test_lower", "test_invalid_bounds")]


def case_fixture():
    return {
        "schema": "r55/engineering-case-v1",
        "case_id": "inclusive-boundary",
        "author_id": "source-author",
        "files": {"bounds.py": BUG, "tests/test_bounds.py": TESTS},
        "editable": ["bounds.py"],
        "test_ids": IDS[:],
        "expected_failures": [IDS[0]],
        "patch": [{"path": "bounds.py",
                   "before_sha256": hashlib.sha256(BUG.encode()).hexdigest(),
                   "after_utf8": FIX}],
        "command_profile": "python-unittest-v1",
        "timeout_seconds": 8,
    }


class EngineeringWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ENGINE / "engineering_workflow.py").is_file(),
                        "R55 executable workflow is missing; source instructions are not execution")
        self.w = importlib.import_module("engineering_workflow")
        self.tmp = tempfile.TemporaryDirectory(prefix="r55-workflow-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def run_case(self, case=None, name="run"):
        case = case or case_fixture()
        return self.w.execute(case, self.base / name,
                              expected_case_sha256=self.w.canonical_sha(case),
                              reviewed_code=True)

    def test_complete_red_patch_green_and_separate_review(self):
        case = case_fixture()
        original = copy.deepcopy(case)
        result = self.run_case(case)
        self.assertEqual(case, original)
        self.assertEqual(result["status"], "GREEN_TESTED")
        self.assertEqual(result["red"]["exit_code"], 1)
        self.assertEqual(result["red"]["result"]["failures"], [IDS[0]])
        self.assertEqual(result["green"]["exit_code"], 0)
        self.assertEqual(result["green"]["result"]["tests_run"], 4)
        self.assertEqual(result["green"]["result"]["failures"], [])
        self.assertEqual(result["green"]["result"]["errors"], [])
        self.assertEqual(result["green"]["result"]["skipped"], [])
        self.assertNotEqual(result["baseline_commit"], result["patched_commit"])
        self.assertEqual((self.base / "run/repo/bounds.py").read_text(), FIX)
        self.assertEqual((self.base / "run/repo/tests/test_bounds.py").read_text(), TESTS)
        candidate = self.base / "run/candidate.json"
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        review = self.w.review(candidate, self.base / "review",
                               expected_candidate_sha256=digest,
                               reviewer_id="separate-reviewer", expected_author_id="source-author",
                               reviewed_code=True)
        self.assertEqual(review["verdict"], "REVIEW_PASS")
        self.assertEqual(review["candidate_sha256"], digest)
        self.assertEqual(review["replayed_red_failures"], [IDS[0]])
        self.assertEqual(review["replayed_green_tests"], 4)
        self.assertFalse(review["identity_authenticated"])
        self.assertFalse(result["native_muse_invoked"])
        self.assertFalse(result["external_effect_authorized"])
        self.assertFalse(result["os_sandboxed"])
        self.assertTrue((self.base / "review/REVIEW.json").is_file())

    def test_unreviewed_code_refused_before_workspace_creation(self):
        c = case_fixture()
        with self.assertRaisesRegex(ValueError, "REVIEWED_CODE_REQUIRED"):
            self.w.execute(c, self.base / "no", expected_case_sha256=self.w.canonical_sha(c))
        self.assertFalse((self.base / "no").exists())

    def test_noop_patch_refused_before_execution(self):
        c = case_fixture()
        c["patch"][0]["after_utf8"] = BUG
        with self.assertRaisesRegex(ValueError, "NO_OP_PATCH"):
            self.run_case(c)
        self.assertFalse((self.base / "run").exists())

    def test_test_file_patch_and_unlisted_source_refused(self):
        for path in ("tests/test_bounds.py", "other.py", "../outside.py", ".git/config"):
            c = case_fixture()
            c["patch"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.run_case(c)
        self.assertFalse((self.base / "run").exists())

    def test_revision_mismatch_refused(self):
        c = case_fixture()
        c["patch"][0]["before_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SOURCE_REVISION_MISMATCH"):
            self.run_case(c)

    def test_case_hash_mismatch_refused(self):
        c = case_fixture()
        with self.assertRaisesRegex(ValueError, "CASE_PIN_MISMATCH"):
            self.w.execute(c, self.base / "no", expected_case_sha256="0" * 64,
                           reviewed_code=True)

    def test_missing_test_and_arbitrary_commands_refused(self):
        for change in ("unknown-command", "missing-test", "external-effect"):
            c = case_fixture()
            if change == "unknown-command": c["command_profile"] = "shell-powershell"
            elif change == "missing-test": c["test_ids"] = ["not_present.Suite.test_no"]
            else: c["external_effect"] = {"url": "https://invalid.example/"}
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.run_case(c)
        self.assertFalse((self.base / "run").exists())

    def test_green_baseline_not_accepted_as_red(self):
        c = case_fixture()
        c["files"]["bounds.py"] = FIX
        c["patch"][0]["before_sha256"] = hashlib.sha256(FIX.encode()).hexdigest()
        c["patch"][0]["after_utf8"] = FIX + "\n# no behavioral repair required\n"
        r = self.run_case(c)
        self.assertEqual(r["status"], "RED_NOT_REPRODUCED")
        self.assertFalse((self.base / "run/candidate.json").exists())
        self.assertEqual((self.base / "run/repo/bounds.py").read_text(), FIX)

    def test_import_error_does_not_count_as_intended_red(self):
        c = case_fixture()
        c["files"]["tests/test_bounds.py"] = "import nonexistent_fixture_module\n" + TESTS
        r = self.run_case(c)
        self.assertEqual(r["status"], "RED_NOT_REPRODUCED")
        self.assertFalse((self.base / "run/candidate.json").exists())

    def test_wrong_patch_keeps_green_failed(self):
        c = case_fixture()
        c["patch"][0]["after_utf8"] = BUG.replace("high - 1", "high - 2")
        r = self.run_case(c)
        self.assertEqual(r["status"], "GREEN_FAILED")
        self.assertFalse((self.base / "run/candidate.json").exists())

    def test_duplicate_execution_is_read_only_and_changed_payload_refused(self):
        c = case_fixture()
        r = self.run_case(c)
        paths = [self.base / "run/red.stdout.log", self.base / "run/green.stdout.log"]
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
        same = self.run_case(c)
        self.assertEqual(same, r)
        self.assertEqual(before, [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths])
        c["patch"][0]["after_utf8"] += "\n# changed candidate\n"
        with self.assertRaisesRegex(ValueError, "CHANGED_PAYLOAD_REPLAY"):
            self.run_case(c)

    def test_timeout_is_unknown_and_blind_retry_cannot_spawn_worker(self):
        c = case_fixture()
        c["timeout_seconds"] = 0.25
        c["files"]["tests/test_bounds.py"] = "import time\ntime.sleep(3)\n" + TESTS
        r = self.run_case(c)
        self.assertEqual(r["status"], "UNKNOWN_EFFECT_HOLD")
        before = (self.base / "run/red.stdout.log").stat().st_mtime_ns
        again = self.run_case(c)
        self.assertEqual(again["status"], "UNKNOWN_EFFECT_HOLD")
        self.assertEqual((self.base / "run/red.stdout.log").stat().st_mtime_ns, before)
        self.assertFalse((self.base / "run/candidate.json").exists())

    def test_printed_success_cannot_replace_process_result(self):
        c = case_fixture()
        c["files"]["tests/test_bounds.py"] = "import os\nprint('OK 4 tests passed', flush=True)\nos._exit(1)\n" + TESTS
        r = self.run_case(c)
        self.assertEqual(r["status"], "UNKNOWN_EFFECT_HOLD")
        self.assertFalse((self.base / "run/candidate.json").exists())

    def test_unexpected_file_written_by_tests_is_source_drift(self):
        c = case_fixture()
        c["files"]["tests/test_bounds.py"] = "from pathlib import Path\nPath('unexpected.txt').write_text('changed')\n" + TESTS
        r = self.run_case(c)
        self.assertEqual(r["status"], "SOURCE_DRIFT")
        self.assertEqual((self.base / "run/repo/bounds.py").read_text(), BUG)
        self.assertFalse((self.base / "run/candidate.json").exists())

    def test_existing_nonworkflow_destination_is_preserved(self):
        dest = self.base / "run"
        dest.mkdir()
        (dest / "owner.txt").write_text("owner data")
        with self.assertRaises(ValueError): self.run_case()
        self.assertEqual((dest / "owner.txt").read_text(), "owner data")

    def test_candidate_drift_rejected_before_review_execution(self):
        self.run_case()
        p = self.base / "run/candidate.json"
        original = hashlib.sha256(p.read_bytes()).hexdigest()
        p.write_bytes(p.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "CANDIDATE_PIN_MISMATCH"):
            self.w.review(p, self.base / "review", expected_candidate_sha256=original,
                          reviewer_id="reviewer", expected_author_id="source-author", reviewed_code=True)
        self.assertFalse((self.base / "review").exists())

    def test_self_review_and_wrong_author_refused(self):
        self.run_case()
        p = self.base / "run/candidate.json"
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        for reviewer, author in (("source-author", "source-author"), ("reviewer", "other-author")):
            with self.subTest(reviewer=reviewer), self.assertRaises(ValueError):
                self.w.review(p, self.base / "review", expected_candidate_sha256=digest,
                              reviewer_id=reviewer, expected_author_id=author, reviewed_code=True)

    def test_missing_reviews_and_forged_success_refused(self):
        self.run_case()
        p = self.base / "run/candidate.json"
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        for observations in ([], [{"status": "REVIEW_PASS"}], [{"verdict": "COMPLETE"}]):
            with self.subTest(observations=observations), self.assertRaises(ValueError):
                self.w.complete(p, expected_candidate_sha256=digest, observations=observations)

    def test_workspace_source_drift_after_green_is_not_cached_success(self):
        self.run_case()
        (self.base / "run/repo/bounds.py").write_text("# replaced after tests\n")
        with self.assertRaisesRegex(ValueError, "SOURCE_DRIFT"):
            self.run_case()

    def test_ancestor_symlink_refused(self):
        real = self.base / "real"
        real.mkdir()
        link = self.base / "alias"
        try: link.symlink_to(real, target_is_directory=True)
        except OSError: self.skipTest("OS denies symlink creation")
        with self.assertRaises(ValueError):
            self.w.execute(case_fixture(), link / "run",
                           expected_case_sha256=self.w.canonical_sha(case_fixture()), reviewed_code=True)
        self.assertEqual(list(real.iterdir()), [])


    def test_git_revision_drift_after_green_refuses_cached_success(self):
        self.run_case()
        # Same file bytes, different revision: the old receipt must not cover it.
        self.w._git(self.base / "run", "commit", "--quiet", "--allow-empty", "-m", "unexpected revision")
        with self.assertRaisesRegex(ValueError, "SOURCE_REVISION_DRIFT"):
            self.run_case()

    def test_second_unrelated_defect_uses_same_executor(self):
        c = case_fixture()
        broken = "def normalize(value):\n    return value.strip()\n"
        fixed = "def normalize(value):\n    return value.strip().lower()\n"
        tests = ("import unittest\nfrom textutil import normalize\n"
                 "class TextTests(unittest.TestCase):\n"
                 "    def test_upper(self):\n        self.assertEqual(normalize('  YES  '), 'yes')\n"
                 "    def test_lower(self):\n        self.assertEqual(normalize('  ok  '), 'ok')\n")
        c.update(case_id="text-normalization", files={"textutil.py": broken, "tests/test_textutil.py": tests},
                 editable=["textutil.py"], test_ids=["test_textutil.TextTests.test_upper", "test_textutil.TextTests.test_lower"],
                 expected_failures=["test_textutil.TextTests.test_upper"],
                 patch=[{"path": "textutil.py", "before_sha256": hashlib.sha256(broken.encode()).hexdigest(),
                         "after_utf8": fixed}])
        result = self.run_case(c)
        self.assertEqual(result["status"], "GREEN_TESTED")
        self.assertEqual(result["green"]["result"]["tests_run"], 2)

    def test_complete_bound_observations_and_tampered_receipt(self):
        from unittest.mock import patch
        # Host names are TEST DOUBLES for the external observation boundary;
        # this tests binding logic, not authenticated machine independence.
        with patch.object(self.w.socket, "gethostname", return_value="fixture-writer"):
            result = self.run_case()
        p = self.base / "run/candidate.json"
        digest = result["candidate_sha256"]
        observations = []
        for host, reviewer in (("fixture-b", "reviewer-b"), ("fixture-c", "reviewer-c")):
            dest = self.base / reviewer
            with patch.object(self.w.socket, "gethostname", return_value=host):
                observed = self.w.review(p, dest, expected_candidate_sha256=digest,
                                        reviewer_id=reviewer, expected_author_id="source-author", reviewed_code=True)
            self.assertEqual(observed["verdict"], "REVIEW_PASS")
            path = dest / "REVIEW.json"
            observations.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                 "host": host, "reviewer_id": reviewer})
        complete = self.w.complete(p, expected_candidate_sha256=digest, observations=observations)
        self.assertEqual(complete["status"], "COMPLETE")
        self.assertFalse(complete["identity_authenticated"])
        self.assertFalse(complete["external_effect_authorized"])
        self.assertEqual(complete["scope"], "DISPOSABLE_REPOSITORY_SOURCE_WORKFLOW_ONLY")
        import io
        from contextlib import redirect_stdout
        observed_file = self.base / "operator-observations.json"
        observed_file.write_text(json.dumps(observations), encoding="utf-8")
        captured = io.StringIO()
        with redirect_stdout(captured):
            self.assertEqual(self.w.main(["complete", "--candidate", str(p),
                             "--candidate-sha256", digest, "--observations", str(observed_file)]), 0)
        self.assertEqual(json.loads(captured.getvalue())["status"], "COMPLETE")
        forged = copy.deepcopy(observations)
        forged[1]["host"] = forged[0]["host"]
        with self.assertRaises(ValueError):
            self.w.complete(p, expected_candidate_sha256=digest, observations=forged)
        receipt = Path(observations[1]["path"])
        receipt.write_bytes(receipt.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "REVIEW_RECEIPT_PIN_MISMATCH"):
            self.w.complete(p, expected_candidate_sha256=digest, observations=observations)

    def test_output_limit_is_held_not_red(self):
        c = case_fixture()
        c["files"]["tests/test_bounds.py"] = "print('x' * 180000, flush=True)\n" + TESTS
        result = self.run_case(c)
        self.assertEqual(result["status"], "UNKNOWN_EFFECT_HOLD")
        self.assertLessEqual((self.base / "run/red.stdout.log").stat().st_size, 65536)
        self.assertFalse((self.base / "run/candidate.json").exists())

    def test_skipped_regression_never_counts_as_green(self):
        c = case_fixture()
        c["files"]["tests/test_bounds.py"] = TESTS.replace(
            "    def test_upper_inclusive(self):", "    @unittest.skip('cannot count skipped repair')\n    def test_upper_inclusive(self):")
        result = self.run_case(c)
        self.assertEqual(result["status"], "RED_NOT_REPRODUCED")

    def test_interrupted_claim_holds_without_implicit_retry(self):
        from claim_gate import ClaimGate
        c = case_fixture()
        dest = self.base / "run"
        dest.mkdir()
        raw = self.w._canonical(c)
        (dest / "plan.json").write_bytes(raw)
        ClaimGate(str(dest / "claim-state")).claim("engineering-workflow", c["case_id"], raw)
        result = self.run_case(c)
        self.assertEqual(result["status"], "UNKNOWN_EFFECT_HOLD")
        self.assertFalse((dest / "repo").exists())


    def test_role_verifier_runs_real_workflow_not_only_claim_gate(self):
        from examples.verify_role_packages import verify_one
        report = verify_one(ROOT, "software-engineer")
        self.assertTrue(report.get("workflow_red_green_proven", False))
        self.assertIs(report.get("workflow_independent_review_complete"), False)

    def test_packaged_workflow_cli_and_demo_preserve_red_and_green(self):
        demo_path = ROOT / "examples/software_engineer_workflow_demo.py"
        self.assertTrue(demo_path.is_file(), "Source pack lacks executable workflow demonstration")
        from examples.software_engineer_workflow_demo import demonstrate
        target = self.base / "installed-demo"
        result = demonstrate(target)
        self.assertEqual(result["status"], "LOCAL_ENGINEERING_WORKFLOW_GREEN")
        self.assertEqual(result["workflow"]["red_exit"], 1)
        self.assertEqual(result["workflow"]["green_exit"], 0)
        self.assertEqual(result["independent_review_status"], "PENDING_EXTERNAL_REVIEWS")
        self.assertTrue((target / "work/candidate.json").is_file())
        self.assertTrue((target / "engine/runtime/claim-gate/workflow_worker.py").is_file())
        self.assertFalse(result["native_muse_invoked"])
        self.assertFalse(result["external_effect_authorized"])


    def test_unknown_review_execution_produces_failed_receipt_not_success(self):
        from unittest.mock import patch
        result = self.run_case()
        candidate = self.base / "run/candidate.json"
        with patch.object(self.w, "_capture", return_value=(124, b"", b"", "TIMEOUT")):
            review = self.w.review(candidate, self.base / "failed-review",
                        expected_candidate_sha256=result["candidate_sha256"],
                        reviewer_id="reviewer", expected_author_id="source-author", reviewed_code=True)
        self.assertEqual(review["verdict"], "REVIEW_FAILED")
        self.assertEqual(review["replayed_green_tests"], 0)
        self.assertTrue((self.base / "failed-review/REVIEW.json").exists())


if __name__ == "__main__":
    unittest.main()
