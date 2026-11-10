"""R61 OS path contracts: narrowly admit standard root-owned Darwin aliases.

These are isolated predicate tests on Linux, not native macOS proof.
"""
from pathlib import Path
from types import SimpleNamespace
import unittest
import os
from unittest.mock import patch
from muse_presets import model_toy_bundle as b


@unittest.skipUnless(os.name == "posix", "Darwin alias predicates require POSIX path semantics")
class DarwinRootPathTests(unittest.TestCase):
    def configured(self, *, platform='darwin', link='/var', target='/private/var', uid=0,
                   is_directory=True, read_error=None):
        self.stack = []
        self.addCleanup(self.cleanup)
        values = [
            patch.object(b.sys, 'platform', platform),
            patch.object(Path, 'is_symlink', autospec=True,
                         side_effect=lambda p: str(p) == link),
            patch.object(Path, 'lstat', autospec=True,
                         side_effect=read_error if read_error else lambda p: SimpleNamespace(st_uid=uid)),
            patch.object(Path, 'resolve', autospec=True,
                         side_effect=lambda p, strict=False: Path(target)),
            patch.object(Path, 'is_dir', autospec=True, return_value=is_directory),
        ]
        for item in values:
            item.start(); self.stack.append(item)

    def cleanup(self):
        for item in reversed(self.stack):
            item.stop()
        self.stack.clear()

    def test_native_darwin_var_alias_accepts_real_temp_path_shape(self):
        self.configured()
        path=Path('/var/folders/fictional/cache/new-output')
        try:
            result=b._admitted_path(path)
        except b.Refused as exc:
            self.fail('Standard root-owned Darwin /var alias incorrectly refused: '+str(exc))
        self.assertEqual(result,path)

    def test_native_darwin_tmp_alias_accepts_sourcekit_path_shape(self):
        self.configured(link='/tmp',target='/private/tmp')
        path=Path('/tmp/fake-disposable/new-output')
        try:
            result=b._admitted_path(path)
        except b.Refused as exc:
            self.fail('Standard root-owned Darwin /tmp alias incorrectly refused: '+str(exc))
        self.assertEqual(result,path)

    def test_darwin_alias_wrong_destination_refused(self):
        self.configured(target='/private/owner-controlled')
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/var/folders/new'))

    def test_darwin_alias_nonroot_owner_refused(self):
        self.configured(uid=501)
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/var/folders/new'))

    def test_darwin_alias_unavailable_metadata_refused(self):
        self.configured(read_error=OSError('unavailable'))
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/var/folders/new'))

    def test_darwin_alias_non_directory_target_refused(self):
        self.configured(is_directory=False)
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/var/folders/new'))

    def test_linux_does_not_grant_darwin_alias_exception(self):
        self.configured(platform='linux')
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/var/folders/new'))

    def test_owner_directory_named_var_is_not_system_alias(self):
        self.configured(link='/owner/var',target='/private/var')
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/owner/var/new'))

    def test_descendant_symlink_is_not_system_alias(self):
        self.configured(link='/var/folders/owner-link',target='/private/var')
        with self.assertRaisesRegex(b.Refused,'LINKED_PATH'):
            b._admitted_path(Path('/var/folders/owner-link/new'))

    def test_standard_alias_exception_cannot_admit_dotdot(self):
        self.configured()
        with self.assertRaisesRegex(b.Refused,'CANONICAL_PATH'):
            b._admitted_path(Path('/var/folders/../new'))

if __name__=='__main__': unittest.main()
