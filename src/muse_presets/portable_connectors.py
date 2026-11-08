"""Portable role-scoped connector contracts for GitHub source packages.

All providers are disabled/unbound. Only explicitly supplied synthetic
observations can be normalized locally; no shell, browser, desktop, network,
model, scheduling, host discovery or recipient calls are performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .catalog import ROOT, load_registry
from .family import REQUEST_ID
from .native_canary import _no_duplicate_json, _reject_constant
from .native_skill_binding import _regular_bytes
from .playbooks import load_playbook

SCHEMA="r44/portable-connector-v1"
FIXTURE_SCHEMA="r44/offline-connector-fixture-v1"
MAX_SOURCE_BYTES=131072
MAX_FIXTURE_BYTES=32768
MAX_OBSERVATIONS=32
CATEGORY=re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PROVIDERS=frozenset({
    "offline-fixture", "terminal", "desktop-commander", "browser-cua", "ssh"
})


class ConnectorRefusal(ValueError):
    pass


def _bytes(value:Any)->bytes:
    return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False,
                       allow_nan=False)+"\n").encode("utf-8")


def _sha(value:bytes)->str:
    return hashlib.sha256(value).hexdigest()


def _playbook_bytes(role:str)->bytes:
    return _regular_bytes(ROOT/"presets"/role/"playbook.json",MAX_SOURCE_BYTES)


def role_connectors(role:str)->dict:
    """Load *actual* role allowlist and source hash, not a new controller."""
    if type(role) is not str or not CATEGORY.fullmatch(role):
        raise ConnectorRefusal("INVALID_ROLE")
    if role not in load_registry()["presets"]:
        raise ConnectorRefusal("ROLE_NOT_IN_CATALOG")
    try:
        source=_playbook_bytes(role)
        playbook=json.loads(source.decode("utf-8"),object_pairs_hook=_no_duplicate_json,
                            parse_constant=_reject_constant)
        if playbook!=load_playbook(role) or not isinstance(playbook,dict):
            raise ConnectorRefusal("SOURCE_PLAYBOOK_MISMATCH")
        categories=playbook.get("optional_tool_categories")
        if (not isinstance(categories,list) or not 1<=len(categories)<=16
            or not all(type(x) is str and CATEGORY.fullmatch(x) for x in categories)
            or len(set(categories))!=len(categories)):
            raise ConnectorRefusal("INVALID_ROLE_CAPABILITY_CATALOG")
    except (OSError,UnicodeError,ValueError,TypeError,KeyError) as exc:
        raise ConnectorRefusal("INVALID_ROLE_SOURCE") from exc
    return {
        "schema":SCHEMA,"role":role,"source_sha256":_sha(source),
        "categories":{x:{"connected":False,"can_execute":False,
                          "external_effect_authorized":False,
                          "adapter":"REQUIRES_OWNER_CONFIG"}
                      for x in categories},
        "native_installed":False,
        "can_dispatch":False,
        "providers_configured":[],
        "grant_scope":"NOT_ISSUED",
    }


def plan_connector(role:str,capability:str,*,request_id:str,
                   provider:str="offline-fixture")->dict:
    """Reviewable proposal, with no host/path/credential or effect authority."""
    catalog=role_connectors(role)
    if type(capability) is not str or capability not in catalog["categories"]:
        raise ConnectorRefusal("CAPABILITY_NOT_IN_ROLE")
    if type(request_id) is not str or REQUEST_ID.fullmatch(request_id) is None:
        raise ConnectorRefusal("INVALID_REQUEST_ID")
    if type(provider) is not str or provider not in PROVIDERS:
        raise ConnectorRefusal("UNSUPPORTED_PROVIDER")
    base={
        "schema":SCHEMA,"status":"PROPOSAL_ONLY",
        "role":role,"capability":capability,"request_id":request_id,
        "provider":provider,"source_sha256":catalog["source_sha256"],
        "provider_connected":False,"owner_grant_verified":False,
        "owner_id":None,"target_host":None,"provider_operation_id":None,
        "can_execute":False,"external_effect_authorized":False,
        "recipient_readback_verified":False,
        "retry_policy":"NO_RETRY_WITHOUT_ORIGINAL_PROVIDER_RECONCILIATION",
        "next":"OWNER_CONFIGURES_AND_AUTHORIZES_ADAPTER_IF_REQUIRED",
    }
    # Digest excludes its own digest field. It detects accidental or naive
    # edits, not malicious signing or a provider-issued effect receipt.
    return {**base,"plan_sha256":_sha(_bytes(base))}


def _normalize_observations(rows:Any)->list[dict]:
    if type(rows) is not list or not 1<=len(rows)<=MAX_OBSERVATIONS:
        raise ConnectorRefusal("OBSERVATION_COUNT_INVALID")
    result=[]
    seen=set()
    for row in rows:
        if type(row) is not dict or set(row)!={"id","sha256","observation"}:
            raise ConnectorRefusal("OBSERVATION_FIELDS_INVALID")
        identifier=row["id"]
        if type(identifier) is not str or REQUEST_ID.fullmatch(identifier) is None:
            raise ConnectorRefusal("OBSERVATION_ID_INVALID")
        if identifier in seen:
            raise ConnectorRefusal("OBSERVATION_DUPLICATE_ID")
        seen.add(identifier)
        text=row["observation"]
        if (type(text) is not str or not text.strip()
            or len(text.encode("utf-8"))>2048
            or any(ord(c)<32 and c not in "\n\t" for c in text)):
            raise ConnectorRefusal("OBSERVATION_TEXT_INVALID")
        digest=row["sha256"]
        if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise ConnectorRefusal("OBSERVATION_DIGEST_INVALID")
        if _sha(text.encode("utf-8"))!=digest:
            raise ConnectorRefusal("OBSERVATION_HASH_MISMATCH")
        result.append({"id":identifier,"sha256":digest,"observation":text})
    return sorted(result,key=lambda x:x["id"])


def run_offline_fixture(plan:dict,observations:Any)->dict:
    """Actually normalize caller-provided synthetic rows, never a remote call."""
    if type(plan) is not dict:
        raise ConnectorRefusal("INVALID_PLAN")
    expected=plan_connector(plan.get("role"),plan.get("capability"),
                            request_id=plan.get("request_id"),
                            provider=plan.get("provider"))
    if plan!=expected:
        raise ConnectorRefusal("PLAN_TAMPERED_OR_SOURCE_CHANGED")
    if expected["provider"]!="offline-fixture":
        raise ConnectorRefusal("PROVIDER_NOT_OFFLINE_FIXTURE")
    normalized=_normalize_observations(observations)
    return {
        "schema":FIXTURE_SCHEMA,"status":"FIXTURE_ONLY",
        "role":expected["role"],"capability":expected["capability"],
        "request_id":expected["request_id"],
        "provider":"offline-fixture",
        "source_sha256":expected["source_sha256"],
        "plan_sha256":expected["plan_sha256"],
        "observation_count":len(normalized),
        "observation_sha256":_sha(_bytes(normalized)),
        "observations":normalized,
        "native_invocation_verified":False,
        "provider_response_authenticated":False,
        "recipient_acknowledged":False,
        "owner_grant_verified":False,
        "can_execute":False,
        "external_effect_authorized":False,
        "provider_operation_id":None,
    }


def reconcile_fixture(plan:dict,observations:Any,reported:Any)->dict:
    """Detect inconsistent local fixtures; never endorse real-world effects."""
    expected=run_offline_fixture(plan,observations)
    if type(reported) is not dict or reported!=expected:
        raise ConnectorRefusal("FIXTURE_RECEIPT_MISMATCH")
    return {"status":"CONSISTENT_OFFLINE_FIXTURE_ONLY",
            "request_id":expected["request_id"],
            "source_sha256":expected["source_sha256"],
            "provider_authenticated":False,
            "owner_grant_verified":False,
            "can_execute":False,"recipient_readback_verified":False}


def load_fixture_file(path:Path)->Any:
    """Bounded, read-only fixture JSON; reject symlinks and duplicate keys."""
    try:
        data=_regular_bytes(Path(path),MAX_FIXTURE_BYTES)
        return json.loads(data.decode("utf-8"),object_pairs_hook=_no_duplicate_json,
                          parse_constant=_reject_constant)
    except (OSError,ValueError,TypeError,UnicodeError) as exc:
        raise ConnectorRefusal("FIXTURE_FILE_INVALID") from exc
