"""CLI for checking and rendering local drafts; no account/network effects."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .catalog import load_registry, load_preset, validate_catalog, render_preset
from .family import propose_handoff


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='Unofficial Muse AI agent presets — offline source tooling')
    sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('list',help='List neutral specialist roles')
    sub.add_parser('doctor',help='Validate local catalog and default-deny policy')
    renderer=sub.add_parser('render',help='Create one draft profile, never install into Muse')
    renderer.add_argument('--preset',required=True)
    renderer.add_argument('--to',type=Path,required=True)
    renderer.add_argument('--name',default=None)
    preview=sub.add_parser('family-preview',help='Validate a proposal without sending it')
    preview.add_argument('--from-role',dest='from_role',required=True)
    preview.add_argument('--to-role',dest='to_role',required=True)
    preview.add_argument('--request-id',required=True)
    preview.add_argument('--capability',default='review')
    args=ap.parse_args(argv)
    if args.command=='list':
        print('\n'.join(f"{s}: {load_preset(s)['title']}" for s in load_registry()['presets']))
        return 0
    if args.command=='doctor':
        errors=validate_catalog()
        print(json.dumps({'status':'PASS' if not errors else 'FAIL','errors':errors,'native_muse_status':'NOT_CHECKED'},indent=2))
        return 0 if not errors else 2
    try:
        if args.command=='render':
            dest=render_preset(args.preset,args.to,display_name=args.name)
            print(json.dumps({'status':'LOCAL_DRAFT_CREATED','destination':str(dest),'native_installed':False},indent=2))
        else:
            print(json.dumps(propose_handoff(args.from_role,args.to_role,request_id=args.request_id,capability=args.capability),indent=2))
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc)}))
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
