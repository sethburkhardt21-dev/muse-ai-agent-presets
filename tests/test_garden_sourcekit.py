"""Standalone T26 packaging; exercises real SQLite source outside the repo."""
from __future__ import annotations
import hashlib, io, json, os, shutil, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from muse_presets import garden_sourcekit as kit
from muse_presets.public_export import select_public_files

ROOT = Path(__file__).resolve().parents[1]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

class GardenSourcekitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="garden-kit-test-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def export(self, name="garden.zip"):
        target = self.folder / name
        result = kit.export_garden_sourcekit(ROOT, target)
        return target, result

    def extracted(self):
        target, result = self.export()
        out = self.folder / "extracted"
        with zipfile.ZipFile(target) as archive:
            archive.extractall(out)  # Only the just-built, canonically verified fixture.
        return out, result

    def run_kit(self, folder, operation="demo"):
        env = dict(os.environ, PYTHONPATH="not-a-repository", PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, "-I", "-B", str(folder / "run.py"),
                               "--operation", operation], cwd=self.folder,
                              env=env, capture_output=True, text=True, timeout=60)

    def test_repeatable_export_and_exact_verification(self):
        first, one = self.export()
        second, two = self.export("second.zip")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(one["archive_sha256"], two["archive_sha256"])
        self.assertFalse(one["native_installed"])
        self.assertEqual(kit.verify_garden_sourcekit(ROOT, first, one["archive_sha256"])["status"],
                         "LOCAL_GARDEN_SOURCEKIT_VERIFIED")

    def test_original_engine_demo_tests_and_role_bytes_are_preserved(self):
        target, _ = self.export()
        with zipfile.ZipFile(target) as z:
            for source, destination in kit.SOURCE_MAP.items():
                self.assertEqual(z.read(destination), (ROOT / source).read_bytes())
            manifest = json.loads(z.read("SOURCEKIT_MANIFEST.json"))
            self.assertEqual(set(z.namelist()), set(manifest["files_sha256"]) | {"SOURCEKIT_MANIFEST.json"})
            for name, digest in manifest["files_sha256"].items():
                self.assertEqual(sha(z.read(name)), digest)
            self.assertFalse(manifest["provider_authenticated"])
            self.assertFalse(manifest["external_calendar_writes"])

    def test_existing_destination_is_not_overwritten(self):
        target, _ = self.export()
        before = target.read_bytes()
        with self.assertRaises(ValueError):
            kit.export_garden_sourcekit(ROOT, target)
        self.assertEqual(target.read_bytes(), before)

    def test_external_digest_required_and_must_match(self):
        target, _ = self.export()
        for digest in (None, "", "x" * 64, "0" * 64):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                kit.verify_garden_sourcekit(ROOT, target, digest)

    def test_rehashed_changed_archive_is_not_trusted(self):
        target, _ = self.export()
        target.write_bytes(target.read_bytes() + b"unreviewed-trailer")
        with self.assertRaisesRegex(ValueError, "CANONICAL_ARCHIVE_CHANGED"):
            kit.verify_garden_sourcekit(ROOT, target, sha(target.read_bytes()))

    def test_untrusted_archive_is_never_parsed_or_decompressed(self):
        target = self.folder / "bad.zip"
        target.write_bytes(b"not a zip")
        original = zipfile.ZipFile
        def guarded(*args, **kwargs):
            mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")
            self.assertEqual(mode, "w", "Untrusted ZIP parser opened")
            return original(*args, **kwargs)
        with patch.object(zipfile, "ZipFile", side_effect=guarded):
            with self.assertRaisesRegex(ValueError, "CANONICAL_ARCHIVE_CHANGED"):
                kit.verify_garden_sourcekit(ROOT, target, sha(target.read_bytes()))

    def test_hostile_member_and_rehashed_manifest_cannot_be_admitted(self):
        target = self.folder / "hostile.zip"
        with zipfile.ZipFile(target, "w") as z:
            z.writestr("../escape.py", b"untrusted")
            z.writestr("SOURCEKIT_MANIFEST.json", b"{}")
        with self.assertRaisesRegex(ValueError, "CANONICAL_ARCHIVE_CHANGED"):
            kit.verify_garden_sourcekit(ROOT, target, sha(target.read_bytes()))
        self.assertFalse((self.folder.parent / "escape.py").exists())

    def test_changed_original_source_is_refused(self):
        copy = self.folder / "source"
        for name in kit.SOURCE_SHA:
            out = copy / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, out)
        engine = copy / "src/muse_presets/garden_calendar.py"
        engine.write_bytes(engine.read_bytes() + b"\n# drift\n")
        with self.assertRaisesRegex(ValueError, "SOURCE_PIN_MISMATCH"):
            kit.export_garden_sourcekit(copy, self.folder / "drift.zip")
        self.assertFalse((self.folder / "drift.zip").exists())

    def test_oversized_archive_is_refused_before_read(self):
        target, result = self.export()
        with patch.object(kit, "MAX_ARCHIVE", 1):
            with self.assertRaisesRegex(ValueError, "ARCHIVE_UNSAFE"):
                kit.verify_garden_sourcekit(ROOT, target, result["archive_sha256"])

    def test_standalone_demo_uses_real_sqlite_without_repository(self):
        folder, _ = self.extracted()
        run = self.run_kit(folder)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        result = json.loads(run.stdout)
        self.assertEqual(result["status"], "LOCAL_SQLITE_DEMO_PASSED")
        self.assertTrue(result["lost_ack_recovered"])
        self.assertFalse(result["host_authenticated"])
        self.assertFalse(result["external_calendar_writes"])
        self.assertFalse(list(folder.rglob("*.sqlite3")))

    def test_standalone_original_tests_run_in_isolated_python(self):
        folder, _ = self.extracted()
        run = self.run_kit(folder, "self-test")
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        result = json.loads(run.stdout)
        self.assertEqual(result["status"], "LOCAL_GARDEN_SELF_TEST_PASSED")
        self.assertGreater(result["tests_run"], 10)
        self.assertEqual(result["failures"], 0)
        self.assertEqual(result["errors"], 0)

    def test_runner_refuses_changed_engine_even_with_rehashed_manifest(self):
        folder, _ = self.extracted()
        engine = folder / "muse_presets/garden_calendar.py"
        engine.write_bytes(engine.read_bytes() + b"\n# changed\n")
        manifest = folder / "SOURCEKIT_MANIFEST.json"
        doc = json.loads(manifest.read_bytes())
        doc["files_sha256"]["muse_presets/garden_calendar.py"] = sha(engine.read_bytes())
        manifest.write_text(json.dumps(doc), encoding="utf-8")
        run = self.run_kit(folder)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "REFUSED")
        self.assertNotIn("Traceback", run.stderr)

    def test_runner_refuses_extra_import_shadow(self):
        folder, _ = self.extracted()
        (folder / "sqlite3.py").write_text("raise RuntimeError('unreviewed import')\n", encoding="utf-8")
        run = self.run_kit(folder)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)["status"], "REFUSED")
        self.assertNotIn("Traceback", run.stderr)

    def test_export_cli_and_verify_cli(self):
        target = self.folder / "cli.zip"
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        command = [sys.executable, "-B", str(ROOT / "examples/export_garden_sourcekit.py")]
        made = subprocess.run(command + ["--to", str(target)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(made.returncode, 0, made.stderr + made.stdout)
        digest = json.loads(made.stdout)["archive_sha256"]
        verified = subprocess.run(command + ["--verify", str(target), "--sha256", digest], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(verified.returncode, 0, verified.stderr + verified.stdout)

    def test_runner_refuses_deeply_nested_manifest_without_traceback(self):
        folder, _ = self.extracted()
        manifest = folder / "SOURCEKIT_MANIFEST.json"
        cases = {
            "array": b"[" * 10000 + b"0" + b"]" * 10000,
            "object": b'{"x":' * 5000 + b"0" + b"}" * 5000,
        }
        for shape, raw in cases.items():
            with self.subTest(shape=shape):
                self.assertLess(len(raw), 65536)
                manifest.write_bytes(raw)
                run = self.run_kit(folder)
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                response = json.loads(run.stdout)
                self.assertEqual(response["status"], "REFUSED")
                self.assertFalse(response["native_installed"])
                self.assertFalse(response["external_calendar_writes"])
                self.assertNotIn("Traceback", run.stderr)

    def test_public_snapshot_includes_complete_garden_implementation(self):
        selected = select_public_files(ROOT)
        for name in ("src/muse_presets/garden_sourcekit.py", "examples/export_garden_sourcekit.py",
                     "tests/test_garden_sourcekit.py", "docs/kits/GARDEN_SOURCEKIT.md"):
            self.assertIn(name, selected)
        self.assertFalse(any(n.startswith("control/") for n in selected))

    def check_linked_kit_refused(self, *, junction, package):
        folder, _ = self.extracted()
        target = folder
        linked = self.folder / "linked-kit"
        runner = linked
        if package:
            target = self.folder / "relocated-package"
            (folder / "muse_presets").rename(target)
            linked = folder / "muse_presets"
            runner = folder
        if junction:
            if os.name != "nt":
                self.skipTest("Native Windows directory-junction case")
            made = subprocess.run(["cmd", "/c", "mklink", "/J", str(linked), str(target)],
                                  capture_output=True, text=True, timeout=15)
            self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
            self.assertTrue(linked.is_junction())
        else:
            try:
                linked.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest("Host cannot create a directory symlink: " + str(exc))
        try:
            result = self.run_kit(runner)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response["status"], "REFUSED")
            self.assertIn("LINKED_KIT_REFUSED", response["reason"])
            self.assertNotIn("Traceback", result.stderr)
        finally:
            if junction:
                os.rmdir(linked)  # Only this fixture's junction, never its target.
            else:
                linked.unlink()

    def test_runner_refuses_junction_at_kit_root(self):
        self.check_linked_kit_refused(junction=True, package=False)

    def test_runner_refuses_junction_at_package_directory(self):
        self.check_linked_kit_refused(junction=True, package=True)

    def test_runner_refuses_symlink_at_kit_root(self):
        self.check_linked_kit_refused(junction=False, package=False)

    def test_runner_refuses_symlink_at_package_directory(self):
        self.check_linked_kit_refused(junction=False, package=True)

if __name__ == "__main__":
    unittest.main()
