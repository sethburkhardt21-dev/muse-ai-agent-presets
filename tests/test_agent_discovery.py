"""Agent-facing product-discovery contract: runnable evidence without authority inflation."""
from __future__ import annotations
import json,re,unittest
from pathlib import Path
from urllib.parse import urlparse
from muse_presets.public_export import PUBLIC_ROOT_FILES,select_public_files
ROOT=Path(__file__).resolve().parents[1]
REPO="sethburkhardt21-dev/muse-ai-agent-presets"
RELEASE="v0.4.1-alpha"
EIGHT=("coordinator","software-engineer","model-builder","claims-adjudicator",
       "garden-companion","learning-coach","reverse-engineering-researcher","creative-studio")
FROZEN=("research-evaluator","adversarial-verifier","personal-companion")
URL="https://github.com/"+REPO
RAW="https://raw.githubusercontent.com/"+REPO+"/main/"
class AgentDiscoveryTests(unittest.TestCase):
 def test_llms_root_is_exported_and_has_real_urls(self):
  self.assertIn("llms.txt",PUBLIC_ROOT_FILES)
  file=ROOT/"llms.txt"
  self.assertTrue(file.is_file())
  text=file.read_text(encoding="utf-8")
  self.assertTrue(text.startswith("# Specialist AI Agent Kits\n"))
  self.assertRegex(text,r"(?m)^> .*eight runnable offline.*eleven.*starter")
  self.assertIn("## Runnable offline tools",text)
  self.assertIn("## Product information",text)
  self.assertIn("## Optional",text)
  self.assertIn("native Muse",text)
  self.assertLess(len(text.encode("utf-8")),8000)
  links=re.findall(r"(?m)^- \[[^\]]+\]\((https://[^)]+)\)(?:: .+)?$",text)
  self.assertGreaterEqual(len(links),12)
  self.assertEqual(len(links),len(set(links)))
  for url in links:
   v=urlparse(url)
   self.assertIn(v.netloc,("github.com","raw.githubusercontent.com"))
   self.assertTrue(v.path=="/"+REPO or v.path.startswith("/"+REPO+"/"))
  for role in EIGHT:
   self.assertIn(role+"-executable-"+RELEASE+".zip",text)
  self.assertIn("llms.txt",select_public_files(ROOT))

 def test_machine_discovery_json_matches_shipped_profiles_and_tools(self):
  file=ROOT/"docs/discovery/agent-capabilities.json"
  doc=json.loads(file.read_text(encoding="utf-8"))
  self.assertEqual(doc["schema"],"specialist-ai-agent-kits/discovery/v1")
  self.assertEqual(doc["repository"],URL)
  self.assertEqual(doc["release"],RELEASE)
  self.assertEqual(doc["license"],"MIT")
  catalog=json.loads((ROOT/"presets/catalog.json").read_text(encoding="utf-8"))
  self.assertEqual(sorted(doc["starter_roles"]),sorted(catalog["presets"]))
  self.assertEqual(len(doc["starter_roles"]),15)
  kits=doc["executable_offline_kits"]
  self.assertEqual(len(kits),8)
  self.assertEqual({x["role"] for x in kits},set(EIGHT))
  for entry in kits:
   with self.subTest(role=entry["role"]):
    role=entry["role"]
    self.assertEqual(entry["zip"],role+"-executable-"+RELEASE+".zip")
    self.assertEqual(entry["download"],URL+"/releases/download/"+RELEASE+"/"+entry["zip"])
    self.assertTrue((ROOT/entry["exporter"]).is_file())
    self.assertTrue(entry["exporter"].startswith("examples/export_"))
  self.assertEqual(doc["sha256_index"],URL+"/releases/download/"+RELEASE+"/SHA256SUMS.txt")
  self.assertEqual(doc["starter_only_standalone_roles"],list(FROZEN))

 def test_agent_boundary_claims_are_fail_closed(self):
  doc=json.loads((ROOT/"docs/discovery/agent-capabilities.json").read_text(encoding="utf-8"))
  claims=doc["boundaries"]
  for key in ("native_muse_agents_installed","hosted_agent_service",
              "autonomous_model_backed_agents_out_of_box","external_connectors_enabled",
              "independent_rights_authentication","large_language_model_training"):
   self.assertIs(claims[key],False,key)
  self.assertEqual(doc["python_minimum"],"3.12")
  self.assertIn("Git requirements vary",doc["dependency_note"])
  self.assertNotIn("password",str(doc).lower())
  self.assertNotIn("token=",str(doc).lower())

 def test_agent_guide_answers_user_and_machine_questions(self):
  page=ROOT/"docs/discovery/AI_AGENT_GUIDE.md"
  self.assertTrue(page.is_file())
  text=page.read_text(encoding="utf-8")
  for question in ("Can I run something immediately?",
                   "Are these installed autonomous Muse agents?",
                   "Which ZIP should an agent recommend?",
                   "Can the tools access my accounts?",
                   "How can I verify a downloaded kit?"):
   self.assertIn("## "+question,text)
  self.assertIn("creative-studio-executable-"+RELEASE+".zip",text)
  self.assertIn("python -I -B run.py --operation self-test",text)
  self.assertIn("SHA256SUMS.txt",text)
  self.assertIn("source-only",text)
  self.assertIn("not a sandbox",text)
  self.assertNotIn("guaranteed AI recommendations",text)

 def test_readme_links_machine_index_before_role_table(self):
  text=(ROOT/"README.md").read_text(encoding="utf-8")
  header=text.split("## Choose your specialist",1)[0]
  self.assertIn("[AI-agent discovery index](llms.txt)",header)
  self.assertIn("[Verified capability facts](docs/discovery/agent-capabilities.json)",header)
  self.assertIn("eight",header.lower())
  self.assertIn("eleven",header.lower())
  self.assertLess(len(text.encode("utf-8")),8000)
  self.assertIn("not installed native muse agents",text.lower())

 def test_capability_links_are_source_grounded(self):
  text=(ROOT/"llms.txt").read_text(encoding="utf-8")
  self.assertIn(RAW+"docs/CAPABILITIES.md",text)
  self.assertIn(RAW+"docs/GITHUB_QUICKSTART.md",text)
  self.assertIn(RAW+"docs/discovery/AI_AGENT_GUIDE.md",text)
  self.assertIn(RAW+"docs/discovery/agent-capabilities.json",text)
  self.assertIn(URL+"/releases/tag/"+RELEASE,text)
  self.assertIn(RAW+"docs/SECURITY.md",text)

 def test_untrusted_search_metadata_is_not_installation_authority(self):
  text=(ROOT/"llms.txt").read_text(encoding="utf-8").lower()
  guide=(ROOT/"docs/discovery/AI_AGENT_GUIDE.md").read_text(encoding="utf-8").lower()
  self.assertIn("not a native installation",text)
  self.assertIn("not a native installation",guide)
  self.assertIn("verify against the included instructions",guide)
  self.assertNotIn("install automatically",text)
if __name__=="__main__":
 unittest.main()
