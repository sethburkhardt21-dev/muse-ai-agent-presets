"""Create-only offline Software Engineer pack staging, not native Muse install."""
from __future__ import annotations
import hashlib,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from muse_presets import engineering_pack as pack


class EngineerPackStaging(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='software-pack-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.dest=self.root/'software-engineer'

    def test_dry_run_preview_validates_exact_engine_and_leaves_no_files(self):
        result=pack.preview_engineer_pack()
        self.assertEqual(result['status'],'LOCAL_ENGINE_SOURCE_VERIFIED')
        self.assertEqual(result['runtime_modules'],9)
        self.assertEqual(result['role_id'],'software-engineer')
        self.assertEqual(result['native_muse_status'],'UNBOUND')
        self.assertFalse(result['source_owner_authenticated'])
        self.assertFalse(result['external_effect_authorized'])
        self.assertFalse(self.dest.exists())

    def test_stages_actual_engine_original_skill_contract_and_blank_owner_profile(self):
        result=pack.stage_engineer_pack(self.dest)
        self.assertEqual(result['status'],'LOCAL_ENGINE_PACK_STAGED')
        self.assertFalse(result['native_installed'])
        self.assertFalse(result['external_effect_authorized'])
        self.assertFalse(result['schedulers_enabled'])
        self.assertEqual(result['role_id'],'software-engineer')
        self.assertEqual(result['runtime_modules'],9)
        self.assertTrue((self.dest/'runtime/claim-gate/claim_gate.py').is_file())
        self.assertTrue((self.dest/'runtime/claim-gate/gate_approval.py').is_file())
        self.assertTrue((self.dest/'runtime/claim-gate/engineering_claim_gate.py').is_file())
        self.assertTrue((self.dest/'skills/claim-gate/SKILL.md').is_file())
        self.assertTrue((self.dest/'skills/claim-gate/skill.yaml').is_file())
        self.assertTrue((self.dest/'profile/AGENTS.md').is_file())
        self.assertTrue((self.dest/'profile/MEMORY.md').is_file())
        self.assertEqual(json.loads((self.dest/'profile/FAMILY_LINK.json').read_text())['enabled'],False)
        receipt=json.loads((self.dest/'receipts/PACK_RECEIPT.json').read_text())
        self.assertEqual(receipt['schema'],'software-engineer/pack-v1')
        self.assertEqual(receipt['installed_native_tools'],[])
        self.assertEqual(receipt['native_muse_status'],'UNBOUND')
        self.assertGreaterEqual(len(receipt['files_sha256']),23)
        for path,expected in receipt['files_sha256'].items():
            self.assertEqual(hashlib.sha256((self.dest/path).read_bytes()).hexdigest(),expected,path)

    def test_cannot_overwrite_owner_custom_profile_or_previous_stage(self):
        self.dest.mkdir()
        (self.dest/'MEMORY.md').write_bytes(b'private owner edits')
        before=(self.dest/'MEMORY.md').read_bytes()
        with self.assertRaisesRegex(FileExistsError,'DESTINATION_EXISTS'):
            pack.stage_engineer_pack(self.dest)
        self.assertEqual((self.dest/'MEMORY.md').read_bytes(),before)

    def test_unsafe_symlink_destination_refuses_without_following(self):
        outside=self.root/'owner'
        outside.mkdir()
        try:
            self.dest.symlink_to(outside,target_is_directory=True)
        except OSError as error:
            if os.name=='nt' and getattr(error,'winerror',None)==1314:
                self.skipTest('Windows symlink privilege unavailable on this host')
            raise
        with self.assertRaisesRegex((FileExistsError,ValueError),'DESTINATION'):
            pack.stage_engineer_pack(self.dest)
        self.assertEqual(list(outside.iterdir()),[])

    def test_symlink_destination_guard_without_native_symlink_privilege(self):
        with patch.object(Path,'is_symlink',autospec=True,
                          side_effect=lambda path:path==self.dest):
            with self.assertRaisesRegex(FileExistsError,'DESTINATION_EXISTS'):
                pack._require_new(self.dest)
        self.assertFalse(self.dest.exists())

    def test_wrong_runtime_sha_refused_before_creating_destination(self):
        original=pack.ENGINE_MANIFEST
        bogus=self.root/'bad_manifest.json'
        config=json.loads(original.read_text())
        config['files']['claim_gate.py']='0'*64
        bogus.write_text(json.dumps(config))
        with patch.object(pack,'ENGINE_MANIFEST',bogus):
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN_MISMATCH'):
                pack.stage_engineer_pack(self.dest)
        self.assertFalse(self.dest.exists())

    def test_post_install_inspection_detects_owner_changes_without_overwriting(self):
        pack.stage_engineer_pack(self.dest)
        old=self.dest/'profile/MEMORY.md'
        old.write_text('owner edited memory')
        check=pack.inspect_engineer_pack(self.dest)
        self.assertEqual(check['status'],'OWNER_CUSTOMIZED')
        self.assertEqual(check['owner_modified'],['profile/MEMORY.md'])
        self.assertFalse(check['native_installed'])
        self.assertEqual(old.read_text(),'owner edited memory')

    def test_tampered_skill_instruction_refused_before_pack_creation(self):
        copy=self.root/'tampered-skill'
        shutil.copytree(pack.SKILL_ROOT,copy)
        path=copy/'SKILL.md'
        path.write_text(path.read_text()+'\nUnsafe unreviewed instructions.\n')
        with patch.object(pack,'SKILL_ROOT',copy):
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN_MISMATCH'):
                pack.stage_engineer_pack(self.dest)
        self.assertFalse(self.dest.exists())

    def test_tampered_skill_registration_refused_before_pack_creation(self):
        copy=self.root/'tampered-skill'
        shutil.copytree(pack.SKILL_ROOT,copy)
        path=copy/'skill.yaml'
        path.write_text(path.read_text()+'\ninclude_in_prompt: true\n')
        with patch.object(pack,'SKILL_ROOT',copy):
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN_MISMATCH'):
                pack.preview_engineer_pack()
        self.assertFalse(self.dest.exists())

    def test_skills_explicitly_pinned_in_manifest(self):
        manifest=json.loads(pack.ENGINE_MANIFEST.read_text())
        self.assertEqual(set(manifest['skills']),{'SKILL.md','skill.yaml'})
        for name,digest in manifest['skills'].items():
            self.assertEqual(
                hashlib.sha256((pack.SKILL_ROOT/name).read_bytes()).hexdigest(),
                digest)

    def test_generated_bytecode_cache_cannot_be_staged_as_source(self):
        copy=self.root/'source-copy'
        shutil.copytree(pack.ENGINE_ROOT,copy)
        cache=copy/'__pycache__'
        cache.mkdir()
        (cache/'claim_gate.cpython-312.pyc').write_bytes(b'synthetic bytecode artifact')
        with patch.object(pack,'ENGINE_ROOT',copy), patch.object(pack,'ENGINE_MANIFEST',copy/'ENGINE.json'):
            result=pack.stage_engineer_pack(self.dest)
        self.assertEqual(result['status'],'LOCAL_ENGINE_PACK_STAGED')
        self.assertFalse((self.dest/'runtime/claim-gate/__pycache__').exists())

    @unittest.skipUnless(os.name=='nt','Windows-specific refusal contract')
    def test_windows_execution_cli_refuses_without_importing_posix_engine(self):
        import subprocess,sys
        from muse_presets.engineering_pack import ENGINE_ROOT
        state=self.root/'state'
        state.mkdir()
        p=subprocess.run([sys.executable,'-I','-B',str(ENGINE_ROOT/'engineering_claim_gate.py'),
                          '--state-dir',str(state),'--scope','engineering','--claim-id','dry-1','inspect'],
                         capture_output=True,text=True,timeout=8)
        self.assertEqual(p.returncode,2)
        answer=json.loads(p.stdout)
        self.assertEqual(answer['error_code'],'UNSUPPORTED_PLATFORM_POSIX_FCNTL_REQUIRED')
        self.assertFalse(answer['native_muse_invoked'])

    def test_invalid_role_or_unexpected_effect_injection_does_not_create_files(self):
        with self.assertRaises(TypeError):
            pack.stage_engineer_pack(self.dest,execute_shell='unsafe')
        self.assertFalse(self.dest.exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
