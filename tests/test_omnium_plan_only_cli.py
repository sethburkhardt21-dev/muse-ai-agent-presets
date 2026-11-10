"""CLI acceptance for read-only Omnium source plan consumer (no host/worker)."""
from __future__ import annotations
import io,json,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path

from examples.omnium_plan_only_demo import synthetic_plan
from muse_presets.cli import main


class PlanPreviewCliTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="omnium-preview-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.case=self.root/"plan.json"
        self.plan=synthetic_plan()
        self.case.write_text(json.dumps(self.plan),encoding="utf-8")

    def invoke(self,argv):
        out=io.StringIO()
        with redirect_stdout(out):
            rc=main(argv)
        return rc,json.loads(out.getvalue())

    def test_explicit_external_sha_and_plan_only_status(self):
        before=self.case.read_bytes()
        rc,result=self.invoke(["omnium-plan-preview","--file",str(self.case),
                               "--sha256",self.plan["plan_sha256"]])
        self.assertEqual(rc,0)
        self.assertEqual(result["status"],"PLAN_ONLY_MISSING_WORKER_ADAPTER_HELD")
        self.assertEqual(result["worker_dispatch_status"],"NOT_INVOKED")
        self.assertFalse(result["native_worker_invoked"])
        self.assertEqual(self.case.read_bytes(),before)
        self.assertEqual(list(self.root.iterdir()),[self.case])

    def test_wrong_external_pin_refused_without_source_or_output_write(self):
        before=self.case.read_bytes()
        rc,result=self.invoke(["omnium-plan-preview","--file",str(self.case),
                               "--sha256","0"*64])
        self.assertEqual(rc,2)
        self.assertEqual(result["status"],"REFUSED")
        self.assertEqual(self.case.read_bytes(),before)

    def test_unsafe_duplicate_key_input_refused(self):
        self.case.write_text('{"plan":1,"plan":2}',encoding="utf-8")
        rc,result=self.invoke(["omnium-plan-preview","--file",str(self.case),
                               "--sha256","a"*64])
        self.assertEqual(rc,2)
        self.assertEqual(result["status"],"REFUSED")
        self.assertFalse(result.get("external_effect_authorized",False))


if __name__=="__main__":
    unittest.main()
