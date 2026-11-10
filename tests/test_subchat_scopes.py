"""T05: source-only, role-scoped subchats that cannot impersonate provider chat IDs."""
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
from muse_presets.system_profile import plan_system_profile
from muse_presets import subchat_scopes as scopes
from muse_presets.cli import main


class SubchatScopesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def stage(self, role="garden-companion"):
        dest = self.root / role
        digest = plan_system_profile(role)["source_sha256"]
        result = scopes.stage_subchat_scopes(dest, role, expected_profile_source_sha256=digest)
        self.assertEqual(result["status"], "LOCAL_SUBCHATS_STAGED")
        return dest

    def test_all_eleven_roles_three_unique_nonempty_subchats(self):
        roles = load_registry()["presets"]
        self.assertEqual(len(roles), 11)
        total = 0
        for role in roles:
            dest = self.stage(role)
            method_ids = [m["id"] for m in load_playbook(role)["methods"]]
            self.assertEqual({x.name for x in (dest / "subchats").iterdir()}, set(method_ids))
            for method in method_ids:
                room = dest / "subchats" / method
                self.assertEqual({x.name for x in room.iterdir()}, set(scopes.ROOM_FILES))
                for name in scopes.ROOM_FILES:
                    self.assertGreater((room / name).stat().st_size, 0)
                metadata = json.loads((room / "SUBCHAT.json").read_text())
                self.assertEqual(metadata["method_id"], method)
                self.assertIsNone(metadata["native_chat_id"])
                self.assertIsNone(metadata["owner_id"])
                self.assertFalse(metadata["native_installed"])
                self.assertFalse(metadata["external_effect_authorized"])
                self.assertFalse(metadata["model_invocation_verified"])
                self.assertEqual((room / "skills.yaml").read_text(), "version: 1\nentries:\n")
            report = scopes.inspect_subchat_scopes(dest)
            self.assertEqual(report["status"], "LOCAL_SUBCHATS_MATCH")
            self.assertFalse(report["native_loaded"])
            self.assertFalse(report["can_apply"])
            total += 3
        self.assertEqual(total, 33)

    def test_staging_pin_mismatch_before_creating_destination(self):
        dest = self.root / "bad"
        with self.assertRaisesRegex(ValueError, "SOURCE_PIN_MISMATCH"):
            scopes.stage_subchat_scopes(dest, "software-engineer", expected_profile_source_sha256="0"*64)
        self.assertFalse(dest.exists())

    def test_invalid_role_never_creates_destination(self):
        dest = self.root / "bad"
        with self.assertRaises(ValueError):
            scopes.stage_subchat_scopes(dest, "../original-agent")
        self.assertFalse(dest.exists())

    def test_existing_destination_never_overwritten(self):
        target = self.root / "occupied"
        target.mkdir()
        (target / "MEMORY.md").write_text("owner text", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            scopes.stage_subchat_scopes(target, "coordinator")
        self.assertEqual((target / "MEMORY.md").read_text(), "owner text")

    def test_missing_parent_refused_without_effects(self):
        target = self.root / "missing" / "new"
        with self.assertRaises(FileNotFoundError):
            scopes.stage_subchat_scopes(target, "learning-coach")
        self.assertFalse(target.parent.exists())

    def test_owner_memory_and_preferences_are_reported_not_rewritten(self):
        dest = self.stage()
        room = dest / "subchats" / "observe-plant"
        (room / "MEMORY.md").write_text("owner-provided content", encoding="utf-8")
        (room / "PREFERENCES.md").write_text("owner preference", encoding="utf-8")
        report = scopes.inspect_subchat_scopes(dest)
        self.assertEqual(report["status"], "OWNER_CUSTOMIZED")
        self.assertEqual(report["owner_modified"], ["subchats/observe-plant/MEMORY.md",
                                                     "subchats/observe-plant/PREFERENCES.md"])
        self.assertEqual((room / "MEMORY.md").read_text(), "owner-provided content")
        self.assertFalse(report["native_loaded"])

    def test_tool_policy_change_refused_even_with_forged_manifest(self):
        dest = self.stage()
        room = dest / "subchats" / "observe-plant"
        tools = room / "TOOLS.md"
        tools.write_text("# Tools\nUnrestricted access is available.\n", encoding="utf-8")
        manifest = dest / scopes.MANIFEST
        entry = json.loads(manifest.read_text())
        entry["files"]["subchats/observe-plant/TOOLS.md"] = hashlib.sha256(tools.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(entry), encoding="utf-8")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")

    def test_host_claim_forged_and_self_hash_updated_refused(self):
        dest = self.stage()
        room = dest / "subchats" / "observe-plant"
        config = room / "SUBCHAT.json"
        claim = json.loads(config.read_text())
        claim["native_chat_id"] = "invented-provider-id"
        claim["native_installed"] = True
        config.write_text(json.dumps(claim), encoding="utf-8")
        receipt_path = dest / scopes.MANIFEST
        receipt = json.loads(receipt_path.read_text())
        receipt["files"]["subchats/observe-plant/SUBCHAT.json"] = hashlib.sha256(config.read_bytes()).hexdigest()
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")

    def test_missing_or_extra_file_refused(self):
        dest = self.stage()
        (dest / "subchats" / "observe-plant" / "CONTEXT.md").unlink()
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")
        second = self.stage("software-engineer")
        (second / "subchats" / "reproduce-defect" / "unauthorized.py").write_text("print(1)")
        self.assertEqual(scopes.inspect_subchat_scopes(second)["status"], "REVIEW_REQUIRED")

    def test_incomplete_stage_preserved_on_failure(self):
        dest = self.root / "failed"
        real = scopes._write_new
        counter = [0]
        def fail_midway(path, data):
            counter[0] += 1
            if counter[0] == 4:
                raise OSError("synthetic interrupted operation")
            return real(path, data)
        with patch.object(scopes, "_write_new", side_effect=fail_midway):
            with self.assertRaises(OSError):
                scopes.stage_subchat_scopes(dest, "learning-coach")
        self.assertTrue((dest / "STAGING_INCOMPLETE").exists())
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "INCOMPLETE_STAGE")

    def test_symlinked_memory_refused_without_following_target(self):
        dest = self.stage()
        secret = self.root / "outside-data"
        secret.write_text("source must not read", encoding="utf-8")
        member = dest / "subchats" / "observe-plant" / "MEMORY.md"
        member.unlink()
        try:
            member.symlink_to(secret)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")
        self.assertEqual(secret.read_text(), "source must not read")

    def test_preview_does_not_write_and_preserves_owner_memory(self):
        dest = self.stage()
        target = self.root / "host-state"
        (target / "subchats" / "observe-plant").mkdir(parents=True)
        memory = target / "subchats" / "observe-plant" / "MEMORY.md"
        memory.write_text("user memory", encoding="utf-8")
        unknown = target / "unlisted-owner-asset.txt"
        unknown.write_text("leave me", encoding="utf-8")
        result = scopes.preview_subchat_scopes(dest, target)
        self.assertFalse(result["can_apply"])
        self.assertFalse(result["native_loaded"])
        self.assertIn({"path": "subchats/observe-plant/MEMORY.md", "action": "PRESERVE_OWNER_EDIT"}, result["files"])
        self.assertEqual(memory.read_text(), "user memory")
        self.assertEqual(unknown.read_text(), "leave me")

    def test_preview_policy_conflict_is_not_an_apply_instruction(self):
        dest = self.stage()
        target = self.root / "host-state"
        (target / "subchats" / "observe-plant").mkdir(parents=True)
        (target / "subchats" / "observe-plant" / "TOOLS.md").write_text("prior owner policy")
        result = scopes.preview_subchat_scopes(dest, target)
        self.assertIn({"path": "subchats/observe-plant/TOOLS.md", "action": "REVIEW_CONFLICT"}, result["files"])
        self.assertFalse(result["can_apply"])

    def test_profile_role_mismatch_refused_by_inspector(self):
        dest = self.stage()
        manifest = dest / scopes.MANIFEST
        claim = json.loads(manifest.read_text())
        claim["role"] = "software-engineer"
        manifest.write_text(json.dumps(claim), encoding="utf-8")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")

    def test_wrong_disabled_skill_metadata_refused(self):
        dest = self.stage()
        path = dest / "subchats" / "observe-plant" / "skills.yaml"
        path.write_text("version: 1\nentries:\n  unlimited:\n    status: available\n")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")

    def test_t04_source_pin_in_bundle_matches_plan(self):
        dest = self.stage("coordinator")
        receipt = json.loads((dest / scopes.MANIFEST).read_text())
        self.assertEqual(receipt["profile_source_sha256"], plan_system_profile("coordinator")["source_sha256"])
        self.assertFalse(receipt["provider_issued_chat_ids"])
        self.assertFalse(receipt["external_effect_authorized"])

    def test_cli_stage_inspect_plan_and_preview_are_source_only(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["subchat-scopes-plan", "--preset", "software-engineer"]), 0)
        plan = json.loads(out.getvalue())
        self.assertEqual(plan["status"], "SOURCE_PLAN_ONLY")
        dest = self.root / "scopes"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["subchat-scopes", "--preset", "software-engineer", "--to", str(dest),
                                   "--profile-source-sha256", plan["profile_source_sha256"]]), 0)
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["subchat-scopes-inspect", "--path", str(dest)]), 0)
        self.assertEqual(json.loads(out.getvalue())["status"], "LOCAL_SUBCHATS_MATCH")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["subchat-scopes-preview", "--path", str(dest),
                                   "--target", str(self.root / "not-created")]), 0)
        self.assertFalse(json.loads(out.getvalue())["can_apply"])
        self.assertFalse((self.root / "not-created").exists())


    def test_method_contexts_are_distinct_and_handoffs_are_proposals(self):
        dest = self.stage("learning-coach")
        methods = load_playbook("learning-coach")["methods"]
        contexts = []
        for method in methods:
            room = dest / "subchats" / method["id"]
            context = (room / "CONTEXT.md").read_text(encoding="utf-8")
            contexts.append(context)
            self.assertIn(method["trigger"], context)
            self.assertIn(method["stop_rule"], context)
            self.assertIn(method["handoff_to"], context)
            self.assertIn("proposal only", context)
        self.assertEqual(len(set(contexts)), 3)

    def test_receipt_source_pin_forgery_is_rejected(self):
        dest = self.stage()
        path = dest / scopes.MANIFEST
        claim = json.loads(path.read_text(encoding="utf-8"))
        claim["source_pins"]["presets/garden-companion/playbook.json"] = "a" * 64
        path.write_text(json.dumps(claim), encoding="utf-8")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "SOURCE_DRIFT")

    def test_registry_identity_and_handoff_cannot_be_enabled(self):
        dest = self.stage("coordinator")
        path = dest / "config" / "subchats.json"
        claim = json.loads(path.read_text(encoding="utf-8"))
        claim["subchats"][0]["native_chat_id"] = "invented"
        claim["subchats"][0]["host_installed"] = True
        path.write_text(json.dumps(claim), encoding="utf-8")
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")

    def test_extra_unlisted_subchat_directory_is_refused(self):
        dest = self.stage()
        (dest / "subchats" / "unreviewed").mkdir()
        self.assertEqual(scopes.inspect_subchat_scopes(dest)["status"], "REVIEW_REQUIRED")

    def test_preview_rejects_tampered_candidate_without_reading_owner(self):
        dest = self.stage()
        (dest / "config" / "subchats.json").write_text("{}", encoding="utf-8")
        target = self.root / "owner-data"
        target.mkdir()
        owner = target / "secret.txt"
        owner.write_text("protected", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "UNTRUSTED_SUBCHAT_CANDIDATE"):
            scopes.preview_subchat_scopes(dest, target)
        self.assertEqual(owner.read_text(), "protected")

    def test_preview_refuses_regular_file_as_owner_folder(self):
        dest = self.stage()
        file = self.root / "regular-file"
        file.write_text("content", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "UNSAFE_SUBCHAT_TARGET"):
            scopes.preview_subchat_scopes(dest, file)
        self.assertEqual(file.read_text(), "content")


    def test_documentation_does_not_embed_original_agent_identities(self):
        text = (Path(__file__).resolve().parents[1] /
                "docs/CUSTOMIZE.md").read_text(encoding="utf-8").casefold()
        for original in ("legacy-role-eta", "legacy-role-alpha", "legacy-role-beta", "legacy-role-delta",
                         "legacy-role-gamma", "legacy-role-zeta", "legacy-role-epsilon"):
            self.assertNotIn(original, text)
        self.assertIn("native", text)
        self.assertIn("owner", text)

    def test_staged_scopes_never_promote_native_authority(self):
        dest = self.stage("software-engineer")
        metadata = json.loads((dest / "config/subchats.json").read_text())
        self.assertFalse(metadata["native_installed"])
        self.assertFalse(metadata["model_selected_invocation"])
        self.assertFalse(metadata["external_effect_authorized"])
        self.assertEqual(len(metadata["subchats"]), 3)
        for member in metadata["subchats"]:
            self.assertIsNone(member["native_chat_id"])
            self.assertFalse(member["host_installed"])

if __name__ == "__main__":
    unittest.main()
