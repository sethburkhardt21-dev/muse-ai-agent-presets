"""Source catalog content must be public-safe without losing real service names."""
from pathlib import Path
import json,sys,tempfile,unittest
from muse_presets.distribution import product_findings
from muse_presets.neutrality import audit_public_tree
ROOT=Path(__file__).resolve().parents[1]

class ProductSanitizationTests(unittest.TestCase):
 def test_asana_service_name_is_valid_in_connector_directory(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"docs"/"connectors";p.mkdir(parents=True)
   (p/"CATALOG.md").write_text("# Connector directory\nAsana manages team tasks.\n",encoding="utf8")
   self.assertEqual(product_findings(Path(d)),[])
 def test_nonservice_internal_markers_remain_blocked(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"docs"/"connectors";p.mkdir(parents=True)
   (p/"CATALOG.md").write_text("# Directory\nAsana prepush notes R123.\n",encoding="utf8")
   self.assertIn("INTERNAL_WORK_LANGUAGE",[x["reason"] for x in product_findings(Path(d))])
 def test_normalized_connector_metadata_has_no_private_paths_or_emails(self):
  doc=ROOT/"docs/connectors/catalog.json"
  self.assertNotIn("PERSONAL_EMAIL_REVIEW_REQUIRED",[x["reason"] for x in audit_public_tree(doc.parent.parent.parent) if x["path"]=="docs/connectors/catalog.json"])
  self.assertNotIn("PRIVATE_HOST_PATH",[x["reason"] for x in audit_public_tree(doc.parent.parent.parent) if x["path"]=="docs/connectors/catalog.json"])
if __name__=="__main__":unittest.main()
