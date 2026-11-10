"""One reviewed synthetic repair case shared by the R55 demo and source-kit export.

The example is deterministic, offline, nonclinical, source-only, and requires no
model, live repository, provider identity, or external effects.
"""
from __future__ import annotations

import hashlib


def fixture_case() -> dict:
    broken = ('def clamp(value, low, high):\n'
              '    if low > high:\n'
              '        raise ValueError("invalid bounds")\n'
              '    return min(max(value, low), high - 1)\n')
    tests = '''import unittest
from bounds import clamp

class BoundaryTests(unittest.TestCase):
    def test_upper_inclusive(self):
        self.assertEqual(clamp(10, 0, 10), 10)
    def test_interior(self):
        self.assertEqual(clamp(5, 0, 10), 5)
    def test_lower(self):
        self.assertEqual(clamp(-2, 0, 10), 0)
    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            clamp(1, 3, 2)
'''
    ids = ['test_bounds.BoundaryTests.' + name for name in
           ('test_upper_inclusive', 'test_interior', 'test_lower', 'test_invalid_bounds')]
    return {'schema': 'r55/engineering-case-v1', 'case_id': 'inclusive-boundary',
            'author_id': 'source-author', 'files': {'bounds.py': broken, 'tests/test_bounds.py': tests},
            'editable': ['bounds.py'], 'test_ids': ids, 'expected_failures': [ids[0]],
            'patch': [{'path': 'bounds.py', 'before_sha256': hashlib.sha256(broken.encode()).hexdigest(),
                       'after_utf8': broken.replace('high - 1)', 'high)')}],
            'command_profile': 'python-unittest-v1', 'timeout_seconds': 8}
