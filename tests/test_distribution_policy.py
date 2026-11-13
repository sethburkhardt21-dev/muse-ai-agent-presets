"""Public product quality: negative fixtures must fail before publication."""
from __future__ import annotations
import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class DistributionPolicyTests(unittest.TestCase):
 def test_public_text_bytes_match_declared_lf_checkout_policy(self):
  from muse_presets.public_export import select_public_files
  files=select_public_files(ROOT,verify_manifest=False)
  noncanonical=[name for name,raw in files.items() if b'\r\n' in raw]
  self.assertEqual(noncanonical,[], 'Manifest hashes must match Git-normalized source on every platform')

 def engine(self):
  self.assertIsNotNone(importlib.util.find_spec('muse_presets.distribution'),
      'A reusable public distribution quality gate must ship with the source')
  from muse_presets import distribution
  return distribution
 def test_gate_module_exists(self):self.engine()
 def test_clean_customer_document_allowed(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'docs').mkdir();(r/'docs/USAGE.md').write_text('# Usage\nA checkpoint stores local progress.\n')
   self.assertEqual(self.engine().product_findings(r),[])
 def test_nested_milestones_and_case_variants_rejected(self):
  for name in ('docs/R77_STATUS.md','docs/guide/r777_handoff.md','docs/nested/FINAL_CHECKPOINT.json','control/WORKGRAPH.json','.atlas/receipts/proof.json','scratch/plan.md'):
   with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
    r=Path(td);p=r/name;p.parent.mkdir(parents=True);p.write_text('{}')
    self.assertTrue(self.engine().product_findings(r),name)
 def test_internal_prose_in_any_role_readme_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/'presets/demo/README.md';p.parent.mkdir(parents=True)
   p.write_text('# Role\nR77 source candidate; see Asana task T19.\n')
   self.assertTrue(self.engine().product_findings(r))
 def test_technical_schema_and_historical_download_urls_allowed(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'README.md').write_text('# User guide\n[Download](https://example.org/releases/tag/kit-r56-alpha)\n\n```json\n{"schema":"r33/example-v1"}\n```\n')
   self.assertEqual(self.engine().product_findings(r),[])
 def test_nested_broken_markdown_link_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/'docs/guide/index.md';p.parent.mkdir(parents=True)
   p.write_text('# Help\n[Missing](../../NO_SUCH_FILE.md)\n')
   self.assertTrue(any(x['reason']=='BROKEN_LOCAL_LINK' for x in self.engine().product_findings(r)))
 def test_symlink_never_read_or_exported(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/'outside.md';p.write_text('private')
   q=r/'docs';q.mkdir()
   try:(q/'LINK.md').symlink_to(p)
   except (OSError,NotImplementedError):self.skipTest('Symlink creation unavailable')
   self.assertTrue(self.engine().product_findings(r))
 def test_capabilities_match_actual_modules_and_examples(self):
  d=self.engine();catalog=json.loads((ROOT/'presets/capabilities.json').read_text())
  self.assertEqual(len(catalog['roles']),15)
  self.assertEqual(d.capability_findings(ROOT,catalog),[])
  bad=json.loads(json.dumps(catalog));bad['features'][0]['module']='muse_presets.does_not_exist'
  self.assertTrue(d.capability_findings(ROOT,bad))
 def test_advertised_native_authority_rejected(self):
  catalog=json.loads((ROOT/'presets/capabilities.json').read_text())
  catalog['external_effects_enabled']=True
  self.assertTrue(self.engine().capability_findings(ROOT,catalog))
 def test_all_promoted_modules_available(self):
  for name in ('builder_delivery','research_evaluator','numeric_evaluation','model_training_demo','model_toy_install','continuum_checkpoint','family_envelope','engineer_sourcekit','coordinator_sourcekit','model_builder_sourcekit','omnium_plan_review'):
   with self.subTest(module=name):self.assertIsNotNone(importlib.util.find_spec('muse_presets.'+name))
 def test_manifest_refresh_refuses_unknown_customer_files(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'README.md').write_text('# Product\n');(r/'control').mkdir();(r/'control/internal.json').write_text('{}')
   with self.assertRaises(ValueError):self.engine().refresh_manifest(r)
   self.assertFalse((r/'PUBLIC_SOURCE_MANIFEST.json').exists())
 def test_manifest_refresh_is_deterministic_and_audited(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'README.md').write_text('# Product\n')
   d=self.engine();a=d.refresh_manifest(r);first=(r/'PUBLIC_SOURCE_MANIFEST.json').read_bytes();b=d.refresh_manifest(r)
   self.assertEqual(first,(r/'PUBLIC_SOURCE_MANIFEST.json').read_bytes())
   self.assertEqual(a['files'],b['files'])
   self.assertEqual(a['files']['README.md'],hashlib.sha256((r/'README.md').read_bytes()).hexdigest())
 def test_generated_kit_guides_are_customer_facing(self):
  from muse_presets import engineer_sourcekit,model_builder_sourcekit,model_toy_sourcekit
  from muse_presets.distribution import _prose,WORK_ID
  for name,guide in (('software-engineer',engineer_sourcekit.START_HERE),('model-builder',model_builder_sourcekit.START_HERE),('toy-installer',model_toy_sourcekit.START)):
   with self.subTest(kit=name):self.assertIsNone(WORK_ID.search(_prose(guide)),name)
if __name__=='__main__':unittest.main()
