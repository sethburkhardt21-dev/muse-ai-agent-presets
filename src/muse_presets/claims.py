"""Conservative claim/scope checker; not an independent adjudication authority."""
from __future__ import annotations

GRADES = ('SOURCE_PRESENT', 'LOCAL_TESTED', 'HOST_WIRED', 'NATIVE_USED', 'INDEPENDENT_USEFUL')


def assess_scope(statement: str, asserted_grade: str, evidence_grade: str, *, conditions: tuple[str, ...]) -> dict:
    """Flag grades wider than their declared evidence, retaining all conditions.

    The supplied evidence grade is a claim by the caller, not a proven attestation.
    """
    if not isinstance(statement, str) or not statement.strip() or len(statement) > 1000:
        raise ValueError('INVALID_CLAIM')
    if asserted_grade not in GRADES or evidence_grade not in GRADES:
        raise ValueError('UNKNOWN_GRADE')
    if (not isinstance(conditions, (tuple, list)) or not conditions
            or any(not isinstance(c, str) or not c.strip() or len(c) > 1000 for c in conditions)):
        raise ValueError('CONDITIONS_REQUIRED')
    return {
        'schema': 'muse-presets/claims-scope-v1',
        'statement': statement,
        'asserted_grade': asserted_grade,
        'declared_evidence_grade': evidence_grade,
        'conditions': list(conditions),
        'disposition': ('OVERCLAIM' if GRADES.index(asserted_grade) > GRADES.index(evidence_grade)
                        else 'WITHIN_DECLARED_SCOPE_UNAUTHENTICATED'),
        'independent_verified': False,
        'effect_authorized': False,
    }
