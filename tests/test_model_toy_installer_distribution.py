"""R61: installer shipped in sourcekit and executable without original repo."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from muse_presets import model_toy_math as engine, model_toy_sourcekit as kit

class InstallerDistributionTests(unittest.TestCase):
    def test_extracted_kit_stages_and_inspects_through_own_isolated_cli(self):
        with tempfile.TemporaryDirectory(prefix='r61-extracted-installer-') as temp:
            root=Path(temp);archive=root/'kit.zip'
            exported=kit.export_sourcekit(archive)
            extracted=root/'fresh';extracted.mkdir()
            with zipfile.ZipFile(archive) as z:
                self.assertIn('runtime/model_toy_install.py',z.namelist())
                z.extractall(extracted)
            cli=extracted/'runtime/model_toy_install.py'
            stage=root/'new-install'
            denied=subprocess.run([sys.executable,'-I','-B',str(cli),'stage','--to',str(stage)],
                                   capture_output=True,text=True,timeout=30,cwd=extracted)
            self.assertEqual(denied.returncode,2,denied.stdout+denied.stderr)
            self.assertFalse(stage.exists())
            created=subprocess.run([sys.executable,'-I','-B',str(cli),'stage','--to',str(stage),
                                    '--include-toy-training'],capture_output=True,text=True,
                                   timeout=30,cwd=extracted)
            self.assertEqual(created.returncode,0,created.stdout+created.stderr)
            info=json.loads(created.stdout)
            self.assertEqual(info['status'],'SOURCE_ONLY_TOY_EXTENSION_STAGED')
            self.assertFalse(info['training_started'])
            inspect=subprocess.run([sys.executable,'-I','-B',str(cli),'inspect','--root',str(stage),
                                    '--stage-sha256',info['stage_receipt_sha256']],
                                   capture_output=True,text=True,timeout=30,cwd=extracted)
            self.assertEqual(inspect.returncode,0,inspect.stdout+inspect.stderr)
            self.assertEqual(json.loads(inspect.stdout)['status'],'LOCAL_TOY_EXTENSION_STAGE_MATCH')
            self.assertEqual((stage/'runtime/model_toy_install.py').read_bytes(),cli.read_bytes())
            self.assertEqual(engine.digest(archive.read_bytes()),exported['sha256'])

if __name__=='__main__':unittest.main()
