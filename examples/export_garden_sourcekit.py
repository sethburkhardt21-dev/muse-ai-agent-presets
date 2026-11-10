"""Create or verify a standalone Garden Companion source kit."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from muse_presets.garden_sourcekit import export_garden_sourcekit, verify_garden_sourcekit

ROOT = Path(__file__).resolve().parents[1]

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--to", type=Path, help="New ZIP; never overwrites")
    command.add_argument("--verify", type=Path, help="Canonical ZIP to verify without parsing")
    parser.add_argument("--sha256", help="External digest required when verifying")
    args = parser.parse_args(argv)
    try:
        if args.to:
            if args.sha256 is not None:
                raise ValueError("EXPORT_CANNOT_ACCEPT_EXTERNAL_PIN")
            result = export_garden_sourcekit(ROOT, args.to)
        else:
            result = verify_garden_sourcekit(ROOT, args.verify, args.sha256)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": type(exc).__name__ + ":" + str(exc)[:180],
                          "native_installed": False, "external_calendar_writes": False}, sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
