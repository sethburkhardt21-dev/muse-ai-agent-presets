"""Create or verify a pinned standalone offline Creative Studio ZIP."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from muse_presets.creative_sourcekit import export_creative_sourcekit,verify_creative_sourcekit
ROOT=Path(__file__).resolve().parents[1]
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--to',type=Path);g.add_argument('--verify',type=Path)
    p.add_argument('--sha256');a=p.parse_args(argv)
    try:
        if a.to is not None:
            if a.sha256 is not None:raise ValueError('EXPORT_DOES_NOT_ACCEPT_EXTERNAL_DIGEST')
            result=export_creative_sourcekit(ROOT,a.to)
        else:result=verify_creative_sourcekit(ROOT,a.verify,a.sha256)
        print(json.dumps(result,sort_keys=True));return 0
    except (ValueError,OSError) as e:
        print(json.dumps({'status':'REFUSED','reason':type(e).__name__+':'+str(e)[:180],
                          'native_installed':False,'media_rendered':False,'external_effects_authorized':False},sort_keys=True));return 2
if __name__=='__main__':raise SystemExit(main())
