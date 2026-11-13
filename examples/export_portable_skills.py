"""Export a separate portable instruction library; never install a native agent."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
# Only the checked-out local source is loaded; no package install or network.
sys.path.insert(0,str(ROOT/'src'))
from muse_presets.portable_skill_export import (plan_portable_skills,
    stage_portable_skills,inspect_portable_skills)


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description='Create-only 50-skill instruction export; no native installation')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan',action='store_true',help='Read-only source and output inventory')
    mode.add_argument('--to',type=Path,help='New destination folder; existing paths refuse')
    mode.add_argument('--inspect',type=Path,help='Compare a created library against this source checkout')
    args=parser.parse_args(argv)
    try:
        if args.plan:report=plan_portable_skills()
        elif args.to is not None:
            plan=plan_portable_skills()
            report=stage_portable_skills(args.to,expected_source_sha256=plan['source_sha256'])
        else:report=inspect_portable_skills(args.inspect)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        report={'status':'REFUSED','reason':str(exc),'native_installed':False,'external_effect_authorized':False}
    print(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=True))
    return 0 if report['status'] in ('SOURCE_PLAN_ONLY','LOCAL_PORTABLE_SKILLS_STAGED','LOCAL_PORTABLE_SKILLS_MATCH') else 2


if __name__=='__main__':raise SystemExit(main())
