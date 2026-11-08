"""Host SDK metadata may traverse only OS-owned canonical macOS root aliases."""
import sys
import tempfile
import unittest
from pathlib import Path

from muse_presets.native_host_doctor import probe_host


def probe(root: Path, skills_root: Path):
    binary = root / "hatch-fixture"
    binary.write_bytes(b"fixture")
    proc = root / "proc"
    proc.mkdir()
    return probe_host("personal-hatch", binary_path=binary,
                      process_root=proc, skills_root=skills_root,
                      version_reader=lambda _: "hatch 0.1.0")


class HostDoctorMacRootAliasTests(unittest.TestCase):
    def test_trusted_system_var_alias_allows_read_only_sdk_hint(self):
        if sys.platform != "darwin" or not Path("/var").is_symlink():
            self.skipTest("requires standard macOS /var root alias")
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.assertTrue(str(root).startswith("/var/"), "macOS test must exercise /var alias")
            sdk=root/"skills"/"spaces"/"ts-runtime"/"sdk"
            sdk.mkdir(parents=True)
            (sdk/"package.json").write_text('{"name":"@hatch/space-sdk","version":"0.14.0"}')
            report=probe(root,root/"skills")
            self.assertEqual(report["runtime"]["space_sdk_version_hint"],"0.14.0")
            self.assertTrue(all(not granted for granted in report["authority"].values()))

    def test_arbitrary_user_symlink_ancestor_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            actual=root/"real-parent"
            sdk=actual/"skills"/"spaces"/"ts-runtime"/"sdk"
            sdk.mkdir(parents=True)
            (sdk/"package.json").write_text('{"name":"@hatch/space-sdk","version":"0.14.0"}')
            alias=root/"var"
            try:
                alias.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("platform denies test symlinks")
            report=probe(root,alias/"skills")
            self.assertIsNone(report["runtime"]["space_sdk_version_hint"])
            self.assertFalse(report["authority"]["host_authenticated"])


if __name__ == "__main__":
    unittest.main()
