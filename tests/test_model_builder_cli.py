"""R33 Model Builder CLI create-only and inspector gates."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.cli import main


class ModelBuilderCliTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)

    def invoke(self,argv):
        stream=io.StringIO()
        with redirect_stdout(stream):
            code=main(argv)
        return code,json.loads(stream.getvalue())

    def test_standalone_stage_and_source_inspect(self):
        dest=self.root/"model-builder"
        code,receipt=self.invoke(["model-builder-dropin","--to",str(dest)])
        self.assertEqual(code,0)
        self.assertEqual(receipt["status"],"SOURCE_ONLY_MODEL_BUILDER_STAGED")
        self.assertFalse(receipt["native_installed"])
        code,report=self.invoke(["model-builder-dropin-inspect","--path",str(dest)])
        self.assertEqual(code,0)
        self.assertEqual(report["status"],"LOCAL_MODEL_BUILDER_MATCH")
        self.assertFalse(report["external_effect_authorized"])

    def test_existing_owner_directory_preserved(self):
        target=self.root/"owner"
        target.mkdir()
        (target/"MEMORY.md").write_text("original")
        code,result=self.invoke(["model-builder-dropin","--to",str(target)])
        self.assertEqual(code,2)
        self.assertEqual(result["status"],"REFUSED")
        self.assertEqual((target/"MEMORY.md").read_text(),"original")

    def test_tamper_rejected_with_nonzero_exit(self):
        target=self.root/"model"
        self.invoke(["model-builder-dropin","--to",str(target)])
        (target/"config"/"skills.yaml").write_text("version: 1\nentries:\n")
        code,result=self.invoke(["model-builder-dropin-inspect","--path",str(target)])
        self.assertEqual(code,2)
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertFalse(result["native_installed"])


if __name__=="__main__":
    unittest.main()
