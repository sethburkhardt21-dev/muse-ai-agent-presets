"""Generic host-canary CLI surfaces report local success without native claims."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.cli import main


class GenericCanaryCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def call(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(argv)
        return code, json.loads(output.getvalue())

    def test_create_then_verify_source_bundle(self):
        dest = self.root / "candidate"
        rc, result = self.call([
            "generic-native-canary", "--preset", "coordinator",
            "--host", "personal-hatch", "--to", str(dest),
        ])
        self.assertEqual(rc, 0)
        self.assertEqual(result["status"], "SOURCE_ONLY_STAGED")
        self.assertFalse(result["native_installed"])
        self.assertFalse(result["external_effect_authorized"])
        rc, result = self.call(["generic-native-inspect", "--path", str(dest)])
        self.assertEqual(rc, 0)
        self.assertEqual(result["status"], "SOURCE_ONLY_MATCH")
        self.assertFalse(result["native_installed"])

    def test_existing_destination_is_not_overwritten(self):
        dest = self.root / "existing"
        dest.mkdir()
        (dest / "keep.txt").write_text("keep")
        rc, report = self.call([
            "generic-native-canary", "--preset", "software-engineer",
            "--host", "muse-code", "--to", str(dest),
        ])
        self.assertEqual(rc, 2)
        self.assertEqual(report["status"], "REFUSED")
        self.assertEqual((dest / "keep.txt").read_text(), "keep")

    def test_tampered_candidate_refused(self):
        dest = self.root / "candidate"
        self.call([
            "generic-native-canary", "--preset", "garden-companion",
            "--host", "muse-code", "--to", str(dest),
        ])
        (dest / "NATIVE_HANDOFF.md").write_text("altered")
        rc, result = self.call(["generic-native-inspect", "--path", str(dest)])
        self.assertEqual(rc, 2)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["external_effect_authorized"])

    def test_missing_supported_host_is_parse_error(self):
        with self.assertRaises(SystemExit) as ctx:
            self.call(["generic-native-canary", "--preset", "coordinator",
                       "--host", "invented-host", "--to", str(self.root / "new")])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
