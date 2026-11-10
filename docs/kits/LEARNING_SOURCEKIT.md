# Learning Coach executable source kit

This is a portable offline kit around the existing standard-library SQLite
LearningSession engine. It is a source product, not an installed native agent.
The engine, database path checker, original study demo and 25 engine tests are
copied byte-for-byte under explicit source pins; no study or account state is
included. The packaging and runner retain the accepted reviewed path, manifest and
canonical-archive boundaries.

## Build and inspect

From this repository:

    PYTHONPATH=src python3 -B examples/export_learning_sourcekit.py --to ../learning-coach.zip
    PYTHONPATH=src python3 -B examples/export_learning_sourcekit.py --verify ../learning-coach.zip --sha256 <external-sha256>

On Windows set $env:PYTHONPATH='src' and use python instead of python3.
Export is create-only and requires an existing safe parent directory.
Verification compares bounded exact canonical bytes without parsing or
extracting a supplied ZIP. Recompressed or changed packages are refused even
when their caller-supplied hash matches. A separately trusted digest is still
needed to establish the expected artifact; hashes are not publisher signatures.

After verifying the digest and extracting into a new directory:

    python -I -B run.py --operation demo
    python -I -B run.py --operation self-test

The runner checks file names, sizes, hashes, directories, manifest and linked
paths before importing the engine. Unknown files, import shadows, duplicate
or deeply nested manifest JSON and optimized-interpreter operation refuse.
It supports Windows, macOS and Linux Python 3.12+; platform-specific skips
remain explicit. The extracted source does not need the original repository.

## Useful behavior and boundaries

The demo admits explicitly supplied definitions with source hashes and line
locators, creates held drafts, approves one as a synthetic owner, gives the
learner a question without its answer, records a score, reopens SQLite,
recovers the same receipt and calculates next-day review eligibility.
The original 25-test engine suite exercises wrong-role and cross-session
refusal, source tampering, injected lessons, stale versions, duplicate scoring,
transaction rollback and concurrent connections.

The generator accepts only simple Term :: Definition. lines. Scoring is literal
case/whitespace normalization, not semantic assessment. Review due times use
HEURISTIC_V1_NOT_FSRS, not validated adaptive mastery. Material is caller-supplied
and is not independently verified educational or clinical content.

Read [the local study contract](../LEARNING_LOCAL_STUDY.md) before integration.
LearningScope is not a credential: use a protected host-side authority callback,
never model/browser identity fields. SQLite is unencrypted local storage and is
not appropriate for clinical data, examination secrets or regulated scoring.
No native Muse, scheduler, Space, model or external connector is activated.
Python -I is not an OS sandbox. Demo databases are disposable; user databases
belong outside the immutable kit. Upgrade by creating a newly verified kit;
there is no automatic migration or state-deleting uninstall.

## Repository regression commands

    PYTHONPATH=src python3 -B -m unittest discover -s tests -p test_learning_sourcekit.py -v
    PYTHONPATH=src python3 -B -m unittest discover -s tests -p test_learning_session.py -v
    PYTHONPATH=src python3 -B -m unittest discover -s tests -v

Native provider acceptance and public release are separate from these source tests.
