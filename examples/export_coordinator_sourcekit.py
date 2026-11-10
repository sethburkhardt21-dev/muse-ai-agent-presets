"""Build one pristine offline Coordinator runtime ZIP without native installation.

Operator-supplied destination must be a new ZIP under an existing parent.
All profiles are neutral synthetic source, with disabled skills and no grants.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from muse_presets.coordinator_dropin import (
    stage_coordinator_dropin, inspect_coordinator_dropin
)
from muse_presets.coordinator_sourcekit import (
    export_coordinator_sourcekit,
)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to",type=Path,required=True,
                        help="new absolute .zip path (must not already exist)")
    args=parser.parse_args(argv)
    try:
        if not args.to.is_absolute():
            raise ValueError("COORDINATOR_SOURCEKIT_ABSOLUTE_DESTINATION_REQUIRED")
        with tempfile.TemporaryDirectory(prefix="r58-offline-coordinator-source-") as temp:
            source=Path(temp)/"coordinator"
            staged=stage_coordinator_dropin(source)
            if (staged["status"]!="SOURCE_ONLY_COORDINATOR_STAGED"
                or inspect_coordinator_dropin(source)["status"]!="LOCAL_COORDINATOR_MATCH"):
                raise ValueError("COORDINATOR_SOURCEKIT_PRISTINE_PREFLIGHT_FAILED")
            receipt=export_coordinator_sourcekit(source,args.to)
        print(json.dumps(receipt,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as exc:
        print(json.dumps({
            "status":"REFUSED",
            "reason":str(exc),
            "native_installed":False,
            "external_effect_authorized":False,
            "omnium_mission_compiled":False,
        },sort_keys=True))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
