"""Family Link proposal-only adapter. No transport, signing or host grants.

Only accepts bounded, named role references; never impersonates a native agent.
"""
from __future__ import annotations

import re
from .catalog import load_registry, load_preset

REQUEST_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
ALLOWED_FINDING_KEYS = frozenset({'source_uri','source_sha256','observation','result'})

class FamilyLinkRefusal(ValueError):
    pass


def _recipient_set() -> set[str]:
    reg = load_registry()
    return set(reg['presets']) | set(reg['services'])


def propose_handoff(sender: str, receiver: str, *, request_id: str, capability: str) -> dict:
    """Produce a preview without sending, creating identity or assuming native link."""
    reg = load_registry()
    if sender not in reg['presets']:
        raise FamilyLinkRefusal('UNKNOWN_SENDER_OR_SERVICE_MUST_USE_OWN_INBOX')
    if receiver not in _recipient_set() or receiver == sender:
        raise FamilyLinkRefusal('UNKNOWN_OR_SELF_RECEIVER')
    if not isinstance(request_id,str) or not REQUEST_ID.fullmatch(request_id):
        raise FamilyLinkRefusal('INVALID_REQUEST_ID')
    if not isinstance(capability,str) or not REQUEST_ID.fullmatch(capability):
        raise FamilyLinkRefusal('INVALID_CAPABILITY')
    settings = load_preset(sender)['family_link']
    if receiver not in settings['suggested_receivers']:
        raise FamilyLinkRefusal('RECEIVER_NOT_IN_PREVIEW_POLICY')
    return {'schema':'muse-presets/family-handoff-preview-v1',
            'state':'PROPOSAL_ONLY_NOT_SENT', 'admission':'HOST_AND_RECIPIENT_REQUIRED',
            'request_id':request_id,'sender_role':sender,'receiver_role':receiver,
            'requested_capability':capability,'family_link_enabled':False,
            'native_receipt':False,'recipient_acknowledged':False,
            'effect_authorized':False}


def verify_finding(finding: dict) -> dict:
    """Validate a finder record's shape, NOT its authenticity or source claims."""
    if not isinstance(finding,dict) or set(finding) != ALLOWED_FINDING_KEYS:
        raise FamilyLinkRefusal('FINDING_SHAPE_REFUSED_NO_VERDICT_FIELD')
    if not isinstance(finding.get('source_uri'),str) or not finding['source_uri']:
        raise FamilyLinkRefusal('SOURCE_URI_REQUIRED')
    if not isinstance(finding.get('source_sha256'),str) or not SHA256.fullmatch(finding['source_sha256']):
        raise FamilyLinkRefusal('SHA256_REQUIRED')
    if finding.get('result') not in ('FOUND','NOT_FOUND'):
        raise FamilyLinkRefusal('INVALID_FINDING_RESULT')
    if not isinstance(finding.get('observation'),str):
        raise FamilyLinkRefusal('OBSERVATION_MUST_BE_STRING')
    if finding['result']=='FOUND' and not finding['observation'].strip():
        raise FamilyLinkRefusal('FOUND_REQUIRES_OBSERVATION')
    if finding['result']=='NOT_FOUND' and finding['observation'].strip():
        raise FamilyLinkRefusal('NULL_FINDING_MUST_BE_EMPTY')
    return {'status':'VALID_FINDING_ONLY','source_authenticated':False,
            'verdict_present':False,'receiver_accepted':False}
