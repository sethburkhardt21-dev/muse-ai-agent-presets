"""R33 generic Coordinator CLI smoke and preservation gates."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.cli import main


class CoordinatorCliTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="r33-coordinator-cli-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)

    def invoke(self, args):
        out=io.StringIO()
        with redirect_stdout(out):
            code=main(args)
        return code,json.loads(out.getvalue())

    def test_stage_and_readback_are_source_only(self):
        p=self.root/"coordinator"
        code,result=self.invoke(["coordinator-dropin","--to",str(p)])
        self.assertEqual(code,0)
        self.assertEqual(result["status"],"SOURCE_ONLY_COORDINATOR_STAGED")
        self.assertFalse(result["native_installed"])
        code,result=self.invoke(["coordinator-dropin-inspect","--path",str(p)])
        self.assertEqual(code,0)
        self.assertEqual(result["status"],"LOCAL_COORDINATOR_MATCH")
        self.assertFalse(result["external_effect_authorized"])

    def test_existing_profile_is_not_overwritten(self):
        p=self.root/"existing"
        p.mkdir()
        (p/"MEMORY.md").write_text("owner preserved")
        code,out=self.invoke(["coordinator-dropin","--to",str(p)])
        self.assertEqual(code,2)
        self.assertEqual(out["status"],"REFUSED")
        self.assertEqual((p/"MEMORY.md").read_text(),"owner preserved")

    def test_tamper_refused_without_claiming_native(self):
        p=self.root/"role"
        self.invoke(["coordinator-dropin","--to",str(p)])
        (p/"config"/"skills.yaml").write_text("version: 1\nentries:\n")
        code,out=self.invoke(["coordinator-dropin-inspect","--path",str(p)])
        self.assertEqual(code,2)
        self.assertEqual(out["status"],"REVIEW_REQUIRED")
        self.assertFalse(out["native_installed"])

    def test_missing_source_does_not_fabricate_host_auth(self):
        code,out=self.invoke(["coordinator-dropin-inspect","--path",str(self.root/"absent")])
        self.assertEqual(code,2)
        self.assertEqual(out["status"],"REVIEW_REQUIRED")
        self.assertFalse(out["external_effect_authorized"])


if __name__=="__main__":
    unittest.main()
