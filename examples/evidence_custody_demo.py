"""Run the public, generic Evidence Finder custody example with synthetic text."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from muse_presets.evidence_custody import EvidenceLedger


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="showcase_evidence_demo_") as tmp:
        workspace = Path(tmp)
        source = workspace / "sources"
        source.mkdir()
        state = workspace / "state"
        state.mkdir()
        item = source / "fictional_observation.txt"
        item.write_bytes(b"Fictional test item.\nFinding: the light is on.\n")
        ledger = EvidenceLedger(state, role_id="evidence-finder")
        first = ledger.record(
            operation_id="example001", source_root=source,
            relative_path=item.name, query="light is on",
        )
        item.unlink()  # Show custody survives after original source removal.
        reopened = ledger.read("example001")
        check = ledger.verify()
        assert first["receipt"]["chain_sha256"] == reopened["receipt"]["chain_sha256"]
        assert reopened["finding"]["text"] == "Fictional test item.\nFinding: the light is on.\n"
        assert check["receipt_count"] == 1
        print(json.dumps({
            "status": "LOCAL_DEMO_PASSED",
            "recorded": first["status"],
            "reopened": reopened["status"],
            "outcome": reopened["outcome"],
            "source_sha256": reopened["source_sha256"],
            "receipt_count": check["receipt_count"],
            "local_chain_verified": check["local_chain_verified"],
            "host_principal_verified": False,
            "native_muse_invoked": False,
            "external_effect_performed": False,
        }, indent=2))


if __name__ == "__main__":
    main()
