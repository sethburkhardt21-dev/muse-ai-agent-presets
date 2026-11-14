"""Exercise both source-checkout and exported-practice checker closure."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest

# The same file works from repository tests/ and this bounded review snapshot.
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE if (HERE/'src').is_dir() else HERE/'source'
CHECKER = ROOT/'collections/muse-starters-v1/r5/r5_checks.py'
TOOLS = ROOT/'src/muse_presets/specialist_extensions'


def load(path):
    spec = importlib.util.spec_from_file_location('_r5_independent_test_checker', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('checker loader unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckerIsolationTests(unittest.TestCase):
    def setUp(self):
        self.old_aliases = {k:v for k,v in sys.modules.items()
                            if k.startswith('_muse_r5_checked_specialist_tools')}
        self.addCleanup(self.restore_aliases)

    def restore_aliases(self):
        for key in list(sys.modules):
            if key.startswith('_muse_r5_checked_specialist_tools'):
                del sys.modules[key]
        sys.modules.update(self.old_aliases)

    def test_source_checker_loads_repinned_closure(self):
        module = load(CHECKER)
        self.assertEqual(len(module.R5_CHECKS), 11)
        self.assertEqual(set(module.PINS), {p.name for p in TOOLS.glob('*.py')})

    def test_exported_practice_checker_loads_without_repository(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(TOOLS,root/'specialist_extensions')
            shutil.copyfile(CHECKER,root/'r5_checks.py')
            module = load(root/'r5_checks.py')
            result = module._EVALUATE('capacity-planning', {
                'demand_rps':'900','per_instance_rps':'250','target_utilization':'0.6',
                'instances':4,'reserve_instances':1})
            self.assertEqual(result['required_instances'],7)

    def test_correct_fixed_threshold_output_accepted(self):
        module = load(CHECKER)
        case = {'skill_id':'design-token-audit','inputs':{
            'tokens':{'ink':'#000000','paper':'#000000'},
            'pairs':[{'id':'text','foreground':'ink','background':'paper',
                      'minimum_ratio':'1.000000000000000001'}]}}
        output = module._EVALUATE(case['skill_id'],case['inputs'])
        self.assertEqual(output['status'],'fail')
        self.assertIsNone(module.check(case,output))

    def test_stale_false_pass_output_is_rejected(self):
        module = load(CHECKER)
        case = {'skill_id':'design-token-audit','inputs':{
            'tokens':{'ink':'#000000','paper':'#000000'},
            'pairs':[{'id':'text','foreground':'ink','background':'paper',
                      'minimum_ratio':'1.000000000000000001'}]}}
        output = module._EVALUATE(case['skill_id'],case['inputs'])
        bad = copy.deepcopy(output)
        bad['status']='pass';bad['pairs'][0]['passed']=True
        with self.assertRaisesRegex(ValueError,'mismatch'):
            module.check(case,bad)

    def test_tampered_source_is_refused_before_import(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(TOOLS,root/'specialist_extensions')
            shutil.copyfile(CHECKER,root/'r5_checks.py')
            file = root/'specialist_extensions/__init__.py'
            file.write_bytes(b'raise AssertionError("TAMPER_EXECUTED")\n'+file.read_bytes())
            with self.assertRaisesRegex(ValueError,'source pin mismatch:__init__.py'):
                load(root/'r5_checks.py')

    def test_existing_non_numeric_tool_still_accepted(self):
        module = load(CHECKER)
        case = {'skill_id':'schema-evolution','inputs':{
            'current':[],'proposed':[{'name':'id','type':'integer','nullable':False}],
            'row_count':0}}
        output=module._EVALUATE(case['skill_id'],case['inputs'])
        self.assertEqual(output['status'],'compatible')
        self.assertIsNone(module.check(case,output))


if __name__=='__main__':unittest.main()
