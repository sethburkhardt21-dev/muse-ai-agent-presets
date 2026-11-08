"""R32 independent TOCTOU source-pin regressions: synthetic mid-stage read injection.

Never modifies canonical source or private donor. Patches the stager's read
function within a temporary staging invocation, simulating a source change
after the preflight manifest check but before the staged file copy.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
from unittest import TestCase, main
from unittest.mock import patch
import tempfile, json
from muse_presets import engineering_pack as pack

class PinContinuityReview(TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="r32-read-race-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name).resolve()
        self.original=pack._bytes
        self.poison=b"---\nname: local-unreviewed\n---\nThis is an injected synthetic test fixture.\n"

    def simulate(self, source, expected_subtree, injected=None):
        hit=[0]
        def inject(path,*args,**kwargs):
            if Path(path)==source:
                hit[0]+=1
                if hit[0]>=2:
                    return self.poison if injected is None else injected
            return self.original(path,*args,**kwargs)
        dest=self.root/expected_subtree
        with patch.object(pack,"_bytes",side_effect=inject):
            try:
                result=pack.stage_engineer_pack(dest)
                error=None
            except Exception as exc:
                result=None
                error=type(exc).__name__+":"+str(exc)
        return dest,result,error,hit[0]

    def test_iron_skill_changed_after_preflight_must_be_refused(self):
        source=pack.IRON_SKILL_ROOT/"SKILL.md"
        trusted=json.loads(pack.IRON_MANIFEST.read_text())["skills"]["SKILL.md"]
        dest,result,error,hits=self.simulate(source,"iron-candidate")
        copied=dest/"skills"/"iron-ledger"/"SKILL.md"
        if copied.exists():
            self.assertNotEqual(sha256(copied.read_bytes()).hexdigest(),trusted)
            observed=pack.inspect_engineer_pack(dest)["status"]
            print("IRON_COPY_CHANGED",json.dumps({"inspector":observed,
               "source_read_count":hits,"manifest_pin_unchanged":True,
               "canonical_source_modified":False,"original_files_modified":False}))
        self.assertIsNone(result, "Stager accepted a post-preflight changed skill")

    def test_claim_gate_skill_changed_after_preflight_must_be_refused(self):
        source=pack.SKILL_ROOT/"SKILL.md"
        trusted=json.loads(pack.ENGINE_MANIFEST.read_text())["skills"]["SKILL.md"]
        dest,result,error,hits=self.simulate(source,"claim-skill-candidate")
        copied=dest/"skills"/"claim-gate"/"SKILL.md"
        if copied.exists():
            self.assertNotEqual(sha256(copied.read_bytes()).hexdigest(),trusted)
            observed=pack.inspect_engineer_pack(dest)["status"]
            print("CLAIM_SKILL_COPY_CHANGED",json.dumps({"inspector":observed,
                "source_read_count":hits,"original_pin_unchanged":True,
                "canonical_source_modified":False}))
        self.assertIsNone(result, "Stager accepted a post-preflight changed Claim Gate skill")

    def test_iron_engine_manifest_authority_change_after_preflight_refused(self):
        source=pack.IRON_MANIFEST
        expected=source.read_bytes()
        changed=json.loads(expected)
        changed["external_effects_enabled"]=True
        changed["registered_native_tools"]=["unexpected-tool"]
        manipulated=(json.dumps(changed,sort_keys=True)+"\n").encode("utf-8")
        dest,result,error,hits=self.simulate(source,"iron-engine-manifest",manipulated)
        staged=dest/"runtime"/"iron-ledger"/"ENGINE.json"
        if staged.exists():
            self.assertNotEqual(staged.read_bytes(),expected)
            data=json.loads(staged.read_text())
            print("IRON_ENGINE_MANIFEST_CHANGED",json.dumps({
                "inspector":pack.inspect_engineer_pack(dest)["status"],
                "source_read_count":hits,
                "staged_manifest_claims_effects":data["external_effects_enabled"],
                "original_source_unchanged":source.read_bytes()==expected}))
        self.assertIsNone(result,"Stager accepted changed engine authority manifest after preflight")

    def test_iron_skill_yaml_approval_change_after_preflight_is_refused(self):
        source=pack.IRON_SKILL_ROOT/"skill.yaml"
        manifest=json.loads(pack.IRON_MANIFEST.read_text())
        trusted=manifest["skills"]["skill.yaml"]
        changed=(b"name: engineering_evidence_receipt_consumer\n"
                 b"include_in_prompt: true\n"
                 b"authorization: incorrectly_approved\n")
        dest,result,error,hits=self.simulate(source,"iron-metadata",changed)
        copied=dest/"skills"/"iron-ledger"/"skill.yaml"
        if copied.exists():
            self.assertNotEqual(sha256(copied.read_bytes()).hexdigest(),trusted)
            print("IRON_SKILL_METADATA_CHANGED",json.dumps({
                "inspector":pack.inspect_engineer_pack(dest)["status"],
                "source_read_count":hits,"copied_include_in_prompt_enabled":b"include_in_prompt: true" in copied.read_bytes(),
                "canonical_source_modified":False}))
        self.assertIsNone(result,"Stager accepted unpinned post-preflight skill.yaml")

    def test_vault_runtime_changed_after_preflight_is_refused(self):
        source=pack.VAULT_SOURCE
        dest,result,error,hits=self.simulate(source,"vault-runtime-control")
        self.assertIsNone(result)
        self.assertIn("SOURCE_PIN_MISMATCH",error or "")

    def test_iron_runtime_changed_after_preflight_is_refused(self):
        source=pack.IRON_SOURCE
        dest,result,error,hits=self.simulate(source,"iron-runtime-control")
        self.assertIsNone(result)
        self.assertIn("SOURCE_PIN_MISMATCH",error or "")

    def test_vault_skill_changed_after_preflight_must_be_refused(self):
        source=pack.VAULT_SKILL_ROOT/"SKILL.md"
        trusted=json.loads(pack.VAULT_MANIFEST.read_text())["skills"]["SKILL.md"]
        dest,result,error,hits=self.simulate(source,"vault-candidate")
        copied=dest/"skills"/"provenance-vault"/"SKILL.md"
        if copied.exists():
            self.assertNotEqual(sha256(copied.read_bytes()).hexdigest(),trusted)
            observed=pack.inspect_engineer_pack(dest)["status"]
            print("VAULT_COPY_CHANGED",json.dumps({"inspector":observed,
               "source_read_count":hits,"manifest_pin_unchanged":True,
               "canonical_source_modified":False}))
        self.assertIsNone(result, "Stager accepted a post-preflight changed skill")

    def test_claimgate_runtime_source_change_is_already_refused_control(self):
        source=pack.ENGINE_ROOT/"claim_gate.py"
        dest,result,error,hits=self.simulate(source,"runtime-candidate")
        print("CLAIM_GATE_CONTROL",json.dumps({"source_read_count":hits,"error":error,
            "staging_incomplete":(dest/"STAGING_INCOMPLETE").exists()}))
        self.assertIsNone(result)
        self.assertIn("SOURCE_PIN_MISMATCH",error or "")

    def test_policy_changes_are_refused_before_any_destination_exists(self):
        inputs=[
            (pack.SKILL_ROOT/"SKILL.md","claim-policy-fail"),
            (pack.VAULT_SKILL_ROOT/"skill.yaml","vault-meta-fail"),
            (pack.IRON_SKILL_ROOT/"SKILL.md","iron-skill-fail"),
            (pack.IRON_MANIFEST,"iron-manifest-fail"),
        ]
        for source,name in inputs:
            with self.subTest(name=name):
                dest,result,error,_=self.simulate(source,name)
                self.assertIsNone(result)
                self.assertFalse(dest.exists(),"A refused policy must not create a destination")
                self.assertTrue(error)

    def test_duplicate_engine_manifest_keys_fail_even_if_semantically_equal(self):
        source=pack.IRON_MANIFEST
        original=source.read_bytes()
        key=b'"native_muse_status": "UNBOUND",'
        self.assertIn(key,original)
        duplicate=original.replace(key,key+b'\n  '+key,1)
        dest,result,error,_=self.simulate(
            source,"duplicate-engine-manifest",injected=duplicate)
        self.assertIsNone(result)
        self.assertFalse(dest.exists())
        self.assertIn("SOURCE_MANIFEST_DUPLICATE_KEY",error or "")

if __name__=="__main__":
    main(verbosity=2)
