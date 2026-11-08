#!/usr/bin/env python3
"""Portable local Claim Gate interface for a generic Software Engineer.

Execution is SOURCE-LOCAL only. This CLI DOES NOT execute a work item,
authenticate Muse owners, authorize a third-party effect, or call a model.
Every mutating verb changes only explicit local claim-state files.

On Windows, do not import POSIX-fcntl modules. Refuse the CLI until a
separately tested platform adapter is available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

_COMPONENT=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_SOURCE=16384
_ALLOWED=frozenset(("claim","inspect","verify-bytes","cancel","hold-unknown"))


class CliRefusal(ValueError):
    pass


def reject(reason: str) -> None:
    raise CliRefusal(reason)


def _admitted_root(root:str,*,error:str)->Path:
    path=Path(root)
    if not path.is_absolute() or '..' in path.parts:
        reject(error)
    for node in (path,*path.parents):
        if node.is_symlink() or (
                hasattr(node,'is_junction') and node.is_junction()):
            # Apple ships /var, /tmp and /etc as stable links to /private.
            # Only these exact system-level aliases are permitted.
            allowed=(sys.platform=='darwin' and
                     str(node) in ('/var','/tmp','/etc') and
                     str(node.resolve(strict=True))==
                         {'/var':'/private/var','/tmp':'/private/tmp',
                          '/etc':'/private/etc'}[str(node)])
            if not allowed:
                reject(error)
    if not path.is_dir():
        reject(error)
    return path


def _payload(root: str | None, name: str | None) -> bytes:
    if not root or not name or not _COMPONENT.fullmatch(name) or name.startswith("."):
        reject("SOURCE_PATH_REFUSED")
    parent=_admitted_root(root,error="SOURCE_PATH_REFUSED")
    file=parent/name
    if file.is_symlink():
        reject("SOURCE_PATH_REFUSED")
    try:
        pre=file.lstat()
        if not stat.S_ISREG(pre.st_mode) or not 0<pre.st_size<=_MAX_SOURCE:
            reject("SOURCE_SIZE_OR_TYPE_REFUSED")
        fd=os.open(file,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
        with os.fdopen(fd,"rb") as src:
            opened=os.fstat(src.fileno())
            value=src.read(_MAX_SOURCE+1)
            after=os.fstat(src.fileno())
        identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns)
        if identity(pre)!=identity(opened) or identity(opened)!=identity(after) or len(value)!=pre.st_size:
            reject("SOURCE_CHANGED_DURING_READ")
        return value
    except OSError:
        reject("SOURCE_UNAVAILABLE")


def _state_dir(root: str) -> str:
    path=_admitted_root(root,error="STATE_DIRECTORY_NOT_ADMITTED")
    if path.resolve()==Path(path.anchor):
        reject("STATE_DIRECTORY_NOT_ADMITTED")
    return str(path)


def _reason(value: str | None) -> str:
    if not isinstance(value,str) or not value.strip() or len(value)>256:
        reject("REASON_REQUIRED")
    if any(ord(c)<32 and c not in ("\n","\t") for c in value):
        reject("REASON_INVALID")
    return value


def _output(scope: str,claim_id: str,*,status: str,
            record: dict | None=None,mutated: bool=False) -> dict:
    state=record.get("state") if record else None
    return {
        "schema":"software-engineer/local-claim-gate-v1",
        "status":status,
        "scope":scope,
        "claim_id":claim_id,
        "state":state,
        "payload_sha256":record.get("payload_digest") if record else None,
        "state_record_modified":mutated,
        "native_muse_invoked":False,
        "host_owner_authenticated":False,
        "external_effect_authorized":False,
        "external_effect_performed":False,
        "recipient_acknowledged":False,
        "original_engine":"source-derived-claim-gate",
        "execution_grade":"LOCAL_CLAIM_STATE_ONLY",
    }


def run(args: argparse.Namespace) -> dict:
    if os.name!="posix":
        reject("UNSUPPORTED_PLATFORM_POSIX_FCNTL_REQUIRED")
    if args.action not in _ALLOWED:
        reject("UNSUPPORTED_ACTION")
    if not _COMPONENT.fullmatch(args.scope) or not _COMPONENT.fullmatch(args.claim_id):
        reject("INVALID_CLAIM_COMPONENT")
    root=_state_dir(args.state_dir)
    # Fail source admission before constructing the original state engine;
    # an untrusted or missing file must not even create an empty claim tree.
    source=(_payload(args.source_root,args.payload)
            if args.action in ("claim","verify-bytes") else None)

    # Only import the source-derived modules AFTER rejecting unsupported OS
    # and unsafe state paths; no arbitrary plugins or imports are executed.
    module_home=Path(__file__).resolve().parent
    if module_home.is_symlink():
        reject("ENGINE_SOURCE_SYMLINK_REFUSED")
    sys.path.insert(0,str(module_home))
    from claim_gate import ClaimGate,ReplayRefused,ClaimGateError
    gate=ClaimGate(root)
    scope,identifier=args.scope,args.claim_id

    if args.action=="inspect":
        found=gate.reconcile_unknown(scope,identifier)
        return _output(scope,identifier,status=(
            "LOCAL_CLAIM_OBSERVED" if found is not None else "LOCAL_CLAIM_ABSENT"),record=found)

    if args.action=="verify-bytes":
        present=gate.reconcile_unknown(scope,identifier)
        matched=gate.verify_bytes(scope,identifier,source)
        return {**_output(scope,identifier,status=(
            "LOCAL_SOURCE_MATCH" if matched else "LOCAL_SOURCE_NOT_MATCHED"),record=present),
            "source_verified_against_claim":matched}

    if args.action=="claim":
        try:
            claimed,prior=gate.claim(scope,identifier,source)
        except ReplayRefused:
            reject("REPLAY_REFUSED")
        except ClaimGateError:
            reject("CLAIM_STATE_UNKNOWN_HOLD")
        if claimed:
            state=gate.reconcile_unknown(scope,identifier)
            return _output(scope,identifier,status="LOCAL_CLAIM_RECORDED",
                           record=state,mutated=True)
        # Additional safeguard: original terminal CANCELLED behavior returns
        # the previous record without a changed-byte error. Check explicitly.
        if not gate.verify_bytes(scope,identifier,source):
            reject("REPLAY_REFUSED")
        return _output(scope,identifier,status="LOCAL_CLAIM_REUSED",
                       record=prior)

    reason=_reason(args.reason)
    try:
        if args.action=="hold-unknown":
            record=gate.mark_unknown(scope,identifier,reason)
            return _output(scope,identifier,status="LOCAL_UNKNOWN_HELD",
                           record=record,mutated=True)
        if args.action=="cancel":
            record=gate.cancel(scope,identifier,reason)
            return _output(scope,identifier,status="LOCAL_CLAIM_CANCELLED",
                           record=record,mutated=True)
    except ClaimGateError:
        reject("CLAIM_TRANSITION_REFUSED")
    reject("UNSUPPORTED_ACTION")


def main(argv:list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir",required=True)
    parser.add_argument("--scope",required=True)
    parser.add_argument("--claim-id",required=True)
    parser.add_argument("action")
    parser.add_argument("--source-root")
    parser.add_argument("--payload")
    parser.add_argument("--reason")
    options=parser.parse_args(argv)
    try:
        result=run(options)
        print(json.dumps(result,sort_keys=True,separators=(",",":")))
        return 0
    except CliRefusal as exc:
        reason=str(exc)
    except (OSError,ValueError,ImportError) as exc:
        reason="CLAIM_GATE_UNAVAILABLE_OR_INVALID"
    print(json.dumps({
        "status":"REFUSED","error_code":reason,
        "native_muse_invoked":False,
        "external_effect_authorized":False,
        "external_effect_performed":False,
        "host_owner_authenticated":False,
    },sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
