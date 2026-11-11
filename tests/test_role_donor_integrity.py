"""Source-integrity regressions for optional local role adapters."""
from __future__ import annotations
import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from muse_presets import donor_source as donor
ROOT=Path(__file__).resolve().parents[1]

def manifest_path(root):
    portable=root/'src/muse_presets/donor_sources.json'
    return portable if portable.exists() else root/'control/r70/ROLE_DONOR_SOURCE_PINS.json'

class DonorIntegrityTests(unittest.TestCase):
    def clone(self):
        tmp=tempfile.TemporaryDirectory(prefix='role-integrity-')
        self.addCleanup(tmp.cleanup)
        target=Path(tmp.name)/'source'
        shutil.copytree(ROOT/'src',target/'src')
        shutil.copytree(ROOT/'examples',target/'examples')
        original=manifest_path(ROOT)
        dest=target/original.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,dest)
        return target

    def test_tampered_transitive_database_dependency_refused(self):
        clone=self.clone()
        (clone/'src/muse_presets/database_paths.py').write_text('# corrupted synthetic fixture\n',encoding='utf-8')
        with self.assertRaises(ValueError):
            donor.inspect_donor(clone,'garden')

    def test_rehashed_local_manifest_is_not_a_reviewer_signature(self):
        clone=self.clone()
        source=clone/'src/muse_presets/claims.py'
        source.write_text('# changed synthetic fixture\n',encoding='utf-8')
        path=manifest_path(clone)
        manifest=json.loads(path.read_text())
        manifest['capabilities']['claims']['files_sha256']['src/muse_presets/claims.py']=hashlib.sha256(source.read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest),encoding='utf-8')
        with self.assertRaises(ValueError):
            donor.inspect_donor(clone,'claims')

    def test_inspected_root_cannot_mislabel_parent_process_imports(self):
        clone=self.clone()
        with self.assertRaisesRegex(ValueError,'DONOR_RUNTIME_ROOT_MISMATCH'):
            donor.run_donor_fixture(clone,'claims',allow_reviewed_fixture=True)

    def test_child_imports_ignore_site_and_pythonpath_injection(self):
        commands=[]
        original=donor.subprocess.run
        def checked(command,*args,**kwargs):
            commands.append(command)
            return original(command,*args,**kwargs)
        with patch.object(donor.subprocess,'run',side_effect=checked):
            donor.run_donor_fixture(ROOT,'garden',allow_reviewed_fixture=True)
        self.assertTrue(commands)
        self.assertIn('-I',commands[0])
        self.assertIn('-S',commands[0])

    def test_clean_public_export_contains_complete_donor_source_and_pins(self):
        from muse_presets.public_export import select_public_files
        files=select_public_files(ROOT)
        self.assertIn('src/muse_presets/donor_source.py',files)
        self.assertIn('src/muse_presets/donor_sources.json',files)
        self.assertIn('examples/role_donor_demo.py',files)
        self.assertIn('docs/OPTIONAL_DONOR_ADAPTERS.md',files)
        self.assertFalse(any(x.startswith('control/') for x in files))

if __name__=='__main__':unittest.main()
