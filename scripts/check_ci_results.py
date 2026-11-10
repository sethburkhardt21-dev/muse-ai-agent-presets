"""Fail the stable required check unless every upstream job succeeded."""
from __future__ import annotations
import json
import os
import sys

REQUIRED=frozenset({'source-tests','public-quality'})

def check_results(results:object)->bool:
    if type(results) is not dict or set(results)!=REQUIRED:
        raise ValueError('REQUIRED_CI_JOBS_MISSING_OR_UNEXPECTED')
    for name in sorted(REQUIRED):
        record=results[name]
        if type(record) is not dict or record.get('result')!='success':
            raise ValueError('REQUIRED_CI_JOB_NOT_SUCCESS:'+name)
    return True

def main()->int:
    try:
        check_results(json.loads(os.environ.get('NEEDS_JSON','null')))
    except (ValueError,TypeError) as exc:
        print(json.dumps({'status':'FAIL','reason':str(exc)},sort_keys=True))
        return 2
    print(json.dumps({'status':'PASS','required_jobs':sorted(REQUIRED)},sort_keys=True))
    return 0

if __name__=='__main__':sys.exit(main())
