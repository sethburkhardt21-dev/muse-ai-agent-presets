"""Restart reconciliation for the Claim Gate.

After any restart (process, host, or operator handoff), the gate's durable
state must be surveyed before new work begins. This module does that survey:

    reconcile_on_restart(state_dir) -> report dict (also written durably)

For every claim record under <state_dir>/claims/<scope>/<claim_id>.json it
reports exactly one classification:

- SETTLED        — EFFECT_DONE or CANCELLED. Nothing to do.
- HELD_LIVE      — CLAIMED with a live lease (owner + expiry shown).
- TAKEABLE       — CLAIMED with an expired or absent lease. A new owner may
                   take it over; the decision belongs to the caller, not here.
- HELD_UNKNOWN   — UNKNOWN. The outcome was never confirmed. Reconciliation
                   stays read-only; the owner must investigate the actual
                   effect target before any new claim id is issued.
- CORRUPT        — unreadable or shape-invalid record. Preserved on disk,
                   listed for investigation. Never silently repaired.

This module NEVER executes an effect, NEVER mutates a claim file, NEVER takes
a lease, and NEVER deletes anything. It reads, classifies, and reports. A
restarted worker that finds its own HELD_LIVE claim may resume it; a worker
that finds a TAKEABLE claim it used to own must treat itself as fenced until
it takes over explicitly through claim_lease.

Local vs multi-host: this survey reads the local filesystem state. On one
host it is exact. Across hosts sharing state, lease timestamps are advisory
(see the Second Charter); the fencing token remains the cross-host truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time

from claim_gate import (
    ClaimGate,
    CorruptClaimRecord,
    CANCELLED,
    EFFECT_DONE,
    UNKNOWN,
)


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def classify_record(record: dict, now: float) -> dict:
    """Classify one claim record. Pure function."""
    state = record.get("state")
    if state in (EFFECT_DONE, CANCELLED):
        return {"class": "SETTLED", "state": state,
                "outcome": record.get("outcome")}
    if state == UNKNOWN:
        return {"class": "HELD_UNKNOWN", "state": state,
                "note": "outcome unconfirmed; reconcile read-only; "
                        "investigate the effect target before any new claim"}
    if state == "CLAIMED":
        holder = record.get("lease_owner")
        expires = record.get("lease_expires_epoch")
        # D8: defensive — the real restart path routes through _read_claim
        # (garbage epochs become CORRUPT there); a direct hostile dict
        # answers "not live" instead of raising.
        live = False
        if holder is not None and expires is not None:
            try:
                live = now < float(expires)
            except (TypeError, ValueError):
                live = False
        if live:
            return {"class": "HELD_LIVE", "state": state,
                    "lease_owner": holder,
                    "lease_expires_ts": record.get("lease_expires_ts"),
                    "fencing_token": record.get("fencing_token")}
        return {"class": "TAKEABLE", "state": state,
                "last_owner": holder,
                "last_token": record.get("fencing_token"),
                "note": "lease expired or absent; takeover permitted via claim_lease"}
    return {"class": "CORRUPT", "state": state,
            "note": "unrecognized state; preserved for investigation"}


def reconcile_on_restart(state_dir: str, report_path: str | None = None) -> dict:
    """Survey all claim records. Read-only. Returns and durably writes a report."""
    gate = ClaimGate(state_dir)  # for path layout + _read_claim only
    now = time.time()
    claims_root = os.path.join(os.path.abspath(state_dir), "claims")

    report: dict = {
        "generated_at": _utcnow(),
        "generated_epoch": now,
        "state_dir": os.path.abspath(state_dir),
        "records": [],
        "summary": {},
    }
    counts: dict[str, int] = {}

    if os.path.isdir(claims_root):
        for scope in sorted(os.listdir(claims_root)):
            scope_dir = os.path.join(claims_root, scope)
            if not os.path.isdir(scope_dir):
                continue
            for name in sorted(os.listdir(scope_dir)):
                if not name.endswith(".json") or name.startswith("."):
                    continue
                path = os.path.join(scope_dir, name)
                entry: dict = {"scope": scope,
                               "claim_id": name[:-len(".json")],
                               "path": path}
                try:
                    record = gate._read_claim(path)
                except CorruptClaimRecord as exc:
                    entry["classification"] = {
                        "class": "CORRUPT",
                        "note": str(exc),
                    }
                else:
                    entry["classification"] = classify_record(record, now)
                    entry["payload_sha256"] = hashlib.sha256(
                        json.dumps(record, sort_keys=True).encode()
                    ).hexdigest()
                cls = entry["classification"]["class"]
                counts[cls] = counts.get(cls, 0) + 1
                report["records"].append(entry)

    report["summary"] = {
        "total": len(report["records"]),
        "by_class": counts,
        "action_required": bool(counts.get("HELD_UNKNOWN") or counts.get("CORRUPT")),
    }

    if report_path is None:
        report_path = os.path.join(
            os.path.abspath(state_dir),
            "restart-reconciliation-%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        )
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(report_path)),
                               prefix=".restart-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, report_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    report["report_path"] = report_path
    return report


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.abspath(__file__))
    rep = reconcile_on_restart(state)
    print(json.dumps(rep["summary"], indent=2, sort_keys=True))
    print("report:", rep["report_path"])
