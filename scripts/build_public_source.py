#!/usr/bin/env python3
"""Create a history-free GitHub source ZIP; NEVER pushes to GitHub."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

def main() -> int:
    parser=argparse.ArgumentParser(description="Build a clean, history-free generic agent source ZIP")
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1],
                        help="Frozen source directory (defaults to parent of scripts/)")
    parser.add_argument("--to",type=Path,required=True,
                        help="New ZIP path outside the source tree")
    parser.add_argument("--forbidden-terms-file",type=Path,default=None,
                        help="Operator-owned denylist path outside source; never published")
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    sys.path.insert(0,str(root/"src"))
    from muse_presets.public_export import export_public_snapshot, PublicExportError
    try:
        terms=()
        if args.forbidden_terms_file is not None:
            private=args.forbidden_terms_file
            if (private.is_symlink() or not private.is_file()
                or private.stat().st_size>16384
                or private.resolve(strict=True).is_relative_to(root)):
                raise PublicExportError("INVALID_OPERATOR_PRIVATE_DENYLIST")
            terms=tuple(line.strip() for line in private.read_text(encoding="utf-8").splitlines()
                        if line.strip())
            if len(terms)>128:
                raise PublicExportError("OPERATOR_DENYLIST_TOO_LONG")
        result=export_public_snapshot(root,args.to,forbidden_terms=terms)
    except (PublicExportError,ValueError,OSError) as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc),
                          "public_git_pushed":False},sort_keys=True))
        return 2
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
