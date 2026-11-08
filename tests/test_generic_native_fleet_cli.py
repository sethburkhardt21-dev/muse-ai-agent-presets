"""CLI smoke for the 11-role/22-host source-only fleet."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from muse_presets.cli import main


class GenericFleetCliTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)

    def call(self, command):
        stream=io.StringIO()
        with redirect_stdout(stream):
            status=main(command)
        return status,json.loads(stream.getvalue())

    def test_stage_and_inspect_all_roles_with_no_provider_auth(self):
        path=self.root/"fleet"
        status,receipt=self.call(["generic-native-fleet","--to",str(path)])
        self.assertEqual(status,0)
        self.assertEqual(receipt["profile_count"],11)
        self.assertEqual(receipt["native_canary_count"],22)
        self.assertFalse(receipt["native_installed"])
        status,report=self.call(["generic-native-fleet-inspect","--path",str(path)])
        self.assertEqual(status,0)
        self.assertEqual(report["status"],"LOCAL_FLEET_MATCH")
        self.assertFalse(report["external_effect_authorized"])

    def test_unsafe_destination_is_refused(self):
        target=self.root/"never-made"
        status,out=self.call(["generic-native-fleet","--to",str(target/"fleet")])
        self.assertEqual(status,2)
        self.assertEqual(out["status"],"REFUSED")
        self.assertFalse(target.exists())


if __name__=="__main__":
    unittest.main()
