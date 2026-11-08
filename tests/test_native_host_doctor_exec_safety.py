"""R32.S2: inventory must not execute a caller-supplied program as a version probe."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from muse_presets.native_host_doctor import probe_host


class NativeDoctorExecSafetyTests(unittest.TestCase):
    def test_version_detection_never_executes_arbitrary_binary(self):
        with tempfile.TemporaryDirectory(prefix="r32s2-exec-fence-") as td:
            root = Path(td)
            marker = root / "unexpected-marker.txt"
            if os.name == "nt":
                executable = root / "fake-hatch.cmd"
                executable.write_text(
                    "@echo off\r\necho EFFECT>\"" + str(marker) + "\"\r\n"
                    "echo hatch 0.1.0\r\n", encoding="utf-8"
                )
            else:
                executable = root / "fake-hatch"
                executable.write_text(
                    '#!/bin/sh\nprintf EFFECT > "' + str(marker) + '"\n'
                    'printf "hatch 0.1.0\\n"\n', encoding="utf-8"
                )
                executable.chmod(0o700)

            report = probe_host(
                "personal-hatch", binary_path=executable,
                process_root=root, skills_root=root
            )
            self.assertFalse(
                marker.exists(),
                "A passive host-doctor inventory executed an untrusted binary"
            )
            self.assertFalse(report["authority"]["external_effect_authorized"])
            self.assertIsNone(report["runtime"]["version"])
            self.assertEqual(report["status"], "HOST_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
