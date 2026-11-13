"""Public copy must distinguish running offline tools from installing native agents."""
from __future__ import annotations
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
README=(ROOT/"README.md")
QUICK=(ROOT/"docs/GITHUB_QUICKSTART.md")
RELEASES=(ROOT/"docs/RELEASES.md")

class ProductPositioningTests(unittest.TestCase):
    def test_readme_leads_with_runnable_tools(self):
        value=README.read_text(encoding="utf-8")
        hero=value.split("## Choose your specialist",1)[0].lower()
        self.assertIn("eight runnable offline python tools",hero)
        self.assertIn("fifteen customizable specialist",hero)
        self.assertIn("v0.4.1-alpha",hero)
        self.assertIn("not installed",hero)
        self.assertIn("native muse",hero)

    def test_readme_links_to_real_executable_not_just_starter(self):
        value=README.read_text(encoding="utf-8")
        self.assertIn("creative-studio-executable-v0.4.1-alpha.zip",value)
        self.assertIn("python -I -B run.py --operation self-test",value)
        self.assertIn('python -I -B run.py --operation demo --to "$HOME/creative-production-demo"',value)
        self.assertIn("SHA256SUMS.txt",value)
        self.assertIn("not a model-backed autonomous assistant",value.lower())

    def test_quickstart_gives_no_clone_executable_route(self):
        quick=QUICK.read_text(encoding="utf-8")
        self.assertIn("## Run a standalone tool without cloning",quick)
        self.assertIn("creative-studio-executable-v0.4.1-alpha.zip",quick)
        self.assertIn("python -I -B run.py --operation self-test",quick)
        self.assertIn('python -I -B run.py --operation demo --to "$HOME/creative-production-demo"',quick)
        self.assertIn("Python 3.12+; Git is not required",quick)
        self.assertIn("For this Creative Studio example",quick)
        self.assertIn("Software Engineer workflows may require Git",quick)
        self.assertNotIn("For executable ZIPs: Python 3.12+ only.",quick)
        self.assertRegex(quick,r"Need a ZIP instead of a clone[^\n]+v0\.4\.1-alpha")
        self.assertIn("not connected",quick.lower())

    def test_release_page_explains_two_products(self):
        releases=RELEASES.read_text(encoding="utf-8").lower()
        self.assertIn("eight runnable",releases)
        self.assertIn("eleven starter",releases)
        self.assertIn("no native muse",releases)
        self.assertIn("not a model-backed autonomous assistant",releases)
        self.assertIn("v0.4.1-alpha",releases)

if __name__=="__main__":
    unittest.main()
