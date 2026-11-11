"""Regression: cleanup uncertainty must not discard bounded execution evidence."""
from __future__ import annotations
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'presets/software-engineer/runtime/claim-gate'))
w=importlib.import_module('engineering_workflow')
from test_engineering_workflow import case_fixture, TESTS, BUG

class CaptureCleanupEvidenceTests(unittest.TestCase):
    def test_cleanup_refusal_retains_output_and_unknown_reason(self):
        # The finite benign child exits naturally; no process is left running.
        for failure in (PermissionError(1,'synthetic cleanup refusal'),
                        ValueError('OWNED_CHILD_CLEANUP_UNCONFIRMED')):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);(root/'repo').mkdir()
                argv=[sys.executable,'-I','-B','-c',
                      "import time; print('x'*180000,flush=True); time.sleep(0.15)"]
                def refused_cleanup(process):
                    process.wait(timeout=2)  # Reconcile this finite test child before simulating the refusal.
                    raise failure
                with patch.object(w,'_terminate_owned',side_effect=refused_cleanup) as stop:
                    code,stdout,stderr,reason=w._capture(argv,root,3)
                self.assertGreaterEqual(stop.call_count,1)
                self.assertEqual(len(stdout),w.MAX_LOG)
                self.assertLessEqual(len(stderr),w.MAX_LOG)
                self.assertTrue(reason.startswith('OWNED_CHILD_CLEANUP_UNCONFIRMED'),reason)
                self.assertEqual(code,0)

    def test_workflow_cleanup_failure_holds_with_logs_and_no_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';case=case_fixture()
            case['files']['tests/test_bounds.py']=(
                "import time\nprint('x'*180000,flush=True)\ntime.sleep(0.15)\n"+TESTS)
            def refused_cleanup(process):
                process.wait(timeout=2)  # Only this fixture's finite child.
                raise PermissionError(1,'synthetic cleanup refusal')
            with patch.object(w,'_terminate_owned',side_effect=refused_cleanup):
                result=w.execute(case,root,expected_case_sha256=w.canonical_sha(case),reviewed_code=True)
            self.assertEqual(result['status'],'UNKNOWN_EFFECT_HOLD')
            self.assertIsNotNone(result['red'])
            self.assertTrue(result['red']['unknown_reason'].startswith('OWNED_CHILD_CLEANUP_UNCONFIRMED'))
            self.assertEqual((root/'red.stdout.log').stat().st_size,w.MAX_LOG)
            self.assertTrue((root/'red.stderr.log').is_file())
            self.assertEqual((root/'repo/bounds.py').read_text(),BUG)
            self.assertFalse((root/'candidate.json').exists())
            with patch.object(w,'_capture',side_effect=AssertionError('retry must not execute')):
                again=w.execute(case,root,expected_case_sha256=w.canonical_sha(case),reviewed_code=True)
            self.assertEqual(again['status'],'UNKNOWN_EFFECT_HOLD')
            self.assertFalse(again['automatic_retry_permitted'])

if __name__=='__main__':
    unittest.main()
