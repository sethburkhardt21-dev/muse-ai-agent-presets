"""Single-command source-only clean consumer and no-overwrite refusal."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class OneCommandSourceQuickstart(unittest.TestCase):
    def call(self,*args):
        env=os.environ.copy()
        env.pop("PYTHONPATH",None)
        return subprocess.run(
            [sys.executable,"-B",str(ROOT/"quickstart.py"),*map(str,args)],
            cwd=ROOT,env=env,capture_output=True,text=True,timeout=65)

    def test_no_env_15_role_smoke(self):
        result=self.call("--all")
        self.assertEqual(result.returncode,0,result.stderr+result.stdout[-900:])
        data=json.loads(result.stdout)
        self.assertEqual(data["role_count"],15)
        self.assertEqual(data["total_subchat_scopes"],45)
        self.assertEqual(data["total_disabled_skills"],120)
        self.assertFalse(data["native_installed"])
        self.assertFalse(data["external_effect_authorized"])

    def test_source_only_create_only_and_memory_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="muse-faststart-") as td:
            target=Path(td)/"personal"
            result=self.call("--role","personal-companion","--to",target)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((target/"system-profile/profile/MEMORY.md").is_file())
            self.assertTrue((target/"system-profile/profile/VOICE.md").is_file())
            self.assertEqual(len(list((target/"subchat-scopes/subchats").iterdir())),3)
            original=target/"system-profile/profile/MEMORY.md"
            original.write_text("owner-private-edit",encoding="utf-8")
            refused=self.call("--role","personal-companion","--to",target)
            self.assertEqual(refused.returncode,2,refused.stdout)
            self.assertIn("REFUSED",refused.stdout)
            self.assertEqual(original.read_text(encoding="utf-8"),"owner-private-edit")

    def test_unknown_role_refused_without_files(self):
        with tempfile.TemporaryDirectory(prefix="muse-faststart-") as td:
            target=Path(td)/"none"
            refused=self.call("--role","nonexistent-specialist","--to",target)
            self.assertNotEqual(refused.returncode,0)
            self.assertFalse(target.exists())

if __name__=="__main__":
    unittest.main()
