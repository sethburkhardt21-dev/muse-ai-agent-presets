"""Regression: community host declarations include user-instance placeholders."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("catalog_cli",ROOT/"scripts/connector_catalog.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class HostDescriptorTests(unittest.TestCase):
 def test_pinned_instance_host_descriptors_are_not_rejected_as_urls(self):
  data=json.loads((ROOT/"docs/connectors/catalog.json").read_bytes())
  hosts={x["id"]:x["allowed_hosts"] for x in data["connectors"]}
  self.assertIn("your n8n instance host",hosts["n8n"])
  self.assertIn("<your-shop>.myshopify.com",hosts["shopify"])
  self.assertEqual(len(module.validate_catalog(data)["connectors"]),151)
 def test_host_description_refuses_control_characters_and_external_schemes(self):
  for value in ("https://attacker.invalid","javascript:alert(1)","example\x00.test","example\n.test"):
   with self.subTest(value=value):
    data=json.loads((ROOT/"docs/connectors/catalog.json").read_bytes())
    data["connectors"][0]["allowed_hosts"]=[value]
    with self.assertRaisesRegex(ValueError,"INVALID_ALLOWED_HOST"):module.validate_catalog(data)
if __name__=="__main__":unittest.main()
