"""Reader-facing product contracts for the additive specialist collection."""
from pathlib import Path
import json,re,unittest
R=Path(__file__).resolve().parents[1]
C=R/'collections/muse-starters-v1'
class ProductDocumentationTests(unittest.TestCase):
    def test_readme_explains_current_product_and_actual_first_use(self):
        text=(R/'README.md').read_text('utf-8')
        for term in ('15 specialists','75 skills','25 workflows','100 starters',
                     'tools/muse_collection.py demo data-engineer',
                     'docs/collection/SPECIALIST_QUICKSTART.md','docs/collection/SPECIALIST_CATALOG.md'):
            self.assertIn(term,text)
        self.assertLess(len(text.encode()),8000)
    def test_unified_catalog_covers_fifteen_real_packages(self):
        path=R/'docs/collection/SPECIALIST_CATALOG.md';self.assertTrue(path.is_file())
        text=path.read_text('utf-8')
        roles=json.loads((C/'specialists.json').read_text('utf-8'))
        self.assertEqual(len(roles),15)
        for role in roles:self.assertIn(role['id'],text)
        self.assertIn('eleven-role protocol',text)
        self.assertIn('not installed',text)
    def test_new_product_links_resolve(self):
        paths=['docs/collection/SPECIALIST_QUICKSTART.md','docs/collection/SPECIALIST_CATALOG.md',
               'collections/muse-starters-v1/README.md','collections/muse-starters-v1/SKILL_INDEX.md']
        for path in paths:
            page=R/path;self.assertTrue(page.is_file())
            for link in re.findall(r'\]\(([^)#]+)(?:#[^)]+)?\)',page.read_text('utf-8')):
                if '://' not in link:self.assertTrue((page.parent/link).exists(),path+':'+link)
    def test_current_collection_docs_do_not_use_old_inventory_as_current(self):
        page=(C/'README.md').read_text('utf-8')
        intro=page.split('## R4 source qualification')[0]
        self.assertIn('75 reusable skills',intro);self.assertIn('25 workflows',intro)
        self.assertNotIn('Current depth: R4',intro)
        self.assertIn('## R4 source qualification',page)
if __name__=='__main__':unittest.main()
