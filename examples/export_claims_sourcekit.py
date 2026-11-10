"""Export or verify the self-contained offline Claims Adjudicator ZIP."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from muse_presets.claims_sourcekit import export_claims_sourcekit,verify_claims_sourcekit

ROOT=Path(__file__).resolve().parents[1]
def main(argv=None)->int:
    p=argparse.ArgumentParser(description="Build or verify a source-only Claims kit")
    commands=p.add_mutually_exclusive_group(required=True)
    commands.add_argument("--to",type=Path,help="New ZIP file; never overwrite")
    commands.add_argument("--verify",type=Path,help="Previously created ZIP")
    p.add_argument("--sha256",help="Expected SHA-256, required with --verify")
    opts=p.parse_args(argv)
    try:
        if opts.to:
            if opts.sha256 is not None:raise ValueError("EXPORT_CANNOT_ACCEPT_EXTERNAL_PIN")
            result=export_claims_sourcekit(ROOT,opts.to)
        else:
            if not opts.sha256:raise ValueError("EXTERNAL_ZIP_SHA256_REQUIRED")
            result=verify_claims_sourcekit(ROOT,opts.verify,opts.sha256)
        print(json.dumps(result,sort_keys=True))
        return 0
    except (ValueError,OSError,FileExistsError) as exc:
        print(json.dumps({"status":"REFUSED","reason":type(exc).__name__+":"+str(exc)[:220],
                          "native_installed":False,"external_effect_authorized":False},
                          sort_keys=True))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
