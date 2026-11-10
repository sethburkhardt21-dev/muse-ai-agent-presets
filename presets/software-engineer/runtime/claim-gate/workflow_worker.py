"""Trusted unittest result recorder for explicitly reviewed disposable Python code.

This process is not a security sandbox. Its controller pins the inputs, bounds
runtime/output and checks its actual exit. Never execute hostile code here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import unittest


class ObservedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observed_ids = []
        self.passed_ids = []

    def startTest(self, test):
        self.observed_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    ids = json.loads(args.contract.read_text(encoding="utf-8"))
    if type(ids) is not list or not ids or len(ids) > 64:
        raise ValueError("INVALID_TRUSTED_TEST_CONTRACT")
    if args.result.exists() or args.result.is_symlink():
        raise ValueError("RESULT_DESTINATION_OCCUPIED")
    # Load stdlib/harness first under -I, then only the admitted local sources.
    sys.path.insert(0, str(args.repo.resolve()))
    sys.path.insert(0, str((args.repo / "tests").resolve()))
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for identity in ids:
        suite.addTests(loader.loadTestsFromName(identity))
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2,
                                     resultclass=ObservedResult)
    result = runner.run(suite)
    record = {
        "schema": "r55/unittest-observation-v1",
        "python": sys.version.split()[0],
        "tests_run": result.testsRun,
        "observed_ids": result.observed_ids,
        "passed": result.passed_ids,
        "failures": [test.id() for test, _ in result.failures],
        "errors": [test.id() for test, _ in result.errors],
        "skipped": [test.id() for test, _ in result.skipped],
        "expected_failures": [test.id() for test, _ in result.expectedFailures],
        "unexpected_successes": [test.id() for test in result.unexpectedSuccesses],
    }
    with args.result.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(record, output, sort_keys=True, separators=(",", ":"))
        output.write("\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
