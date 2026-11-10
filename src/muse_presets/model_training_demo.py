"""Opt-in role adapter for the existing bounded decimal-linear experiment.

Reuses R60 math, evidence and exact restoration unchanged. Runs only a fictional
fixture in a newly owned temporary directory; no provider or deployment grants.
"""
from __future__ import annotations
from pathlib import Path
import tempfile
if __package__:
    from . import model_toy_math as math
    from . import model_toy_bundle as bundle
    from .model_toy_fixture import example_dataset
else:
    import model_toy_math as math
    import model_toy_bundle as bundle
    from model_toy_fixture import example_dataset


def run_linear_demo(*, allow_training: bool = False) -> dict:
    if allow_training is not True:
        raise ValueError('EXPLICIT_LOCAL_TRAINING_OPT_IN_REQUIRED')
    with tempfile.TemporaryDirectory(prefix='model-builder-linear-demo-') as temp:
        root=Path(temp).resolve()
        dataset=root/'dataset.json'
        raw=math.canonical_json(example_dataset())
        dataset.write_bytes(raw)
        run=bundle.run_experiment(dataset,math.digest(raw),root/'experiment',
                                  reviewed_data=True,steps=64,learning_rate='0.05')
        verified=bundle.verify_bundle(root/'experiment',run['receipt_sha256'])
        restored=bundle.restore_baseline(root/'experiment',run['receipt_sha256'],root/'restored.json')
        baseline=(root/'experiment/baseline.json').read_bytes()
        if ((root/'restored.json').read_bytes()!=baseline or
            restored['sha256']!=math.digest(baseline) or
            verified['status']!='LOCAL_TOY_BUNDLE_RECOMPUTED' or
            verified['optimizer_steps']!=64 or verified['final_status']!='HELD_UNEVALUATED'):
            raise ValueError('LINEAR_DEMO_READBACK_OR_ROLLBACK_MISMATCH')
        evaluation=verified['evaluation']
        return {'status':'LOCAL_LINEAR_MODEL_DEMO_PASSED',
            'model_family':'bounded-decimal-linear-regression',
            'optimizer_steps':64,'bundle_recomputed':True,
            'baseline_restored_byte_exact':True,
            'candidate_sha256':verified['candidate_sha256'],
            'baseline_sha256':verified['baseline_sha256'],
            'baseline_mse':evaluation['baseline_mse'],
            'candidate_mse':evaluation['candidate_mse'],
            'final_status':'HELD_UNEVALUATED','promotion_authorized':False,
            'native_tool_invoked':False,'external_effect_authorized':False,
            'independent_reviewer_verified':False,'os_sandboxed':False,
            'gpu_used':False,'network_used':False}
