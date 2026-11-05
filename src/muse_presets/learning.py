"""Exact-source flashcard proposals, with no medical or pedagogical approval."""
from __future__ import annotations

import hashlib
import re

_SOURCE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$')


def draft_supported_card(source_text: str, *, source_id: str, question: str, answer: str) -> dict:
    """Create a held flashcard draft only when the answer is an exact source span."""
    if not isinstance(source_id, str) or not _SOURCE.fullmatch(source_id):
        raise ValueError('INVALID_SOURCE_ID')
    for value, kind, limit in ((source_text, 'SOURCE', 8192), (question, 'QUESTION', 512),
                               (answer, 'ANSWER', 512)):
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError('INVALID_' + kind)
    start = source_text.find(answer)
    if start < 0:
        raise ValueError('ANSWER_NOT_VERBATIM_IN_SOURCE')
    return {
        'schema': 'muse-presets/learning-card-draft-v1',
        'status': 'DRAFT_REVIEW_REQUIRED',
        'source_id': source_id,
        'source_sha256': hashlib.sha256(source_text.encode('utf-8')).hexdigest(),
        'source_span': [start, start + len(answer)],
        'question': question,
        'answer': answer,
        'reviewed': False,
        'clinically_validated': False,
        'host_authorized': False,
    }
