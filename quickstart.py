"""One-command source-only role starter. No installer or provider credential effects.

Run from a checked-out public source tree using Python 3.12+:
  python -B quickstart.py --all
  python -B quickstart.py --role garden-companion --to "$HOME/my-garden-kit"
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from examples.github_quickstart import main  # noqa: E402


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc),
                          "native_installed": False,
                          "external_effect_authorized": False}))
        raise SystemExit(2)
