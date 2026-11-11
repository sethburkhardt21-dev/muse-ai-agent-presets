"""T28 regression: malformed archive with correct hash must fail closed."""
from __future__ import annotations
import hashlib,io,json,os,stat,struct,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from muse_presets import claims_sourcekit as sourcekit
from muse_presets.claims_sourcekit import verify_claims_sourcekit

SOURCE=Path(__file__).resolve().parents[1]
CASES=(("not-a-zip",b"this is a synthetic corrupt archive\n"),
       ("truncated-zip",b"PK\x03\x04"+b"\x00"*12))

class ClaimsMalformedArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="claims-corrupt-")
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def check_direct(self,name,raw):
        p=self.folder/(name+".zip")
        p.write_bytes(raw)
        digest=hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError,"CLAIMS_SOURCEKIT_CORRUPT_ARCHIVE"):
            verify_claims_sourcekit(SOURCE,p,digest)

    def test_invalid_archive_is_valueerror_not_badzipfile(self):
        self.check_direct(*CASES[0])

    def test_truncated_archive_is_valueerror_not_badzipfile(self):
        self.check_direct(*CASES[1])

    def test_command_returns_structured_refusal_for_both(self):
        env=dict(os.environ,PYTHONPATH=str(SOURCE/"src"),
                 PYTHONDONTWRITEBYTECODE="1",GIT_TERMINAL_PROMPT="0")
        for name,raw in CASES:
            with self.subTest(name=name):
                path=self.folder/(name+".zip")
                path.write_bytes(raw)
                digest=hashlib.sha256(raw).hexdigest()
                result=subprocess.run([
                    sys.executable,"-B",
                    str(SOURCE/"examples/export_claims_sourcekit.py"),
                    "--verify",str(path),"--sha256",digest
                ],cwd=SOURCE,env=env,capture_output=True,timeout=25)
                self.assertEqual(result.returncode,2,result.stderr.decode(errors="replace"))
                self.assertNotIn(b"Traceback",result.stderr)
                output=json.loads(result.stdout)
                self.assertEqual(output["status"],"REFUSED")
                self.assertIs(output["external_effect_authorized"],False)

    def make_archive(self, mutation=None):
        """Eight tiny canonical members; no large allocation or external input."""
        payloads=sourcekit._distribution(SOURCE)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as archive:
            for index,(name,payload) in enumerate(sorted(payloads.items())):
                info=zipfile.ZipInfo(name)
                info.external_attr=(stat.S_IFREG|0o644)<<16
                info.compress_type=zipfile.ZIP_DEFLATED
                if mutation=="wrong-length" and index==0:
                    payload+=b"x"
                archive.writestr(info,payload)
        raw=bytearray(stream.getvalue())
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            first=archive.infolist()[0]
            local=first.header_offset
            central=archive.start_dir
            name_size,extra_size=struct.unpack_from("<HH",raw,local+26)
            data=local+30+name_size+extra_size
        if mutation=="bad-deflate":
            raw[data]=6  # Reserved DEFLATE block type, bounded tiny payload.
        elif mutation=="unsupported-method":
            struct.pack_into("<H",raw,local+8,99)
            struct.pack_into("<H",raw,central+10,99)
        elif mutation in ("encrypted","patched-data"):
            flags=1 if mutation=="encrypted" else 0x20
            struct.pack_into("<H",raw,local+6,flags)
            struct.pack_into("<H",raw,central+8,flags)
        path=self.folder/((mutation or "valid-deflated")+".zip")
        path.write_bytes(raw)
        return path,hashlib.sha256(raw).hexdigest()

    def check_before_member_open(self, mutation, reason):
        path,digest=self.make_archive(mutation)
        with patch.object(zipfile.ZipFile,"open",side_effect=AssertionError("BODY_OPENED_BEFORE_ADMISSION")):
            with self.assertRaisesRegex(ValueError,reason):
                verify_claims_sourcekit(SOURCE,path,digest)

    def test_valid_deflated_archive_still_verifies(self):
        path,digest=self.make_archive()
        result=verify_claims_sourcekit(SOURCE,path,digest)
        self.assertEqual(result["status"],"LOCAL_CLAIMS_SOURCEKIT_VERIFIED")

    def test_invalid_deflate_returns_controlled_valueerror(self):
        path,digest=self.make_archive("bad-deflate")
        with self.assertRaisesRegex(ValueError,"CLAIMS_SOURCEKIT_CORRUPT_ARCHIVE"):
            verify_claims_sourcekit(SOURCE,path,digest)

    def test_invalid_deflate_cli_refuses_without_traceback(self):
        path,digest=self.make_archive("bad-deflate")
        env=dict(os.environ,PYTHONPATH=str(SOURCE/"src"),PYTHONDONTWRITEBYTECODE="1")
        result=subprocess.run([sys.executable,"-B",str(SOURCE/"examples/export_claims_sourcekit.py"),
            "--verify",str(path),"--sha256",digest],cwd=SOURCE,env=env,
            capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertNotIn("Traceback",result.stderr)
        response=json.loads(result.stdout)
        self.assertEqual(response["status"],"REFUSED")
        self.assertIs(response["external_effect_authorized"],False)

    def test_unpack_budget_checked_before_any_member_open(self):
        path,digest=self.make_archive()
        with patch.object(sourcekit,"MAX_UNPACKED",1),patch.object(zipfile.ZipFile,"open",
                side_effect=AssertionError("BODY_OPENED_BEFORE_BUDGET")):
            with self.assertRaisesRegex(ValueError,"CLAIMS_SOURCEKIT_UNPACK_BUDGET"):
                verify_claims_sourcekit(SOURCE,path,digest)

    def test_wrong_member_length_refused_before_body(self):
        self.check_before_member_open("wrong-length","CLAIMS_SOURCEKIT_MEMBER_SIZE_INVALID")

    def test_unsupported_method_refused_before_body(self):
        self.check_before_member_open("unsupported-method","CLAIMS_SOURCEKIT_COMPRESSION_UNSUPPORTED")

    def test_encrypted_member_refused_before_body(self):
        self.check_before_member_open("encrypted","CLAIMS_SOURCEKIT_FLAGS_UNSUPPORTED")

    def test_patched_data_flag_refused_before_body(self):
        self.check_before_member_open("patched-data","CLAIMS_SOURCEKIT_FLAGS_UNSUPPORTED")

if __name__=="__main__":
    unittest.main()
