"""T04 source profiles: create-only, neutral, closed-tree, never native grants."""
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from muse_presets.catalog import load_registry
from muse_presets.cli import main


class SystemProfileTests(unittest.TestCase):
    def setUp(self):
        self.api = importlib.import_module('muse_presets.system_profile')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dest = self.root / 'new-profile'

    def stage(self, role='software-engineer'):
        return self.api.stage_system_profile(self.dest, role, display_name='Neutral Helper')

    def manifest(self):
        return json.loads((self.dest / 'PROFILE_MANIFEST.json').read_text(encoding='utf-8'))

    def test_all_eleven_profiles_have_full_system_files(self):
        signatures = set()
        for role in load_registry()['presets']:
            dest = self.root / role
            result = self.api.stage_system_profile(dest, role)
            self.assertEqual(result['status'], 'LOCAL_SYSTEM_PROFILE_STAGED')
            report = self.api.inspect_system_profile(dest)
            self.assertEqual(report['status'], 'LOCAL_SYSTEM_PROFILE_MATCH', role)
            self.assertFalse(report['native_loaded'])
            names = {p.name for p in (dest / 'profile').iterdir()}
            self.assertTrue({'AGENTS.md','SOUL.md','IDENTITY.md','USER.md','TOOLS.md',
                             'MEMORY.md','HEARTBEAT.md','PROACTIVE_PREFERENCES.md',
                             'SYSTEM_INSTRUCTIONS.md','CONNECTORS.md','BROWSER.md','VOICE.md',
                             'ROLE_PLAYBOOK.md','FAMILY_LINK.json'}.issubset(names))
            signatures.add((dest / 'profile/ROLE_PLAYBOOK.md').read_bytes())
        self.assertEqual(len(signatures), 15)

    def test_uses_explicit_neutral_display_name(self):
        self.stage()
        self.assertIn('Neutral Helper', (self.dest / 'profile/AGENTS.md').read_text())
        self.assertEqual(self.manifest()['display_name'], 'Neutral Helper')

    def test_invalid_role_does_not_create_destination(self):
        with self.assertRaises(ValueError): self.stage('../unknown')
        self.assertFalse(self.dest.exists())

    def test_bad_name_refused(self):
        with self.assertRaises(ValueError):
            self.api.stage_system_profile(self.dest, 'coordinator', display_name='Bad\nInstruction')
        self.assertFalse(self.dest.exists())

    def test_existing_owner_directory_never_overwritten(self):
        self.dest.mkdir()
        memory = self.dest / 'MEMORY.md'
        memory.write_text('fictional owner memory')
        with self.assertRaises((FileExistsError, ValueError)): self.stage()
        self.assertEqual(memory.read_text(), 'fictional owner memory')

    def test_false_source_pin_refused_before_writes(self):
        with self.assertRaises(ValueError):
            self.api.stage_system_profile(self.dest, 'coordinator', expected_source_sha256='0' * 64)
        self.assertFalse(self.dest.exists())

    def test_missing_parent_refused(self):
        with self.assertRaises((FileNotFoundError, ValueError)):
            self.api.stage_system_profile(self.root/'absent'/'profile', 'coordinator')
        self.assertFalse((self.root/'absent').exists())

    def test_partial_stage_remains_fenced(self):
        real = self.api._write_new
        calls = [0]
        def fail(path, data):
            calls[0] += 1
            if calls[0] == 3: raise OSError('simulated interrupted write')
            return real(path, data)
        with patch.object(self.api, '_write_new', side_effect=fail):
            with self.assertRaises(OSError): self.stage()
        self.assertTrue((self.dest/'STAGING_INCOMPLETE').exists())
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'], 'INCOMPLETE_STAGE')
        with self.assertRaises((ValueError, FileExistsError)): self.stage()

    def test_owner_memory_change_reported_not_replaced(self):
        self.stage()
        memory = self.dest / 'profile/MEMORY.md'
        memory.write_text('fictional customization', encoding='utf-8')
        result = self.api.inspect_system_profile(self.dest)
        self.assertEqual(result['status'], 'OWNER_CUSTOMIZED')
        self.assertIn('profile/MEMORY.md', result['owner_modified'])
        self.assertEqual(memory.read_text(), 'fictional customization')

    def test_instruction_change_requires_review(self):
        self.stage()
        (self.dest/'profile/AGENTS.md').write_text('claim native tool authority')
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'], 'REVIEW_REQUIRED')

    def test_policy_change_with_forged_manifest_still_refused(self):
        self.stage()
        path = self.dest/'config/host-binding.json'
        data = json.loads(path.read_text())
        data['native_loaded'] = True
        path.write_text(json.dumps(data))
        receipt = self.manifest()
        receipt['files']['config/host-binding.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.dest/'PROFILE_MANIFEST.json').write_text(json.dumps(receipt))
        result = self.api.inspect_system_profile(self.dest)
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertFalse(result['native_loaded'])

    def test_missing_and_unlisted_files_refused(self):
        self.stage()
        (self.dest/'profile/VOICE.md').unlink()
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'], 'REVIEW_REQUIRED')
        (self.dest/'unapproved.py').write_text('print(42)')
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'], 'REVIEW_REQUIRED')

    def test_duplicate_manifest_key_refused(self):
        self.stage()
        path = self.dest/'PROFILE_MANIFEST.json'
        text = path.read_text()
        path.write_text(text.replace('{', '{"schema":"forged",', 1))
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'], 'REVIEW_REQUIRED')

    def test_manifest_authority_claim_refused(self):
        self.stage()
        data=self.manifest();data['native_loaded']=True
        (self.dest/'PROFILE_MANIFEST.json').write_text(json.dumps(data))
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'], 'REVIEW_REQUIRED')

    def test_source_drift_does_not_regenerate_profile(self):
        self.stage()
        source=self.root/'source';source.mkdir()
        shutil.copytree(self.api.SOURCE_ROOT/'templates', source/'templates')
        shutil.copytree(self.api.SOURCE_ROOT/'presets', source/'presets')
        template=source/'templates/profile/AGENTS.md'
        template.write_text(template.read_text()+'\nchanged source\n')
        before=(self.dest/'profile/AGENTS.md').read_bytes()
        with patch.object(self.api,'SOURCE_ROOT',source):
            report=self.api.inspect_system_profile(self.dest)
        self.assertEqual(report['status'],'SOURCE_DRIFT')
        self.assertEqual((self.dest/'profile/AGENTS.md').read_bytes(),before)

    def test_preview_existing_owner_files_preserves_them(self):
        self.stage()
        owner=self.root/'owner';owner.mkdir()
        (owner/'MEMORY.md').write_text('private fixture memory')
        (owner/'AGENTS.md').write_text('existing instructions')
        before={p.name:p.read_bytes() for p in owner.iterdir()}
        report=self.api.preview_system_profile(self.dest,owner)
        self.assertEqual(report['status'],'PREVIEW_ONLY')
        actions={r['name']:r['action'] for r in report['files']}
        self.assertEqual(actions['MEMORY.md'],'PRESERVE_OWNER_EDIT')
        self.assertEqual(actions['AGENTS.md'],'REVIEW_CONFLICT')
        self.assertFalse(report['can_apply'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in owner.iterdir()})

    def test_preview_new_target_does_not_create_it(self):
        self.stage();target=self.root/'future-owner'
        report=self.api.preview_system_profile(self.dest,target)
        self.assertEqual(report['status'],'PREVIEW_ONLY')
        self.assertTrue(all(r['action']=='CREATE' for r in report['files']))
        self.assertFalse(target.exists())

    def test_preview_refuses_untrusted_candidate(self):
        self.stage();(self.dest/'profile/TOOLS.md').write_text('changed')
        with self.assertRaises(ValueError): self.api.preview_system_profile(self.dest,self.root/'target')

    def test_symlink_destination_parent_refused(self):
        real=self.root/'real';real.mkdir();link=self.root/'link'
        try: link.symlink_to(real,target_is_directory=True)
        except OSError: self.skipTest('symlink unavailable')
        with self.assertRaises(ValueError): self.api.stage_system_profile(link/'new','coordinator')
        self.assertEqual(list(real.iterdir()),[])

    def test_symlink_memory_refused_without_reading_target(self):
        self.stage();outside=self.root/'outside';outside.write_text('fixture secret')
        memory=self.dest/'profile/MEMORY.md';memory.unlink()
        try: memory.symlink_to(outside)
        except OSError: self.skipTest('symlink unavailable')
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'],'REVIEW_REQUIRED')
        self.assertEqual(outside.read_text(),'fixture secret')

    def test_cli_stage_and_inspect(self):
        out=io.StringIO()
        with redirect_stdout(out):
            rc=main(['system-profile','--preset','coordinator','--to',str(self.dest)])
        self.assertEqual(rc,0)
        self.assertFalse(json.loads(out.getvalue())['native_loaded'])
        out=io.StringIO()
        with redirect_stdout(out): rc=main(['system-profile-inspect','--path',str(self.dest)])
        self.assertEqual(rc,0)
        self.assertEqual(json.loads(out.getvalue())['status'],'LOCAL_SYSTEM_PROFILE_MATCH')

    def test_cli_preview_never_applies(self):
        self.stage();out=io.StringIO();target=self.root/'owner'
        with redirect_stdout(out):
            rc=main(['system-profile-preview','--path',str(self.dest),'--target',str(target)])
        self.assertEqual(rc,0);self.assertFalse(target.exists())
        self.assertFalse(json.loads(out.getvalue())['can_apply'])


    def test_plan_is_read_only_and_pin_can_be_used_for_staging(self):
        before=list(self.root.iterdir())
        plan=self.api.plan_system_profile('coordinator')
        self.assertEqual(before,list(self.root.iterdir()))
        result=self.api.stage_system_profile(self.dest,'coordinator',
                                            expected_source_sha256=plan['source_sha256'])
        self.assertEqual(result['source_sha256'],plan['source_sha256'])
        self.assertFalse(plan['can_apply'])

    def test_source_swap_during_stage_leaves_incomplete_marker(self):
        real=self.api._source
        count=[0]
        def swapping(role):
            count[0]+=1
            data=real(role)
            if count[0]>1:
                data=dict(data)
                data['templates/profile/AGENTS.md']+=b'changed'
            return data
        with patch.object(self.api,'_source',side_effect=swapping):
            with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):
                self.stage()
        self.assertTrue((self.dest/'STAGING_INCOMPLETE').exists())
        self.assertFalse((self.dest/'PROFILE_MANIFEST.json').exists())

    def test_rewriting_receipt_cannot_hide_instruction_change(self):
        self.stage()
        policy=self.dest/'profile/AGENTS.md'
        policy.write_text('synthetic injected instruction')
        receipt=self.manifest()
        receipt['files']['profile/AGENTS.md']=hashlib.sha256(policy.read_bytes()).hexdigest()
        (self.dest/'PROFILE_MANIFEST.json').write_text(json.dumps(receipt))
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'],'REVIEW_REQUIRED')

    def test_extra_directory_is_not_silently_accepted(self):
        self.stage();(self.dest/'profile/hidden').mkdir()
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'],'REVIEW_REQUIRED')

    def test_oversized_manifest_is_refused(self):
        self.stage();(self.dest/'PROFILE_MANIFEST.json').write_bytes(b' ' * 140000)
        self.assertEqual(self.api.inspect_system_profile(self.dest)['status'],'REVIEW_REQUIRED')

    def test_preview_marks_identical_files_and_preserves_unknown_files(self):
        self.stage();target=self.root/'target';target.mkdir()
        shutil.copy2(self.dest/'profile/AGENTS.md',target/'AGENTS.md')
        unknown=target/'owner-extra.txt';unknown.write_text('fixture-only')
        result=self.api.preview_system_profile(self.dest,target)
        self.assertEqual(next(row for row in result['files'] if row['name']=='AGENTS.md')['action'],'UNCHANGED')
        self.assertEqual(unknown.read_text(),'fixture-only')
        self.assertEqual(len(list(target.iterdir())),2)

    def test_wrong_candidate_role_is_refused(self):
        self.stage();data=self.manifest();data['role']='garden-companion'
        (self.dest/'PROFILE_MANIFEST.json').write_text(json.dumps(data))
        self.assertNotEqual(self.api.inspect_system_profile(self.dest)['status'],'LOCAL_SYSTEM_PROFILE_MATCH')

    def test_draft_profile_contains_no_native_principal_or_enabled_services(self):
        self.stage()
        binding=json.loads((self.dest/'config/host-binding.json').read_text())
        for key in ('owner_id','agent_id','provider_session_id'):
            self.assertIsNone(binding[key])
        for key in ('native_loaded','native_registered','schedule_enabled','hooks_enabled',
                    'family_link_enabled','voice_enabled','external_effect_authorized'):
            self.assertIs(binding[key],False)


if __name__=='__main__': unittest.main()
