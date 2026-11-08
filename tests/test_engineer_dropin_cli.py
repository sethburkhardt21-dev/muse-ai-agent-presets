"""R33 native-format software-engineer command path: source only, no host install."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.cli import main


class EngineerDropinCliTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="r33-engineer-cli-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def call(self, argv):
        captured = io.StringIO()
        with redirect_stdout(captured):
            code = main(argv)
        return code, json.loads(captured.getvalue())

    def test_stage_and_inspect_are_really_callable(self):
        dest = self.root / "new-engineer"
        code, staged = self.call(["engineer-dropin", "--to", str(dest)])
        self.assertEqual(code, 0)
        self.assertEqual(staged["status"], "SOURCE_ONLY_NATIVE_FORMAT_STAGED")
        self.assertFalse(staged["native_installed"])
        code, checked = self.call(["engineer-dropin-inspect", "--path", str(dest)])
        self.assertEqual(code, 0)
        self.assertEqual(checked["status"], "LOCAL_DROPIN_MATCH")
        self.assertFalse(checked["external_effect_authorized"])

    def test_existing_owner_directory_is_preserved(self):
        dest = self.root / "owner-state"
        dest.mkdir()
        (dest / "MEMORY.md").write_text("private-owner-content")
        code, result = self.call(["engineer-dropin", "--to", str(dest)])
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual((dest / "MEMORY.md").read_text(), "private-owner-content")

    def test_missing_pack_is_rejected_without_fake_native_claim(self):
        code, report = self.call(
            ["engineer-dropin-inspect", "--path", str(self.root / "absent")]
        )
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertFalse(report["native_installed"])


if __name__ == "__main__":
    unittest.main()
