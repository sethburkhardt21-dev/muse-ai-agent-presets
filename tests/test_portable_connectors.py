"""R44 GitHub-source connector contract: role-scoped, offline proof without fake CUA."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from muse_presets.catalog import load_registry
from muse_presets.playbooks import load_playbook
from muse_presets.cli import main
from muse_presets import portable_connectors as pc


def observation(item="artifact-1", text="Synthetic verification") -> dict:
    return {"id": item, "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "observation": text}


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.base = Path(self.dir.name)

    def plan(self, role="coordinator", category="source-control",
             request_id="request-01", provider="offline-fixture"):
        return pc.plan_connector(role,category,request_id=request_id,provider=provider)

    def test_eleven_role_catalogs_are_exact_and_default_disabled(self):
        roles = load_registry()["presets"]
        self.assertEqual(len(roles),11)
        for role in roles:
            r = pc.role_connectors(role)
            b = load_playbook(role)
            self.assertEqual(r["role"],role)
            self.assertEqual(set(r["categories"]),set(b["optional_tool_categories"]))
            self.assertTrue(all(x["connected"] is False for x in r["categories"].values()))
            self.assertTrue(all(x["can_execute"] is False for x in r["categories"].values()))
            self.assertTrue(all(x["external_effect_authorized"] is False
                                for x in r["categories"].values()))
            self.assertFalse(r["native_installed"])
            self.assertFalse(r["can_dispatch"])
            self.assertRegex(r["source_sha256"],r"^[a-f0-9]{64}$")

    def test_role_specific_capability_refusal(self):
        with self.assertRaisesRegex(pc.ConnectorRefusal,"CAPABILITY_NOT_IN_ROLE"):
            self.plan("coordinator","permissioned-desktop-control")
        self.assertEqual(self.plan("reverse-engineering-researcher",
                                   "permissioned-desktop-control")["status"],"PROPOSAL_ONLY")

    def test_invalid_role_source_refused(self):
        for role in ("../../private", "unknown", "Coordinator"):
            with self.assertRaises(ValueError):pc.role_connectors(role)

    def test_no_runtime_provider_is_implicitly_connected(self):
        for provider in ("terminal", "desktop-commander", "browser-cua", "ssh"):
            p=self.plan(provider=provider)
            self.assertEqual(p["status"],"PROPOSAL_ONLY")
            self.assertFalse(p["can_execute"])
            self.assertFalse(p["provider_connected"])
            self.assertFalse(p["owner_grant_verified"])
            self.assertFalse(p["recipient_readback_verified"])
            self.assertIsNone(p["target_host"])
            self.assertIsNone(p["owner_id"])
            self.assertIsNone(p["provider_operation_id"])

    def test_unknown_provider_and_target_request_refused(self):
        with self.assertRaisesRegex(pc.ConnectorRefusal,"UNSUPPORTED_PROVIDER"):
            self.plan(provider="custom-backdoor")
        with self.assertRaises(TypeError):
            pc.plan_connector("coordinator","source-control",request_id="req",
                              provider="ssh",target_host="localhost")

    def test_invalid_request_id_refused(self):
        for request_id in ("", "..", "space separated", "a"*101):
            with self.assertRaisesRegex(pc.ConnectorRefusal,"INVALID_REQUEST_ID"):
                self.plan(request_id=request_id)

    def test_fixture_is_useful_readonly_sorted_and_not_provider_proof(self):
        p=self.plan()
        rows=[observation("two","Second"),observation("one","First")]
        copy=json.loads(json.dumps(rows))
        result=pc.run_offline_fixture(p,rows)
        self.assertEqual(rows,copy)
        self.assertEqual(result["status"],"FIXTURE_ONLY")
        self.assertEqual([x["id"] for x in result["observations"]],["one","two"])
        self.assertEqual(result["observation_count"],2)
        self.assertFalse(result["can_execute"])
        self.assertFalse(result["native_invocation_verified"])
        self.assertFalse(result["recipient_acknowledged"])
        self.assertFalse(result["provider_response_authenticated"])
        self.assertEqual(pc.reconcile_fixture(p,rows,result)["status"],
                         "CONSISTENT_OFFLINE_FIXTURE_ONLY")

    def test_fixture_cannot_claim_ssh_desktop_or_other_remote_execution(self):
        p=self.plan(provider="desktop-commander")
        with self.assertRaisesRegex(pc.ConnectorRefusal,"PROVIDER_NOT_OFFLINE_FIXTURE"):
            pc.run_offline_fixture(p,[observation()])
        p=self.plan(provider="ssh")
        with self.assertRaisesRegex(pc.ConnectorRefusal,"PROVIDER_NOT_OFFLINE_FIXTURE"):
            pc.run_offline_fixture(p,[observation()])

    def test_invalid_fixture_shapes_and_duplicate_observations_refused(self):
        p=self.plan()
        bad=[
            [],[observation(),observation()],
            [{"id":"x","observation":"text"}],
            [{"id":"x","sha256":"0"*64,"observation":"x","command":"rm -rf /"}],
            [{"id":"x","sha256":"bad","observation":"x"}],
            [observation("a"*101)],
            [observation()]*33,
        ]
        for items in bad:
            with self.subTest(items=str(items)[:90]):
                with self.assertRaises(pc.ConnectorRefusal):
                    pc.run_offline_fixture(p,items)

    def test_unsigned_observation_hash_must_match_bytes(self):
        p=self.plan()
        row=observation()
        row["sha256"]="a"*64
        with self.assertRaisesRegex(pc.ConnectorRefusal,"OBSERVATION_HASH_MISMATCH"):
            pc.run_offline_fixture(p,[row])

    def test_reconcile_rejects_changed_source_role_or_response(self):
        p=self.plan()
        rows=[observation()]
        result=pc.run_offline_fixture(p,rows)
        for mutation in (
            {"status":"REAL_EXECUTION_COMPLETE"},
            {"owner_grant_verified":True},
            {"provider_response_authenticated":True},
            {"can_execute":True},
            {"source_sha256":"a"*64},
            {"role":"reverse-engineering-researcher"},
            {"provider_operation_id":"forged"},
            {"observations":[observation("forged")]},
        ):
            test={**result,**mutation}
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(pc.ConnectorRefusal,"FIXTURE_RECEIPT_MISMATCH"):
                    pc.reconcile_fixture(p,rows,test)

    def test_reconcile_wrong_original_request_refused(self):
        p=self.plan(request_id="request-01")
        receipt=pc.run_offline_fixture(p,[observation()])
        changed=self.plan(request_id="request-02")
        with self.assertRaisesRegex(pc.ConnectorRefusal,"FIXTURE_RECEIPT_MISMATCH"):
            pc.reconcile_fixture(changed,[observation()],receipt)

    def test_plan_rejects_source_corruption(self):
        with patch.object(pc,"_playbook_bytes",return_value=b'{"wrong":"role"}'):
            with self.assertRaises(pc.ConnectorRefusal):
                pc.role_connectors("coordinator")

    def test_cli_plan_and_offline_fixture_do_not_create_files(self):
        out=io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["connector-plan","--preset","coordinator",
                                   "--capability","source-control",
                                   "--request-id","fixture-001"]),0)
        plan=json.loads(out.getvalue())
        self.assertEqual(plan["status"],"PROPOSAL_ONLY")
        path=self.base/"observations.json"
        rows=[observation()]
        path.write_text(json.dumps(rows),encoding="utf-8")
        before=path.read_bytes()
        out=io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["connector-fixture","--preset","coordinator",
                                   "--capability","source-control",
                                   "--request-id","fixture-001",
                                   "--file",str(path)]),0)
        result=json.loads(out.getvalue())
        self.assertEqual(result["status"],"FIXTURE_ONLY")
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(list(self.base.iterdir()),[path])

    def test_cli_refuses_unknown_category_and_unreadable_fixture(self):
        out=io.StringIO()
        with redirect_stdout(out):
            code=main(["connector-plan","--preset","coordinator",
                       "--capability","permissioned-desktop-control",
                       "--request-id","p1"])
        self.assertNotEqual(code,0)
        self.assertEqual(json.loads(out.getvalue())["status"],"REFUSED")
        out=io.StringIO()
        with redirect_stdout(out):
            code=main(["connector-fixture","--preset","coordinator",
                       "--capability","source-control",
                       "--request-id","p1","--file",str(self.base/"missing.json")])
        self.assertNotEqual(code,0)

    def test_operator_documentation_has_no_private_host_id(self):
        doc=(Path(__file__).resolve().parents[1]/"docs/R44_PORTABLE_CONNECTORS.md").read_text(encoding="utf-8")
        for role in load_registry()["presets"]:
            self.assertIn(role,doc)
        self.assertIn("GitHub",doc)
        self.assertIn("not connected",doc.casefold())
        for word in ("example-owner-user","example-private-host","legacy-role-alpha","legacy-role-eta","example-private-network"):
            self.assertNotIn(word,doc.casefold())

    def test_duplicate_json_keys_are_rejected_without_execution(self):
        p=self.base/"fixture.json"
        p.write_text('[{"id":"a","id":"b","sha256":"'+("a"*64)+'","observation":"x"}]',encoding="utf-8")
        with self.assertRaises(pc.ConnectorRefusal):
            pc.load_fixture_file(p)

    def test_symlinked_fixture_never_read_if_supported(self):
        private=self.base/"external-secret"
        private.write_text("synthetic secret",encoding="utf-8")
        link=self.base/"fixture-link"
        try:
            link.symlink_to(private)
        except (OSError,NotImplementedError):
            self.skipTest("symlinks not supported on this host")
        with self.assertRaises(pc.ConnectorRefusal):
            pc.load_fixture_file(link)
        self.assertEqual(private.read_text(),"synthetic secret")

    def test_oversized_fixture_input_rejected(self):
        p=self.base/"oversized.json"
        p.write_text("x"*32769,encoding="utf-8")
        with self.assertRaises(pc.ConnectorRefusal):
            pc.load_fixture_file(p)

    def test_spoofed_local_plan_must_not_call_backend(self):
        p=self.plan()
        mutated={**p,"can_execute":True,"owner_grant_verified":True}
        with self.assertRaisesRegex(pc.ConnectorRefusal,"PLAN_TAMPERED"):
            pc.run_offline_fixture(mutated,[observation()])
        self.assertFalse(p["can_execute"])

    def test_untrusted_control_characters_are_refused(self):
        p=self.plan()
        text="bad\0text"
        record={"id":"bad-1","sha256":hashlib.sha256(text.encode()).hexdigest(),
                "observation":text}
        with self.assertRaises(pc.ConnectorRefusal):
            pc.run_offline_fixture(p,[record])

    def test_github_source_release_contract_is_clear(self):
        doc=(Path(__file__).resolve().parents[1]/"docs/GITHUB_RELEASE_SCOPE.md").read_text(encoding="utf-8")
        for phrase in ("GitHub", "source", "not required", "native", "clean", "private"):
            self.assertIn(phrase,doc)
        self.assertIn("11",doc)
        self.assertIn("T32",doc)


if __name__=="__main__":
    unittest.main()
