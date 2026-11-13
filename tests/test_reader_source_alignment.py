"""Reader docs must preserve the real source/release split and usable commands."""
from pathlib import Path
import json,re,unittest
ROOT=Path(__file__).resolve().parents[1]

class ReaderSourceAlignmentTests(unittest.TestCase):
 def text(self,path):return (ROOT/path).read_text(encoding='utf-8')
 def test_readme_and_capabilities_include_every_current_role(self):
  roles=json.loads(self.text('presets/catalog.json'))['presets']
  self.assertEqual(len(roles),15)
  for page in ['README.md','docs/CAPABILITIES.md']:
   body=self.text(page)
   for role in roles:
    with self.subTest(page=page,role=role):self.assertIn(role,body)
 def test_reader_guides_distinguish_source_from_published_zip_counts(self):
  for page in ['README.md','docs/GITHUB_QUICKSTART.md','docs/CAPABILITIES.md','docs/discovery/AI_AGENT_GUIDE.md','docs/RELEASES.md']:
   body=self.text(page).lower()
   with self.subTest(page=page):
    self.assertIn('15',body)
    self.assertIn('50',body)
    self.assertIn('v0.4.1-alpha',body)
    self.assertRegex(body,r'\b11\b|\beleven\b')
    self.assertRegex(body,r'\b8\b|\beight\b')
 def test_new_source_entrypoints_survive_reader_rewrite(self):
  for page in ['README.md','docs/GITHUB_QUICKSTART.md']:
   body=self.text(page)
   with self.subTest(page=page):
    self.assertIn('python -B quickstart.py --role personal-companion --to "$HOME/my-assistant-kit"',body)
    self.assertIn('python -B quickstart.py --all',body)
    self.assertIn('python -B examples/export_portable_skills.py --plan',body)
 def test_architecture_explains_shared_vs_role_procedures(self):
  body=self.text('docs/ARCHITECTURE.md')
  for value in ['15','45','five','50','120','role-skills','subchat-scopes','portable_skill_export']:
   self.assertIn(value,body)
 def test_persistence_explains_complete_home_without_claiming_native_memory(self):
  body=self.text('docs/INSTALL_AND_PERSISTENCE.md')
  for value in ['system-profile/profile','MEMORY.md','VOICE.md','OPINION.md','SYSTEM_PROMPT.md','skills.yaml','owner','does not install','three-way']:
   self.assertIn(value,body)
 def test_native_and_competitive_acceptance_stay_separate(self):
  body=self.text('docs/discovery/AI_AGENT_GUIDE.md').lower()
  self.assertIn('native',body)
  self.assertIn('not',body)
  self.assertIn('same model',body)
  self.assertIn('same tools',body)
  self.assertIn('same budget',body)
  self.assertIn('not established',body)
 def test_reader_rewrite_does_not_reintroduce_unsafe_example_destinations(self):
  for p in [ROOT/'README.md',*sorted((ROOT/'docs').rglob('*.md')),*sorted((ROOT/'presets').glob('*/INSTALL.md'))]:
   with self.subTest(path=p.relative_to(ROOT).as_posix()):
    self.assertNotRegex(p.read_text(encoding='utf-8'),r'--to\s+\.\./')

if __name__=='__main__':unittest.main()
