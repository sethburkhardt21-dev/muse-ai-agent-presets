"""Published text must have the LF bytes declared by the repository policy.

A manifest made from CRLF working-tree bytes can pass locally but fail after
Git's configured LF normalization. Keep this regression runnable without Git.
"""
from pathlib import Path
import unittest
from muse_presets.public_export import select_public_files
ROOT=Path(__file__).resolve().parents[1]

class CanonicalPublicBytes(unittest.TestCase):
    def test_manifest_sources_are_canonical_lf_not_checkout_dependent(self):
        source=select_public_files(ROOT,verify_manifest=False)
        noncanonical=[name for name,raw in source.items() if b'\r\n' in raw]
        self.assertEqual(noncanonical,[],
                         'Normalize reviewed text before binding manifest hashes; '
                         'never update a verifier to accept stale checkout hashes.')

if __name__=='__main__':unittest.main()
