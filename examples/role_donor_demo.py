"""Run the existing optional first-party source adapters on synthetic local data.

Default is read-only catalog. --run-fixtures explicitly exercises reviewed
local examples under the invoking OS account. Does NOT create a native agent,
connect a provider or supply a sandbox.
"""
from __future__ import annotations
import argparse,json
from muse_presets.catalog import ROOT
from muse_presets.donor_source import donor_catalog,run_donor_fixture

RUNNABLE=("claims","evaluation","garden","security","study")

def demonstrate(*,run_fixtures:bool=False)->dict:
    report=donor_catalog(ROOT)
    if not run_fixtures:
        return {"schema":"muse-presets/role-donor-demo-v1",
                "status":"SOURCE_CATALOG_ONLY",
                "capabilities":report["capabilities"],
                "fixture_executed":False,
                "animation_engine_bundled":False,
                "native_agent_installed":False,
                "external_effect_authorized":False}
    outputs={name:run_donor_fixture(ROOT,name,allow_reviewed_fixture=True)
             for name in RUNNABLE}
    if any(item["status"]!="LOCAL_SOURCE_FIXTURE_PASS" for item in outputs.values()):
        raise ValueError("DONOR_FIXTURE_NOT_COMPLETE")
    return {"schema":"muse-presets/role-donor-demo-v1",
            "status":"FIVE_EXISTING_LOCAL_FIXTURES_PASS",
            "capabilities":report["capabilities"],
            "fixtures":outputs,
            "fixture_executed":True,
            "animation_engine_bundled":False,
            "native_agent_installed":False,
            "external_effect_authorized":False}

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description="Source-only optional role-donor demo; no host connections")
    parser.add_argument("--run-fixtures",action="store_true",
                        help="Opt into local, reviewed first-party Python fixtures")
    args=parser.parse_args(argv)
    print(json.dumps(demonstrate(run_fixtures=args.run_fixtures),
                     sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
