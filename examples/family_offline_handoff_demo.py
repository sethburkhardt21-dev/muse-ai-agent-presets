"""Two-process, source-only Family Link metadata handoff and replay-shape demo.

No network, native account, receipt authority, real consent, durable replay
ledger, delivery, signed messages or changed personal data. All inputs are
fictional and bounded. Independent real hosts are tested separately.
"""
from __future__ import annotations

from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path

from muse_presets.family_envelope import (
    prepare_offline_envelope,review_local_envelope,envelope_sha256,
)

NOW=datetime(2026,11,9,18,0,0,tzinfo=timezone.utc)


def _finding() -> dict:
    raw="Fictional source-only observation: green sprouts appear.\n"
    return {
      "source_uri":"fictional-example.txt",
      "source_sha256":hashlib.sha256(raw.encode("utf-8")).hexdigest(),
      "observation":raw,"result":"FOUND",
    }


def _save_new(path: Path,value: object) -> None:
    wire=(json.dumps(value,sort_keys=True,separators=(",",":"),
                     ensure_ascii=True,allow_nan=False)+"\n").encode("utf-8")
    with path.open("xb") as output:
        output.write(wire)


def _sender(root: Path) -> int:
    finding=_finding()
    envelope=prepare_offline_envelope(
        "model-builder","research-evaluator","fixture-13","finding-review",
        finding,True,"2026-11-09T17:59:00Z","2026-11-09T18:30:00Z",NOW)
    _save_new(root/"finding.json",finding)
    _save_new(root/"envelope.json",envelope)
    _save_new(root/"expected_pin.json",{"sha256":envelope_sha256(envelope)})
    return 0


def _receiver(root: Path) -> int:
    f=json.loads((root/"finding.json").read_text(encoding="utf-8"))
    e=json.loads((root/"envelope.json").read_text(encoding="utf-8"))
    pinned=json.loads((root/"expected_pin.json").read_text(encoding="utf-8"))
    result=review_local_envelope(e,f,pinned["sha256"],[],[],NOW,expected_receiver_role="research-evaluator")
    # Check the negative replay branch using explicit caller-supplied history;
    # this is NOT proof of a server-side durable history or an actual delivery.
    replay_refused=False
    try:
        review_local_envelope(e,f,pinned["sha256"],[e["request_id"]],[],NOW,expected_receiver_role="research-evaluator")
    except ValueError as exc:
        replay_refused="REPLAY" in str(exc)
    if not replay_refused:
        raise ValueError("LOCAL_DECLARED_REPLAY_WAS_NOT_REFUSED")
    result={**result,"replayed_id_refused":True,
            "separate_process_verified":True,
            "external_effect_authorized":False}
    sys.stdout.write(json.dumps(result,sort_keys=True)+"\n")
    return 0


def main() -> int:
    if len(sys.argv)==3 and sys.argv[1]=="--sender":
        return _sender(Path(sys.argv[2]))
    if len(sys.argv)==3 and sys.argv[1]=="--receiver":
        return _receiver(Path(sys.argv[2]))
    if len(sys.argv)!=1:
        return 2
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="r66-family-offline-fixture-") as scratch:
        root=Path(scratch)
        for action in ("--sender","--receiver"):
            p=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),
                              action,str(root)],
                 capture_output=True,env=env,timeout=25)
            if p.returncode!=0:
                sys.stderr.write(p.stderr.decode("utf-8",errors="replace"))
                return 2
            if action=="--receiver":
                sys.stdout.buffer.write(p.stdout)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
