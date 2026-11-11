"""Run the real offline Creative Studio planner from this repository."""
from pathlib import Path
from muse_presets.creative_cli import main
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    raise SystemExit(main(sample_path=ROOT/'examples/creative_brief.json',kit_root=ROOT))
