"""Regression guards for readable product text and cross-platform required CI."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from muse_presets.distribution import product_findings
ROOT=Path(__file__).resolve().parents[1]

class ReleaseReadinessTests(unittest.TestCase):
 def gate(self):
  p=ROOT/'scripts/check_ci_results.py'
  self.assertTrue(p.is_file(),'A stable fail-closed matrix result check must ship')
  spec=importlib.util.spec_from_file_location('ci_result_gate',p)
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  return module
 def test_corrupted_utf8_prose_is_refused(self):
  for text in ('Version \u00e2\u20ac\u201d source','Broken \ufffd text'):
   with self.subTest(text=repr(text)),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);(root/'README.md').write_text('# Guide\n'+text,encoding='utf-8')
    self.assertIn('CORRUPTED_PRODUCT_TEXT',[x['reason'] for x in product_findings(root)])
 def test_valid_international_text_remains_supported(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'README.md').write_text('# Caf\u00e9\nR\u00e9sum\u00e9 \u2014 documentation.\n',encoding='utf-8')
   self.assertEqual(product_findings(root),[])
 def test_all_current_product_pages_have_clean_utf8(self):
  bad=[]
  for p in [ROOT/'CHANGELOG.md',ROOT/'README.md',*(ROOT/'docs').rglob('*.md')]:
   text=p.read_text(encoding='utf-8')
   if '\ufffd' in text or '\u00e2\u20ac' in text:bad.append(p.name)
  self.assertEqual(bad,[])
 def test_required_workflow_covers_three_platforms(self):
  text=(ROOT/'.github/workflows/checks.yml').read_text(encoding='utf-8')
  for required in ('ubuntu-latest','windows-latest','macos-latest','if: ${{ always() }}','needs: [source-tests, public-quality]','scripts/check_ci_results.py'):
   self.assertIn(required,text)
  self.assertNotIn('continue-on-error: true',text)
 def test_gate_accepts_only_all_success(self):
  gate=self.gate()
  self.assertTrue(gate.check_results({'source-tests':{'result':'success'},'public-quality':{'result':'success'}}))
  for state in ('skipped','cancelled','failure','neutral','unknown',None,True):
   with self.subTest(state=state):
    with self.assertRaises(ValueError):gate.check_results({'source-tests':{'result':state},'public-quality':{'result':'success'}})
 def test_gate_refuses_missing_unknown_or_malformed_jobs(self):
  gate=self.gate()
  for value in ({},[],None,{'source-tests':{'result':'success'}},{'source-tests':{'result':'success'},'public-quality':[]},{'source-tests':{'result':'success'},'public-quality':{'result':'success'},'unexpected':{'result':'success'}}):
   with self.subTest(value=value),self.assertRaises(ValueError):gate.check_results(value)

if __name__=='__main__':unittest.main()
