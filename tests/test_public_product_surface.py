"""Public distribution must read like a product, not an engineering work log.

Runs on the public source tree only. Current-tree checks do not alter Git
history or old release assets. Source-only capability claims stay truthful.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

from muse_presets.public_export import select_public_files

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"
ROLE_SLUGS={
 "coordinator","software-engineer","model-builder","research-evaluator",
 "creative-studio","adversarial-verifier","personal-companion",
 "garden-companion","learning-coach","claims-adjudicator",
 "reverse-engineering-researcher","data-engineering-architect",
 "infrastructure-reliability-engineer","automation-engineer",
 "product-interface-designer",
}
VISITOR_DOCS={
 "CAPABILITIES.md","CUSTOMIZE.md","SKILLS.md","CONNECTORS.md",
 "RELEASES.md","SECURITY.md","GITHUB_QUICKSTART.md",
 "EXTENDING_GENERIC_AGENTS.md",
}
INTERNAL_DOCS={
 "CAPABILITY_FIT_AUDIT.md","COMMUNITY_RESEARCH.md",
 "COMMUNITY_ROLE_INTEGRATIONS.md","FIVE_LAYERS_AND_DOORS.md",
 "GENERIC_NATIVE_ACCEPTANCE.md","GENERIC_SPECIALIST_SHOWCASE.md",
 "GITHUB_RELEASE_SCOPE.md","GITHUB_ROLE_ACCEPTANCE.md",
 "NEUTRALITY_AND_PROVENANCE.md","PRIORITY_TRANSFERS.md",
 "PRIVACY_RELEASE_ASSURANCE.md","RELEASE_CHECKLIST.md","ROADMAP.md",
 "SECURITY_AND_RIGHTS.md","SEO_AND_DISCOVERY.md","STATUS.md",
}
MARKDOWN=re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
WORK_MARKERS=re.compile(
 r"\b(?:Asana|T\d{2}|R\d{2}|prepush|private[- ]main|"
 r"source candidate|release gate|scratch)\b",re.I)


class PublicProductSurfaceTests(unittest.TestCase):
 def test_readme_is_short_product_entrypoint(self):
  readme=(ROOT/"README.md").read_text(encoding="utf-8")
  self.assertLess(len(readme.encode("utf-8")),8000)
  for text in ("# Muse Specialist Toolkit","v0.4.1-alpha","docs/CAPABILITIES.md",
               "docs/GITHUB_QUICKSTART.md","MIT","source-only"):
   self.assertIn(text,readme)
  for role in ROLE_SLUGS:
   self.assertIn("presets/"+role+"/",readme)
  self.assertIsNone(WORK_MARKERS.search(re.sub(r"\]\([^)]+\)", "]()", readme)))

 def test_no_internal_docs_or_milestone_filenames(self):
  current={p.name for p in DOCS.glob("*.md")}
  self.assertFalse(current & INTERNAL_DOCS,sorted(current & INTERNAL_DOCS))
  self.assertFalse([x for x in current if re.match(r"R\d\d[_-]",x)])
  self.assertLessEqual(len(current),18)

 def test_all_product_docs_exist_and_read_as_product(self):
  for name in VISITOR_DOCS:
   with self.subTest(document=name):
    path=DOCS/name
    self.assertTrue(path.is_file(),name)
    text=path.read_text(encoding="utf-8")
    self.assertTrue(text.startswith("# "),name)
    self.assertIsNone(WORK_MARKERS.search(re.sub(r"\]\([^)]+\)", "]()", text)),name)
  self.assertIn("not connected",(DOCS/"CONNECTORS.md").read_text().lower())

 def test_catalog_and_eleven_role_capabilities_are_visible(self):
  data=json.loads((ROOT/"presets/catalog.json").read_text(encoding="utf-8"))
  self.assertEqual(set(data["presets"]),ROLE_SLUGS)
  caps=(DOCS/"CAPABILITIES.md").read_text(encoding="utf-8")
  skills=(DOCS/"SKILLS.md").read_text(encoding="utf-8")
  connectors=(DOCS/"CONNECTORS.md").read_text(encoding="utf-8")
  for role in ROLE_SLUGS:
   self.assertIn(role,caps)
   self.assertIn(role,skills)
   self.assertIn(role,connectors)
  self.assertIn("Template only",caps)
  self.assertIn("Windows",caps)
  self.assertIn("native",skills.lower())
  self.assertIn("source-only",caps.lower())

 def test_published_download_links_present_without_private_credential_urls(self):
  text="\n".join((ROOT/x).read_text(encoding="utf-8")
                 for x in ("README.md","CHANGELOG.md","docs/RELEASES.md"))
  self.assertIn("releases/tag/v0.2.0-alpha",text)
  self.assertIn("releases/tag/software-engineer-sourcekit-r56-alpha",text)
  self.assertNotIn("token=",text.lower())
  self.assertNotIn("sethburkhardt21-dev/muse-ai-agent-presets-r32" + "-private",text)

 def test_relative_markdown_links_resolve_across_visible_source(self):
  pages=[ROOT/"README.md",ROOT/"CHANGELOG.md",ROOT/"CONTRIBUTING.md",
         ROOT/"SECURITY.md"]
  pages.extend(DOCS.rglob("*.md"))
  pages.extend((ROOT/"presets").rglob("*.md"))
  pages.extend((ROOT/"services").rglob("*.md"))
  broken=[]
  for page in pages:
   if not page.is_file():continue
   body=page.read_text(encoding="utf-8")
   for match in MARKDOWN.finditer(body):
    raw=match.group(1).strip().split("#",1)[0].split("?",1)[0]
    if not raw or raw.startswith(("https://","http://","mailto:","data:","#")):
     continue
    if (raw.startswith("<") or raw.startswith("!") or
        raw.startswith("git+")):continue
    if not (page.parent/raw).resolve().exists():
     broken.append((page.relative_to(ROOT).as_posix(),raw))
  self.assertEqual(broken,[])

 def test_public_manifest_matches_current_file_bytes(self):
  manifest=json.loads((ROOT/"PUBLIC_SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
  selected=select_public_files(ROOT)
  self.assertEqual(manifest["source_file_count"],len(selected))
  self.assertEqual(manifest["files"],
                   {name:hashlib.sha256(raw).hexdigest() for name,raw in selected.items()})
  self.assertTrue(manifest["private_git_history_excluded"])
  self.assertFalse(manifest["owner_state_included"])

 def test_ci_cannot_bypass_product_surface_checks(self):
  workflow=(ROOT/".github/workflows/checks.yml").read_text(encoding="utf-8")
  self.assertIn("python -m unittest discover -s tests -v",workflow)
  self.assertIn("audit-neutrality",workflow)
  self.assertTrue((ROOT/"tests/test_public_product_surface.py").is_file())


if __name__=="__main__":
 unittest.main()
