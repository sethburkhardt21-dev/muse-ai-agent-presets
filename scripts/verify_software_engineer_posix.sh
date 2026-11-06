#!/usr/bin/env bash
# R31 public Software Engineer POSIX acceptance.
# Uses only a disposable scratch copy; never activates a Muse host or writes
# into the caller's original worktree, profiles or external services.
set -euo pipefail
source_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d -t muse-software-engineer-XXXXXXXX)"
trap 'rm -rf -- "$scratch"' EXIT
tar -C "$source_root" --exclude=.git --exclude=__pycache__ -cf - . |
  tar -C "$scratch" -xf -
cd "$scratch"
export PYTHONPATH="$scratch/src"
export PYTHONDONTWRITEBYTECODE=1
printf '%s\n' '=== Platform ==='
uname -s
python3 --version
printf '%s\n' '=== Original-derived engineering tests ==='
python3 -B -m unittest discover -s tests -p 'test_software_engineer*.py' -q
printf '%s\n' '=== Create-only pack and source-pin tests ==='
python3 -B -m unittest discover -s tests -p test_engineering_pack.py -q
printf '%s\n' '=== Executable Claim Gate demo ==='
python3 -B examples/software_engineer_claim_gate_demo.py
printf '%s\n' '=== Full public regression ==='
python3 -B -m unittest discover -s tests -q
printf '%s\n' '=== Public neutrality and doctor ==='
python3 -B -m muse_presets.cli audit-neutrality
python3 -B -m muse_presets.cli doctor
printf '%s\n' 'R31_POSIX_ACCEPTANCE_PASS'
