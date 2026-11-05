"""Cross-platform local SQLite path validation with no symlink escape."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from muse_presets.database_paths import validated_database_path


class DatabasePathTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_normal_current_temporary_directory_is_accepted(self):
        db=self.root/'safe.sqlite3'
        self.assertEqual(validated_database_path(db,error='INVALID_DATABASE'),db)
        self.assertEqual(validated_database_path(db,error='UNSAFE_DATABASE_PATH',absolute=True),db)

    @unittest.skipUnless(sys.platform=='darwin', 'macOS system aliases only')
    def test_macos_root_owned_var_alias_is_not_a_user_traversal(self):
        self.assertTrue(Path('/var').is_symlink())
        self.assertEqual(Path('/var').resolve(),Path('/private/var'))
        self.assertEqual(validated_database_path(self.root/'sample.sqlite3',error='INVALID_DATABASE'),self.root/'sample.sqlite3')
        self.assertEqual(validated_database_path(self.root/'sample.sqlite3',error='UNSAFE_DATABASE_PATH',absolute=True),self.root/'sample.sqlite3')

    def test_broken_directory_and_file_rejected(self):
        with self.assertRaisesRegex(ValueError,'INVALID_DATABASE'):
            validated_database_path(self.root/'missing'/'data.db',error='INVALID_DATABASE')
        with self.assertRaisesRegex(ValueError,'UNSAFE_DATABASE_PATH'):
            validated_database_path('.',error='UNSAFE_DATABASE_PATH',absolute=True)
        with self.assertRaisesRegex(ValueError,'INVALID_DATABASE'):
            validated_database_path([],error='INVALID_DATABASE')

    def test_symlink_file_and_intermediate_user_directory_rejected(self):
        actual=self.root/'actual'
        actual.mkdir()
        nested=actual/'child'
        nested.mkdir()
        target=nested/'data.db'
        target.write_text('fixture')
        link=self.root/'redirect'
        link_file=self.root/'alias.db'
        try:
            link.symlink_to(actual,target_is_directory=True)
            link_file.symlink_to(target)
        except (OSError,NotImplementedError):
            self.skipTest('symlink privileges unavailable')
        for p in (link/'data.db',link/'child'/'data.db',link_file):
            with self.subTest(path=str(p)),self.assertRaisesRegex(ValueError,'INVALID_DATABASE'):
                validated_database_path(p,error='INVALID_DATABASE')
            with self.assertRaisesRegex(ValueError,'UNSAFE_DATABASE_PATH'):
                validated_database_path(p,error='UNSAFE_DATABASE_PATH',absolute=True)

    def test_symlink_named_var_inside_user_folder_is_not_trusted_system_alias(self):
        actual=self.root/'actual'
        actual.mkdir()
        alias=self.root/'var'
        try:alias.symlink_to(actual,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('symlink privileges unavailable')
        with self.assertRaisesRegex(ValueError,'UNSAFE_DATABASE_PATH'):
            validated_database_path(alias/'data.db',error='UNSAFE_DATABASE_PATH',absolute=True)


if __name__=='__main__':unittest.main()
