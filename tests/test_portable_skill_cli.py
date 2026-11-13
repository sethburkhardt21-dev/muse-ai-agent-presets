"""The portable instruction library is usable from a fresh source checkout."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'examples/export_portable_skills.py'

class PortableSkillCLITests(unittest.TestCase):
    def call(self,*args):
        self.assertTrue(CLI.is_file(),'A documented no-environment-variable CLI is required')
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        return subprocess.run([sys.executable,'-B',str(CLI),*map(str,args)],
                              cwd=ROOT,env=env,capture_output=True,text=True,
                              encoding='utf-8',timeout=45)

    def test_plan_is_read_only_and_has_50_unique_skills(self):
        result=self.call('--plan')
        self.assertEqual(result.returncode,0,result.stderr)
        doc=json.loads(result.stdout)
        self.assertEqual(doc['unique_skills'],50)
        self.assertFalse(doc['native_installed'])

    def test_create_inspect_then_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'portable'
            made=self.call('--to',path);self.assertEqual(made.returncode,0,made.stdout+made.stderr)
            inspected=self.call('--inspect',path);self.assertEqual(inspected.returncode,0,inspected.stdout+inspected.stderr)
            self.assertEqual(json.loads(inspected.stdout)['status'],'LOCAL_PORTABLE_SKILLS_MATCH')
            before=(path/'safe-resume/SKILL.md').read_bytes()
            refused=self.call('--to',path);self.assertEqual(refused.returncode,2)
            self.assertEqual((path/'safe-resume/SKILL.md').read_bytes(),before)

    def test_inspect_refuses_tampered_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'portable';made=self.call('--to',path)
            self.assertEqual(made.returncode,0,made.stdout)
            (path/'safe-resume/SKILL.md').write_text('fabricated capability',encoding='utf-8')
            bad=self.call('--inspect',path)
            self.assertEqual(bad.returncode,2)
            self.assertEqual(json.loads(bad.stdout)['status'],'REVIEW_REQUIRED')

if __name__=='__main__':unittest.main()
