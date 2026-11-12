"""Reader-facing prose should describe the product, not its build chronology."""
from pathlib import Path
import json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=(ROOT/'docs/CAPABILITIES.md').is_file()
CORE=['README.md','docs/ARCHITECTURE.md','docs/HOST_COMPATIBILITY.md','docs/INSTALL_AND_PERSISTENCE.md']
def prose(value):
 value=re.sub(r'```.*?```','',value,flags=re.S)
 value=re.sub(r'`[^`]+`','',value)
 return re.sub(r'\]\([^)]+\)',']()',value)
class ReaderDocumentationTests(unittest.TestCase):
 def test_reader_pages_do_not_contain_escaped_paragraphs(self):
  for name in CORE:
   with self.subTest(path=name):self.assertNotIn(r'\n\n',(ROOT/name).read_text('utf-8'))
 def test_role_titles_use_names_not_packaging_labels(self):
  for page in (ROOT/'presets').glob('*/README.md'):
   with self.subTest(path=page):
    title=page.read_text('utf-8').splitlines()[0]
    self.assertNotRegex(title,r'(?i)generic|preset|source.only|runnable|R\d\d')
 def test_core_prose_avoids_vague_package_comparisons(self):
  forbidden=r'(?i)\bricher\b|first deeper|\bgeneric (?:specialist|profile|persona|study|helper|package|code|file)|The \[[^\]]+\] is a'
  for name in CORE:
   with self.subTest(path=name):self.assertNotRegex(prose((ROOT/name).read_text('utf-8')),forbidden)
 def test_readme_is_a_short_current_entrypoint(self):
  body=(ROOT/'README.md').read_text('utf-8')
  self.assertLess(len(body.encode()),8000)
  self.assertIn('# Specialist AI Agent Kits',body)
  self.assertNotRegex(prose(body),r'(?im)^#{1,6} .*\b(?:R\d{2}|T\d{2})\b|Python 3\.10\+')
 def test_architecture_has_named_components(self):
  body=(ROOT/'docs/ARCHITECTURE.md').read_text('utf-8')
  for term in ('presets/catalog.json','src/muse_presets/','templates/profile/','Local tools','Host integration'):
   self.assertIn(term,body)
 def test_install_guide_does_not_repeat_obsolete_windows_refusal(self):
  body=(ROOT/'docs/INSTALL_AND_PERSISTENCE.md').read_text('utf-8')
  self.assertNotIn('Windows can stage the pack but cannot execute',body)
  self.assertIn('Windows',body)
  self.assertIn('does not install',body.lower())
 def test_public_demo_uses_a_new_absolute_destination(self):
  if not PUBLIC:return
  for name in ('README.md','docs/GITHUB_QUICKSTART.md','docs/discovery/AI_AGENT_GUIDE.md'):
   body=(ROOT/name).read_text('utf-8')
   with self.subTest(path=name):
    self.assertNotIn('--to ../creative-production-demo',body)
    self.assertIn('--to "$HOME/creative-production-demo"',body)
 def test_public_reader_docs_keep_history_out_of_headings(self):
  if not PUBLIC:return
  for page in (ROOT/'docs').rglob('*.md'):
   with self.subTest(path=page):
    for line in page.read_text('utf-8').splitlines():
     if line.startswith('#'):
      self.assertNotRegex(line,r'(?i)\.S2|source increment|first richer|\bR\d{2}\b|\bT\d{2}\b')
 def test_source_test_and_permission_limits_stay_explicit(self):
  joined='\n'.join((ROOT/n).read_text('utf-8').lower() for n in CORE)
  for term in ('not a sandbox','not installed','disabled','authentication'):
   self.assertIn(term,joined)
if __name__=='__main__':unittest.main()
