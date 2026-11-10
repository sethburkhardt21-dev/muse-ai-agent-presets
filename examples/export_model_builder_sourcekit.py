"""Create one self-contained source-only Model Builder ZIP, never a live installation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile
from muse_presets.model_builder_dropin import stage_model_builder_dropin
from muse_presets.model_builder_sourcekit import export_model_builder_sourcekit


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to",type=Path,required=True,help="new absolute .zip destination")
    args=parser.parse_args(argv)
    try:
        if not args.to.is_absolute() or args.to.suffix.lower()!=".zip":
            raise ValueError("ABSOLUTE_NEW_ZIP_DESTINATION_REQUIRED")
        with tempfile.TemporaryDirectory(prefix="model-builder-export-") as scratch:
            source=Path(scratch)/"model-builder"
            stage_model_builder_dropin(source)
            report=export_model_builder_sourcekit(source,args.to)
        print(json.dumps(report,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as exc:
        print(json.dumps({"status":"REFUSED","reason":str(exc),
                          "native_installed":False,"external_effect_authorized":False},sort_keys=True))
        return 2

if __name__=="__main__":raise SystemExit(main())
