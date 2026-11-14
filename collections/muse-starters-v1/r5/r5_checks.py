"""Source-pinned R5 supplied-output checks, not native model evaluation.

The checker recomputes results from supplied inputs, never reference_output.
Its executable calculations have separate outcome and boundary tests. Shared
implementation assumptions remain; this is not an independent semantic judge.
"""
from pathlib import Path
import hashlib
import importlib.util
import math
import stat
import sys

PINS = {'__init__.py': '2f7425daff47627622a09b93e00529c78f5c89b36bfb3b831b4b17cf8961121b', 'common.py': '1db1285a6c29b4de133d8f00d905ad98bb9dc4cc031880ac1050b74588dd358d', 'data.py': 'a4dea39e5f2ec2a517e05da43dcaddc76e0fa549699930eb7bc412f5ca163b46', 'reliability.py': '131e9de1664079cc3aef32a75dc8e91b9a413cbfef0527770ccc41f7652b6199', 'automation.py': 'ffdb12c9bc5f96b6e8ee5c66b4bd195d3a0835a92c1c6561f1f8321ee19dd0b4', 'interface.py': '4544084233b5a036c9dbffbc8cfc9dd1120c4676d1f8bb829c3d05807017b54e'}
SKILLS = ('schema-evolution','incremental-pipeline','query-plan-review',
          'service-objectives','capacity-planning','incident-triage','automation-contract',
          'selector-resilience','effect-reconciliation','design-token-audit','interaction-state-coverage')


def _load():
    here=Path(__file__).absolute().parent
    candidates=[here/'specialist_extensions']
    if len(here.parents)>=3:
        candidates.append(here.parents[2]/'src'/'muse_presets'/'specialist_extensions')
    for root in candidates:
        if not root.exists():continue
        if root.is_symlink() or not root.is_dir():raise ValueError('R5 source root refused')
        for name,pin in PINS.items():
            file=root/name;info=file.lstat()
            if file.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size>250000:
                raise ValueError('R5 source member refused')
            if hashlib.sha256(file.read_bytes()).hexdigest()!=pin:
                raise ValueError('R5 source pin mismatch:'+name)
        alias='_muse_r5_checked_specialist_tools'
        spec=importlib.util.spec_from_file_location(alias,root/'__init__.py',submodule_search_locations=[str(root)])
        if spec is None or spec.loader is None:raise ValueError('R5 loader unavailable')
        module=importlib.util.module_from_spec(spec);sys.modules[alias]=module
        spec.loader.exec_module(module)
        return module.evaluate
    raise ValueError('R5 executable source closure missing')

_EVALUATE=_load()


def _equal(actual,expected,path='output'):
    if type(expected) is float:
        if type(actual) not in (int,float) or not math.isfinite(actual) or not math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError(path+': calculated number mismatch')
        return
    if type(actual) is not type(expected):raise ValueError(path+': type mismatch')
    if isinstance(expected,dict):
        if actual.keys()!=expected.keys():raise ValueError(path+': output fields mismatch')
        for key in expected:_equal(actual[key],expected[key],path+'.'+key)
    elif isinstance(expected,list):
        if len(actual)!=len(expected):raise ValueError(path+': list length mismatch')
        for i,(a,e) in enumerate(zip(actual,expected)):_equal(a,e,path+'['+str(i)+']')
    elif actual!=expected:raise ValueError(path+': calculated value mismatch')


def check(case,output):
    _equal(output,_EVALUATE(case['skill_id'],case['inputs']))

R5_CHECKS={skill:check for skill in SKILLS}
