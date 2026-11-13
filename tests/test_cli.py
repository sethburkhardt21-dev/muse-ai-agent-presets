import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from muse_presets.cli import main

class CliTests(unittest.TestCase):
    def test_doctor_passes_but_does_not_claim_native(self):
        output=io.StringIO()
        with redirect_stdout(output): code=main(['doctor'])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(output.getvalue())['native_muse_status'],'NOT_CHECKED')

    def test_list_includes_all_roles(self):
        output=io.StringIO()
        with redirect_stdout(output): code=main(['list'])
        self.assertEqual(code,0)
        self.assertEqual(len(output.getvalue().splitlines()),15)

    def test_render_then_deny_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=['render','--preset','learning-coach','--to',str(Path(tmp)/'rendered')]
            with redirect_stdout(io.StringIO()): self.assertEqual(main(args),0)
            with redirect_stdout(io.StringIO()) as result: self.assertEqual(main(args),2)
            self.assertIn('DESTINATION_EXISTS', result.getvalue())

    def test_family_preview_has_no_send(self):
        output=io.StringIO()
        with redirect_stdout(output): code=main(['family-preview','--from-role','learning-coach','--to-role','research-evaluator','--request-id','local-1'])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(output.getvalue())['state'],'PROPOSAL_ONLY_NOT_SENT')
