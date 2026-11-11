"""Explicit offline Creative Studio operations; no automatic execution or overwrite."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from . import creative_production as cp


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("INVALID_ARGUMENTS:" + message)


def main(argv=None, *, sample_path: Path, kit_root: Path | None = None) -> int:
    try:
        parser = _Parser(description=__doc__)
        parser.add_argument('--operation', choices=('demo','compile','verify','diff'), required=True)
        for name in ('to','brief','project','before','after'):
            parser.add_argument('--'+name, type=Path)
        parser.add_argument('--sha256')
        args = parser.parse_args(argv)
        required = {'demo': {'to'}, 'compile': {'brief','to'}, 'verify': {'project','sha256'}, 'diff': {'before','after'}}[args.operation]
        present = {key for key,value in vars(args).items() if key!='operation' and value is not None}
        if present != required:
            raise ValueError('ARGUMENT_SET_MISMATCH:' + args.operation)
        if kit_root is not None:
            root = kit_root.resolve(strict=True)
            for key in present-{'sha256'}:
                path = cp.safe_path(getattr(args,key))
                if path.resolve(strict=False).is_relative_to(root):
                    raise ValueError('USER_PATH_MUST_BE_OUTSIDE_IMMUTABLE_KIT')
        if args.operation in ('demo','compile'):
            source = sample_path if args.operation=='demo' else args.brief
            output = cp.export_project(cp.load_brief(source), args.to)
        elif args.operation=='verify':
            output = cp.verify_project(args.project,args.sha256)
        else:
            output = cp.compare_briefs(cp.load_brief(args.before),cp.load_brief(args.after))
        print(json.dumps(output,sort_keys=True,ensure_ascii=False))
        return 0
    except (ValueError,OSError,TypeError,KeyError,UnicodeError,RecursionError) as exc:
        print(json.dumps({'status':'REFUSED','reason':type(exc).__name__+':'+str(exc)[:220],
                          'native_installed':False,'media_rendered':False,'external_effects_authorized':False},sort_keys=True))
        return 2
