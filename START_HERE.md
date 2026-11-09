# Software Engineer: independent offline source kit

Contains the actual source-pinned Python Claim Gate, R55 RED/PATCH/GREEN
workflow, source-only profile, disabled skills and a fictional test fixture.
No native Muse agent, account connector, paid API, or deployment is installed.

Requirements: Python 3.12+ and Git. No Python package installation required.

1. Extract into a new directory. Preserve any existing user/agent files.
2. Verify downloaded ZIP SHA-256 against trusted publisher metadata, not
   just the unsigned SOURCEKIT_MANIFEST.json inside this ZIP.
3. A reviewed offline fixture is included as EXAMPLE_REPAIR_CASE.json.
   Its expected digest is in SOURCEKIT_MANIFEST.json.
4. To execute the fixture, use absolute case/output paths and a NEW output
   directory that does not exist:

   python -I -B software-engineer/runtime/claim-gate/engineering_workflow.py execute --case ABSOLUTE_CASE_PATH --case-sha256 CASE_SHA --to ABSOLUTE_NEW_WORKSPACE --reviewed-code

5. Check the RED assertion, GREEN test receipt and preserved work evidence.
   A separate reviewer can run the review verb in a distinct workspace.

IMPORTANT: --reviewed-code is an operator assertion, NOT an OS sandbox.
Python tests execute with the operating account's permissions and can reach
its files/network. Never run untrusted source without separate OS isolation.
Local hashes are not signatures. No independent human or native Muse identity
is authenticated. Real external effects and schedulers are disabled.
Windows directory-entry power-loss durability is unproven; Windows destructive
retention pruning remains disabled. This is source only.
