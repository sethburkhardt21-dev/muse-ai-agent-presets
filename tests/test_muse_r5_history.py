"""Current R5 additions cannot erase or rewrite historical collection content."""
from pathlib import Path
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
C=R/'collections/muse-starters-v1'
B=C/'r5/baseline'
ADMITTED={'data-cleaner':'data-engineer','operations-analyst':'reliability-engineer',
          'customer-support-designer':'automation-engineer','frontend-partner':'product-interface-designer'}
def read(p):return json.loads(p.read_text('utf-8'))
class HistoricalProjectionTests(unittest.TestCase):
    def test_original_evaluation_specs_and_workflows_remain_unchanged(self):
        for filename,key,count in [('evaluation_cases.json','skill_id',64),('workflows.json','id',20)]:
            old=read(B/filename);current=read(C/filename)
            self.assertEqual(len(old),count)
            self.assertEqual(current[:count],old)
            self.assertEqual(len({r[key] for r in current}),len(current))
    def test_original_starters_have_only_admitted_additions(self):
        old=read(B/'starters.json');current=read(C/'starters.json')
        self.assertEqual([p['id'] for p in current],[p['id'] for p in old])
        for before,after in zip(old,current):
            with self.subTest(starter=before['id']):
                if before['id'] not in ADMITTED:self.assertEqual(after,before);continue
                self.assertEqual(set(after),set(before)|{'specialist_role'})
                self.assertEqual(after['specialist_role'],ADMITTED[before['id']])
                for key,value in before.items():
                    if key in ('skills','workflows'):
                        self.assertEqual(after[key][:len(value)],value)
                        self.assertEqual(len(after[key]),len(set(after[key])))
                    else:self.assertEqual(after[key],value)
    def test_archived_json_bytes_match_original_unmodified_historical_manifest(self):
        manifest=read(C/'R3_BASELINE_ASSETS.json')['files']
        for name in ('evaluation_cases.json','starters.json','workflows.json'):
            self.assertEqual(hashlib.sha256((B/name).read_bytes()).hexdigest(),manifest['collections/muse-starters-v1/'+name])
    def test_r4_qualification_counts_are_history_not_current_inventory(self):
        counts=read(C/'COUNTS.json')
        self.assertEqual(counts['r4_focused_test_cases_at_qualification'],397)
        self.assertEqual(counts['r4_parent_test_cases_at_qualification'],2041)
        self.assertEqual(counts['initial_evaluation_case_specifications'],64)
        self.assertEqual(counts['current_evaluation_case_specifications'],75)
if __name__=='__main__':unittest.main()
