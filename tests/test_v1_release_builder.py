"""Deterministic, create-only V1 artifact composition and distribution acceptance."""
import hashlib,importlib.util,json,os,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load():
 spec=importlib.util.spec_from_file_location("v1builder",ROOT/"scripts/build_v1_release.py")
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class PackagingTests(unittest.TestCase):
 def test_deterministic_zip_contains_checked_members(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a.zip";b=Path(d)/"b.zip"
   files={"README.txt":b"hello\n","docs/nested.txt":b"data\n"}
   m.write_checked_zip(files,a);m.write_checked_zip(files,b)
   self.assertEqual(a.read_bytes(),b.read_bytes())
   with zipfile.ZipFile(a) as z:
    self.assertEqual(z.testzip(),None)
    self.assertEqual(set(z.namelist()),set(files))
    self.assertEqual(z.read("README.txt"),files["README.txt"])
 def test_create_only_refuses_preexisting_file(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"existing.zip";p.write_bytes(b"DO-NOT-CHANGE")
   with self.assertRaises(FileExistsError):m.write_checked_zip({"a.txt":b"A"},p)
   self.assertEqual(p.read_bytes(),b"DO-NOT-CHANGE")
 def test_unsafe_package_member_is_refused(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   for files in [{"../owner.txt":b"x"},{"/root.txt":b"x"},{"a\\b":b"x"},{"a.txt":b"\0"}]:
    with self.subTest(files=list(files)),self.assertRaises(ValueError):
     m.write_checked_zip(files,Path(d)/"fresh.zip")
    self.assertFalse((Path(d)/"fresh.zip").exists())
 def test_release_manifest_binds_real_distinct_assets(self):
  m=load()
  with tempfile.TemporaryDirectory() as d:
   files={"muse-specialist-toolkit-v1.0.0.zip":b"ZIP1",
          "muse-custom-connectors-v1.0.0.zip":b"ZIP2"}
   r=m.make_checksums(files)
   self.assertEqual(set(r),set(files))
   self.assertEqual(r["muse-custom-connectors-v1.0.0.zip"],hashlib.sha256(b"ZIP2").hexdigest())
 def test_builder_requires_source_head_and_clean_checkout(self):
  m=load()
  self.assertTrue(callable(m.verify_checkout))
  with self.assertRaisesRegex(ValueError,"SOURCE_HEAD"):
   m.verify_checkout(ROOT,"0"*40)
if __name__=="__main__":unittest.main()
