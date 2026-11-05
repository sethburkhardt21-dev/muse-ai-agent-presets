"""Disposable, fictional evidence-to-review learning pipeline.

Run from repo root: PYTHONPATH=src python examples/learning_session_demo.py
Only local SQLite is affected. No Muse, credential, account or scheduler action.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from muse_presets.learning_session import LearningScope, LearningSession


def main() -> None:
    with TemporaryDirectory(prefix='study-source-fixture-') as temp:
        database = Path(temp) / 'study.sqlite'
        roles = {
            'owner': LearningScope('fictional-owner','fictional-space','fictional-learner',
                                   'fictional-owner','owner-session','owner'),
            'specialist': LearningScope('fictional-owner','fictional-space','fictional-learner',
                                        'fictional-tutor','tutor-session','specialist'),
            'learner': LearningScope('fictional-owner','fictional-space','fictional-learner',
                                     'fictional-learner','learner-session','learner'),
        }
        live = {'scope':roles['owner'], 'now':1_800_000_000_000}
        authority=lambda: live['scope']
        clock=lambda: live['now']
        with LearningSession(database, authority=authority, clock_ms=clock) as study:
            source=study.register_source(source_id='intro-science',version='v1',text=(
                'Gravity :: An attractive interaction between objects with mass.\n'
                'Observation :: A recorded description of an event.\n'))
            live['scope']=roles['specialist']
            candidates=study.propose_source_facts('intro-science')
            assert candidates['counts']['generated']==2
            card=candidates['drafts'][0]
            live['scope']=roles['owner']
            reviewed=study.review(draft_id=card['draft_id'],digest=card['digest'],
                                  operation_id='review-01',decision='approve')
            live['scope']=roles['learner']
            challenge=study.issue(draft_id=card['draft_id'],challenge_id='challenge-01')
            assert 'answer' not in challenge
            result=study.submit(challenge_id='challenge-01',operation_id='score-01',
                                answer='An attractive interaction between objects with mass.')
            assert result['correct']
            before=study.review_queue()
            assert not before['queue'][0]['due']
        # This is the original *same* learner session reopening its local store.
        with LearningSession(database, authority=authority, clock_ms=clock) as reopened:
            assert reopened.score_receipt('score-01')==result
            assert reopened.submit(challenge_id='challenge-01',operation_id='score-01',
                                    answer='An attractive interaction between objects with mass.')==result
            live['now']+=86_400_000
            after=reopened.review_queue()
            assert after['queue'][0]['due']
        print(json.dumps({
            'status':'LOCAL_NONCLINICAL_STUDY_DEMO_PASSED',
            'source_identity_sha256':source['sha256'],
            'source_locator':card['source_locator'],
            'source_draft_count':2,
            'owner_review':reviewed['decision'],
            'score_recorded':True,
            'receipt_reopened':True,
            'review_due_after_24h':True,
            'scoring_rule':'literal_casefold_whitespace_v1',
            'review_rule':'HEURISTIC_V1_NOT_FSRS',
            'muse_native_authorized':False,
            'clinical_release_ready':False,
            'external_effects':0,
            'local_demo_database_deleted':True,
        },indent=2,sort_keys=True))


if __name__=='__main__':
    main()
