"""Portable skill artifacts remain separate from underscore-based host descriptors."""
import importlib
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

class PortableSkillExportTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('muse_presets.portable_skill_export'),
                             'A standard-format adapter must exist without changing native IDs')
        return importlib.import_module('muse_presets.portable_skill_export')

    def test_fifty_unique_standard_names_and_directory_match(self):
        api=self.api();planned=api.plan_portable_skills()
        self.assertEqual(planned['unique_skills'],50)
        self.assertEqual(planned['role_methods'],45)
        self.assertEqual(planned['shared_skills'],5)
        self.assertEqual(len(planned['skills']),len(set(planned['skills'])))
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'skills';api.stage_portable_skills(dest)
            for name in planned['skills']:
                self.assertRegex(name,r'^[a-z0-9]+(?:-[a-z0-9]+)*$');self.assertLessEqual(len(name),64)
                raw=(dest/name/'SKILL.md').read_text(encoding='utf-8')
                front=raw.split('---\n',2)[1]
                fields={k:json.loads(v) for k,v in (line.split(': ',1) for line in front.strip().splitlines())}
                self.assertEqual(fields['name'],name)
                self.assertTrue(1<=len(fields['description'])<=1024)
                self.assertEqual(fields['license'],'MIT')
                self.assertNotIn('allowed-tools',fields)
            self.assertEqual(api.inspect_portable_skills(dest)['status'],'LOCAL_PORTABLE_SKILLS_MATCH')

    def test_native_ids_are_preserved_not_renamed(self):
        api=self.api()
        from muse_presets.role_skills import skill_id,plan_role_skills
        before=plan_role_skills('automation-engineer')
        with tempfile.TemporaryDirectory() as tmp:api.stage_portable_skills(Path(tmp)/'skills')
        self.assertEqual(before,plan_role_skills('automation-engineer'))
        self.assertEqual(skill_id('automation-engineer','map-workflow'),'automation_engineer_map_workflow')

    def test_create_only_refuses_and_preserves_owner_state(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'skills';dest.mkdir();p=dest/'MEMORY.md';p.write_text('owner data')
            with self.assertRaises(FileExistsError):api.stage_portable_skills(dest)
            self.assertEqual(p.read_text(),'owner data')

    def test_wrong_source_pin_refused_before_writing(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'skills'
            with self.assertRaisesRegex(ValueError,'PORTABLE_SOURCE_PIN_MISMATCH'):
                api.stage_portable_skills(dest,expected_source_sha256='0'*64)
            self.assertFalse(dest.exists())

    def test_deterministic_two_exports(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/'a',Path(tmp)/'b';api.stage_portable_skills(a);api.stage_portable_skills(b)
            one={p.relative_to(a).as_posix():p.read_bytes() for p in a.rglob('*') if p.is_file()}
            two={p.relative_to(b).as_posix():p.read_bytes() for p in b.rglob('*') if p.is_file()}
            self.assertEqual(one,two)

    def test_rehashed_unapproved_skill_change_refused(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'skills';api.stage_portable_skills(d)
            p=d/'safe-resume'/'SKILL.md';p.write_text(p.read_text(encoding='utf-8')+'\nInvented tool authorization.\n',encoding='utf-8')
            manifest=d/api.MANIFEST;x=json.loads(manifest.read_text());x['files']['safe-resume/SKILL.md']=hashlib.sha256(p.read_bytes()).hexdigest();manifest.write_text(json.dumps(x))
            self.assertEqual(api.inspect_portable_skills(d)['status'],'REVIEW_REQUIRED')

    def test_unlisted_file_refused(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'skills';api.stage_portable_skills(d);(d/'unexpected.py').write_text('untrusted')
            self.assertEqual(api.inspect_portable_skills(d)['status'],'REVIEW_REQUIRED')

    def test_incomplete_marker_is_not_accepted(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'skills';api.stage_portable_skills(d);(d/'STAGING_INCOMPLETE').write_text('incomplete')
            self.assertEqual(api.inspect_portable_skills(d)['status'],'INCOMPLETE_STAGE')

    def test_no_native_install_or_external_effect_claim(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'skills';out=api.stage_portable_skills(d);checked=api.inspect_portable_skills(d)
            for result in (out,checked):
                self.assertFalse(result['native_installed']);self.assertFalse(result['external_effect_authorized'])
            self.assertFalse((d/'skills.yaml').exists())

if __name__=='__main__':unittest.main()
