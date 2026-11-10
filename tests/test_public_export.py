"""T31 public snapshot export: prove clean, portable, reproducible GitHub source."""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import zipfile

from muse_presets.public_export import (PublicExportError, select_public_files,
                                        export_public_snapshot, _validate_file)

ROOT=Path(__file__).resolve().parents[1]


class CleanPublicExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)

    def test_public_tree_excludes_internal_controller_and_private_tests(self):
        found=select_public_files(ROOT)
        self.assertIn("README.md",found)
        self.assertIn("LICENSE",found)
        self.assertIn("src/muse_presets/standalone_pack.py",found)
        self.assertIn("tests/test_standalone_pack.py",found)
        self.assertTrue(all(not p.startswith("control/") for p in found))
        self.assertTrue(all(not p.startswith("tests/test_r35") for p in found))
        for bad in ("tests/test_review_batch.py","tests/test_source_review_gate.py",
                    "tests/test_t03_receipt_consistency.py"):
            self.assertNotIn(bad,found)
        self.assertGreater(len(found),150)

    def test_reproducible_two_independent_exports(self):
        left=self.base/"a.zip"
        right=self.base/"b.zip"
        a=export_public_snapshot(ROOT,left)
        b=export_public_snapshot(ROOT,right)
        self.assertEqual(a["status"],"CLEAN_GITHUB_SOURCE_EXPORTED")
        self.assertEqual(a["sha256"],b["sha256"])
        self.assertEqual(left.read_bytes(),right.read_bytes())
        self.assertFalse(a["native_host_verified"])
        self.assertFalse(a["public_git_pushed"])
        self.assertTrue(a["history_omitted"])
        self.assertGreater(a["file_count"],150)

    def test_archive_is_hash_manifest_complete_no_git(self):
        out=self.base/"candidate.zip"
        result=export_public_snapshot(ROOT,out)
        with zipfile.ZipFile(out) as zipf:
            names=zipf.namelist()
            self.assertIsNone(zipf.testzip())
            self.assertEqual(len(names),len(set(names)))
            self.assertIn("PUBLIC_SOURCE_MANIFEST.json",names)
            self.assertNotIn("control/r35/WORKGRAPH.json",names)
            self.assertNotIn(".git/config",names)
            self.assertNotIn("tests/test_source_review_gate.py",names)
            manifest=json.loads(zipf.read("PUBLIC_SOURCE_MANIFEST.json"))
            self.assertEqual(manifest["schema"],"r46/public-source-snapshot-v1")
            self.assertEqual(manifest["files"],{n:hashlib.sha256(zipf.read(n)).hexdigest()
                                                for n in names if n!="PUBLIC_SOURCE_MANIFEST.json"})
            self.assertEqual(manifest["source_file_count"],len(names)-1)
            self.assertEqual(manifest["release_kind"],"GITHUB_SOURCE_ONLY")
            self.assertFalse(manifest["native_host_verified"])
            self.assertFalse(manifest["public_git_pushed"])
            self.assertTrue(manifest["private_git_history_excluded"])
            self.assertEqual(result["file_count"],len(names)-1)

    def test_existing_destination_refused_with_no_overwrite(self):
        dest=self.base/"occupied.zip"
        dest.write_bytes(b"original")
        with self.assertRaisesRegex(FileExistsError,"PUBLIC_EXPORT_DESTINATION_EXISTS"):
            export_public_snapshot(ROOT,dest)
        self.assertEqual(dest.read_bytes(),b"original")

    def test_missing_parent_refused(self):
        dest=self.base/"missing"/"x.zip"
        with self.assertRaisesRegex(FileNotFoundError,"PUBLIC_EXPORT_PARENT_MISSING"):
            export_public_snapshot(ROOT,dest)
        self.assertFalse(dest.parent.exists())

    def test_private_host_path_detected_in_staged_eligible_content(self):
        tree=self.base/"source"
        tree.mkdir()
        (tree/"README.md").write_text("private login at C:"+chr(92)+"Users"+chr(92)+"example-user"+chr(92)+"secret.txt")
        with self.assertRaises(PublicExportError):
            export_public_snapshot(tree,self.base/"out.zip")

    def test_unknown_root_item_is_refused(self):
        tree=self.base/"source"
        tree.mkdir()
        (tree/"README.md").write_text("# demo")
        (tree/"unexpected-personal-data.txt").write_text("owner notes")
        with self.assertRaisesRegex(PublicExportError,"UNKNOWN_TOPLEVEL_ENTRY"):
            select_public_files(tree)

    def test_symlink_file_rejected_before_reading_external(self):
        source=self.base/"safe"
        source.mkdir()
        secret=self.base/"outside-data"
        secret.write_text("protected",encoding="utf-8")
        link=source/"README.md"
        try:link.symlink_to(secret)
        except (OSError,NotImplementedError):self.skipTest("symlink creation denied")
        with self.assertRaisesRegex(PublicExportError,"SYMLINK"):
            select_public_files(source)
        self.assertEqual(secret.read_text(),"protected")

    def test_sensitive_names_and_unapproved_binaries_rejected(self):
        for name in ("credentials.json","private.sqlite","model.bin","image.png"):
            with self.subTest(name=name):
                tree=self.base/"clean"
                tree.mkdir(exist_ok=True)
                directory=tree/"docs"
                directory.mkdir(exist_ok=True)
                file=directory/name
                file.write_bytes(b"not distributable")
                with self.assertRaises(PublicExportError):
                    select_public_files(tree)
                file.unlink()

    def test_size_bound_prevents_dangerous_archive(self):
        f=self.base/"too_big.md"
        f.write_bytes(b"x"*(2_000_001))
        with self.assertRaises(PublicExportError):
            _validate_file(f,Path("README.md"))

    def test_export_never_scans_git_history(self):
        root=self.base/"source"
        root.mkdir()
        (root/"README.md").write_text("# clean")
        (root/".git").mkdir()
        (root/".git"/"config").write_text("private history")
        found=select_public_files(root)
        self.assertEqual(set(found),{"README.md"})
        dest=self.base/"source.zip"
        export_public_snapshot(root,dest)
        with zipfile.ZipFile(dest) as z:
            self.assertEqual(z.namelist(),["README.md","PUBLIC_SOURCE_MANIFEST.json"])

    def test_control_donor_matrix_test_not_in_public_snapshot(self):
        paths=select_public_files(ROOT)
        self.assertNotIn("tests/test_r39_donor_matrix.py",paths)

    def test_clean_export_can_be_reexported_from_extracted_source(self):
        a=self.base/"original.zip"
        b=self.base/"reexport.zip"
        first=export_public_snapshot(ROOT,a)
        root=self.base/"fresh-source"
        with zipfile.ZipFile(a) as z:
            z.extractall(root)
        self.assertIn("PUBLIC_SOURCE_MANIFEST.json",[p.name for p in root.iterdir()])
        second=export_public_snapshot(root,b)
        self.assertEqual(first["sha256"],second["sha256"])
        self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_tampered_existing_source_manifest_is_rejected(self):
        output=self.base/"source.zip"
        export_public_snapshot(ROOT,output)
        root=self.base/"fresh-source"
        with zipfile.ZipFile(output) as z:
            z.extractall(root)
        path=root/"PUBLIC_SOURCE_MANIFEST.json"
        manifest=json.loads(path.read_text(encoding="utf-8"))
        manifest["files"]["README.md"]="0"*64
        path.write_text(json.dumps(manifest),encoding="utf-8")
        with self.assertRaisesRegex(PublicExportError,"STALE_OR_FORGED_PUBLIC_MANIFEST"):
            select_public_files(root)

    def test_private_operator_terms_fail_public_export(self):
        tree=self.base/"source"
        tree.mkdir()
        (tree/"README.md").write_text("Contains SyntheticPrivateRecipient")
        with self.assertRaisesRegex(PublicExportError,"PUBLIC_NEUTRALITY_FAILED"):
            export_public_snapshot(tree,self.base/"output.zip",
                                   forbidden_terms=("SyntheticPrivateRecipient",))
        self.assertFalse((self.base/"output.zip").exists())

    def test_forbidden_terms_never_added_to_archive(self):
        root=self.base/"source"
        root.mkdir()
        (root/"README.md").write_text("# Generic sample")
        exported=self.base/"sample.zip"
        export_public_snapshot(root,exported,forbidden_terms=("DummySecretName",))
        with zipfile.ZipFile(exported) as z:
            self.assertNotIn("DummySecretName",z.read("PUBLIC_SOURCE_MANIFEST.json").decode())

    def test_public_docs_are_product_facing_and_source_safe(self):
        docs=ROOT/"docs"
        security=(docs/"SECURITY.md").read_text(encoding="utf-8")
        release=(docs/"RELEASES.md").read_text(encoding="utf-8")
        entry=(ROOT/"README.md").read_text(encoding="utf-8")
        self.assertIn("MIT",security)
        self.assertIn("private development repositories",security.lower())
        self.assertIn("source",release.lower())
        self.assertIn("native installation is optional",release.lower())
        self.assertIn("v0.2.0-alpha",entry)
        self.assertNotIn("Verify source ownership and licensing rights before copying",security)
        self.assertNotIn("Host doctor: determine supported personal Muse",release)

    def test_no_native_or_public_push_claim_in_export(self):
        p=self.base/"candidate.zip"
        report=export_public_snapshot(ROOT,p)
        self.assertEqual(report["approval"],"SOURCE_INTEGRITY_ONLY_NOT_PUBLICATION_AUTHORITY")
        self.assertFalse(report["public_git_pushed"])
        self.assertFalse(report["native_host_verified"])
        self.assertTrue(report["history_omitted"])


if __name__=="__main__":
    unittest.main()
