"""Documented output paths must pass the same admission as real first-use commands."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class DocumentedFirstRunTests(unittest.TestCase):
    def test_public_commands_do_not_use_rejected_parent_traversal(self):
        paths=[ROOT/'README.md',ROOT/'quickstart.py']
        paths+=list((ROOT/'docs').rglob('*.md'))+list((ROOT/'presets').rglob('*.md'))
        bad=[]
        for p in paths:
            for match in re.finditer(r'--(?:to|inspect|path) [\"\']?\.\./[A-Za-z0-9_.-]+',p.read_text(encoding='utf-8')):
                bad.append((p.relative_to(ROOT).as_posix(),match.group()))
        self.assertEqual(bad,[], 'Public examples must not instruct users to bypass traversal refusal')

    def test_readme_first_source_command_actually_creates_a_new_home(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        command=re.search(r'python -B quickstart\.py --role ([a-z-]+) --to "\$HOME/([^\"]+)"',text)
        self.assertIsNotNone(command,'Documented first-run command needs a safe new absolute destination')
        with tempfile.TemporaryDirectory() as home:
            target=Path(home)/command.group(2)
            env=os.environ.copy();env.pop('PYTHONPATH',None)
            result=subprocess.run([sys.executable,'-B',str(ROOT/'quickstart.py'),'--role',command.group(1),'--to',str(target)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=40)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((target/'system-profile/profile/AGENTS.md').is_file())
            self.assertTrue((target/'system-profile/profile/MEMORY.md').is_file())
            self.assertFalse(json.loads(result.stdout)['native_installed'])

    def test_portable_documented_destination_creates_inspectable_library(self):
        text=(ROOT/'docs/SKILLS.md').read_text(encoding='utf-8')
        command=re.search(r'python -B examples/export_portable_skills\.py --to "\$HOME/([^\"]+)"',text)
        self.assertIsNotNone(command)
        with tempfile.TemporaryDirectory() as home:
            target=Path(home)/command.group(1)
            env=os.environ.copy();env.pop('PYTHONPATH',None)
            result=subprocess.run([sys.executable,'-B',str(ROOT/'examples/export_portable_skills.py'),'--to',str(target)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=40)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(list(target.glob('*/SKILL.md'))),50)

    def test_traversal_refusal_remains_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            child=Path(tmp)/'cwd';child.mkdir();outside=Path(tmp)/'must-not-be-created'
            result=subprocess.run([sys.executable,'-B',str(ROOT/'quickstart.py'),'--role','personal-companion','--to','../must-not-be-created'],cwd=child,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,2)
            self.assertFalse(outside.exists())

if __name__=='__main__':unittest.main()
