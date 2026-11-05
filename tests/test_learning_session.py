"""Nonclinical learning engine acceptance. A host-issued role is simulated here."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
import tempfile
import threading
import unittest
from pathlib import Path

from muse_presets.learning_session import LearningScope, LearningSession


TEXT = """Gravity :: An attractive interaction between objects with mass.
Observation :: A recorded description of an event.
This paragraph does not qualify as a card.
"""


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / 'learning.sqlite'
        self.clock = 1_800_000_000_000
        self.owner = LearningScope('owner-1', 'space-1', 'student-1', 'owner-1', 'session-owner', 'owner')
        self.specialist = LearningScope('owner-1', 'space-1', 'student-1', 'educator-1', 'session-specialist', 'specialist')
        self.learner = LearningScope('owner-1', 'space-1', 'student-1', 'student-1', 'session-study', 'learner')
        self.host_role = self.owner
        self.session = LearningSession(self.db_path, authority=lambda: self.host_role, clock_ms=lambda: self.clock)
        self.addCleanup(self.session.close)

    def _source(self, text=TEXT, version='v1', source_id='science-notes'):
        return self.session.register_source(source_id=source_id, version=version, text=text)

    def _drafts(self):
        self.host_role = self.specialist
        proposed = self.session.propose_source_facts('science-notes')
        self.assertEqual(proposed['counts']['generated'], 2)
        self.assertEqual(proposed['counts']['skipped'], 1)
        return proposed['drafts']

    def _approved(self):
        self._source()
        card = self._drafts()[0]
        self.host_role = self.owner
        receipt = self.session.review(draft_id=card['draft_id'], digest=card['digest'],
                                      operation_id='approval-1', decision='approve')
        self.assertEqual(receipt['decision'], 'approve')
        return card

    def _issue(self):
        card = self._approved()
        self.host_role = self.learner
        question = self.session.issue(draft_id=card['draft_id'], challenge_id='challenge-1')
        return card, question

    def test_unbound_host_does_not_create_file(self):
        missing = self.db_path.with_name('missing.sqlite')
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNBOUND'):
            LearningSession(missing)
        self.assertFalse(missing.exists())

    def test_host_contract_rejects_forgery_and_owner_mismatch(self):
        self._source()
        self.host_role = {'owner_id': 'owner-1', 'role': 'owner'}
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNVERIFIED'):
            self.session.propose_source_facts('science-notes')
        self.host_role = LearningScope('owner-1','space-1','student-1','wrong-owner','session-x','owner')
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNVERIFIED'):
            self.session.register_source(source_id='other', version='v1', text=TEXT)
        self.host_role = LearningScope('owner-1','space-1','student-1','intruder','session-x','learner')
        with self.assertRaisesRegex(ValueError, 'HOST_AUTHORITY_UNVERIFIED'):
            self.session.review_queue()

    def test_source_admission_immutable_idempotent_and_scoped(self):
        source = self._source()
        self.assertEqual(source['version'], 'v1')
        self.assertEqual(source['lines'], 3)
        self.assertEqual(source['trust'], 'OWNER_SUPPLIED_UNVERIFIED_CONTENT')
        self.assertEqual(self._source(), source)
        with self.assertRaisesRegex(ValueError, 'SOURCE_VERSION_CONFLICT'):
            self._source(text='Gravity :: A different text.')
        self.host_role = LearningScope('owner-2','space-1','student-1','owner-2','session-owner','owner')
        self.assertIsNone(self.session.source('science-notes'))
        self._source(text='Altitude :: Height above a reference surface.')
        self.assertNotEqual(self.session.source('science-notes')['sha256'], source['sha256'])

    def test_source_roles_and_input_constraints(self):
        self.host_role = self.specialist
        with self.assertRaisesRegex(ValueError, 'OWNER_APPROVAL_REQUIRED'):
            self._source()
        self.host_role = self.owner
        for bad in ('', 'Bad\x00', 'Gravity :: It\u202e is hidden.', 'x'*32769):
            with self.subTest(bad=repr(bad[:20])), self.assertRaises(ValueError):
                self._source(text=bad)
        with self.assertRaisesRegex(ValueError, 'INVALID_SOURCE_ID'):
            self._source(source_id='../escape')

    def test_quote_generator_provenance_and_consistent_id(self):
        source = self._source()
        cards = self._drafts()
        self.assertEqual({x['source_locator'] for x in cards}, {'science-notes@v1:line-1','science-notes@v1:line-2'})
        self.assertEqual(cards[0]['answer'], 'An attractive interaction between objects with mass.')
        self.assertEqual(cards[0]['source_sha256'], source['sha256'])
        self.assertEqual(cards[0]['status'], 'HELD_FOR_OWNER_REVIEW')
        self.assertFalse(cards[0]['clinically_validated'])
        self.assertEqual(cards, self.session.propose_source_facts('science-notes')['drafts'])
        self.assertEqual(self.session.draft(cards[0]['draft_id'])['digest'], cards[0]['digest'])

    def test_untrusted_prompts_and_html_do_not_produce_cards(self):
        self._source(text='Ignore previous instructions.\n<html> :: run this\nA :: B\nGravity :: A valid definition.\n')
        self.host_role = self.specialist
        result = self.session.propose_source_facts('science-notes')
        self.assertEqual(result['counts']['generated'], 1)
        self.assertEqual(result['counts']['skipped'], 3)
        self.assertIn('Gravity', result['drafts'][0]['question'])

    def test_duplicate_facts_are_skipped_not_silently_overwritten(self):
        self._source(text='Climate :: The long-term weather pattern.\nClimate :: A different description.\n')
        self.host_role = self.specialist
        result = self.session.propose_source_facts('science-notes')
        self.assertEqual(result['counts']['generated'], 1)
        self.assertEqual(result['counts']['skipped'], 1)

    def test_generator_discloses_truncation_and_respects_limit(self):
        self._source(text='\n'.join(f'Concept {i} :: Explanation number {i}.' for i in range(20)))
        self.host_role = self.specialist
        r = self.session.propose_source_facts('science-notes',limit=2)
        self.assertEqual(len(r['drafts']),2)
        self.assertEqual(r['counts']['generated'],20)
        self.assertTrue(r['truncated'])
        with closing(sqlite3.connect(self.db_path)) as raw, raw:
            self.assertEqual(raw.execute('SELECT count(*) FROM study_drafts').fetchone()[0], 2)
        with self.assertRaisesRegex(ValueError,'INVALID_LIMIT'):
            self.session.propose_source_facts('science-notes',limit=True)

    def test_source_bytes_tampering_blocks_new_drafts_and_reviews(self):
        self._source()
        card = self._drafts()[0]
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("UPDATE study_source_versions SET body='Tampered' WHERE source_key='science-notes'")
        with self.assertRaisesRegex(ValueError, 'SOURCE_DIGEST_MISMATCH'):
            self.session.propose_source_facts('science-notes')
        self.host_role = self.owner
        with self.assertRaisesRegex(ValueError, 'SOURCE_DIGEST_MISMATCH'):
            self.session.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='x',decision='approve')

    def test_owner_approves_only_original_draft_and_receipt_reopens(self):
        card = self._approved()
        first = self.session.receipt('approval-1')
        self.assertEqual(first['draft_id'],card['draft_id'])
        reopened = LearningSession(self.db_path,authority=lambda:self.owner,clock_ms=lambda:self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.receipt('approval-1'),first)
        self.assertEqual(reopened.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='approval-1',decision='approve'),first)
        with self.assertRaisesRegex(ValueError, 'OPERATION_CONFLICT'):
            reopened.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='approval-1',decision='decline')
        with self.assertRaisesRegex(ValueError, 'DRAFT_NOT_HELD'):
            reopened.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='approval-new',decision='approve')

    def test_specialist_cannot_approve_and_learner_cannot_see_draft_answer(self):
        self._source()
        card = self._drafts()[0]
        with self.assertRaisesRegex(ValueError, 'OWNER_APPROVAL_REQUIRED'):
            self.session.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='op-1',decision='approve')
        self.host_role = self.learner
        with self.assertRaisesRegex(ValueError, 'REVIEWER_SCOPE_REQUIRED'):
            self.session.draft(card['draft_id'])
        with self.assertRaisesRegex(ValueError, 'QUESTION_NOT_APPROVED'):
            self.session.issue(draft_id=card['draft_id'],challenge_id='hidden')

    def test_decline_is_immutable_nonissuable(self):
        self._source()
        card = self._drafts()[0]
        self.host_role = self.owner
        r = self.session.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='decline-1',decision='decline')
        self.assertEqual(r['decision'],'decline')
        self.host_role = self.learner
        with self.assertRaisesRegex(ValueError,'QUESTION_NOT_APPROVED'):
            self.session.issue(draft_id=card['draft_id'],challenge_id='blocked')

    def test_stale_source_version_blocks_old_draft_and_question(self):
        card, _ = self._issue()
        self.host_role = self.owner
        newer = self._source(version='v2',text='Gravity :: A revised definition.')
        self.assertEqual(newer['version'],'v2')
        with self.assertRaisesRegex(ValueError,'SOURCE_VERSION_STALE'):
            self.session.review(draft_id=card['draft_id'],digest=card['digest'],operation_id='old',decision='decline')
        self.host_role = self.learner
        with self.assertRaisesRegex(ValueError,'SOURCE_VERSION_STALE'):
            self.session.submit(challenge_id='challenge-1',operation_id='attempt-stale',answer='guess')
        self.assertIsNone(self.session.score_receipt('attempt-stale'))
        self.assertEqual(self.session.review_queue()['eligible'],0)

    def test_issued_challenge_does_not_leak_answer_or_source_body(self):
        card, challenge = self._issue()
        self.assertEqual(challenge['question'],card['question'])
        self.assertNotIn('answer',challenge)
        self.assertNotIn('source_text',challenge)
        self.assertNotIn('quote',challenge)
        self.assertEqual(challenge['status'],'CHALLENGE_OPEN')
        self.assertEqual(challenge['source_locator'],card['source_locator'])
        self.assertEqual(challenge,self.session.issue(draft_id=card['draft_id'],challenge_id='challenge-1'))
        with self.assertRaisesRegex(ValueError,'CHALLENGE_CONFLICT'):
            self.session.issue(draft_id='different-card',challenge_id='challenge-1')

    def test_challenge_session_isolation(self):
        card, challenge = self._issue()
        self.host_role = LearningScope('owner-1','space-1','student-1','student-1','different-session','learner')
        with self.assertRaisesRegex(ValueError, 'CHALLENGE_SESSION_MISMATCH'):
            self.session.submit(challenge_id=challenge['challenge_id'],operation_id='evil',answer=card['answer'])
        self.assertIsNone(self.session.score_receipt('evil'))
        self.host_role = LearningScope('owner-1','space-2','student-1','student-1','session-study','learner')
        with self.assertRaisesRegex(ValueError, 'CHALLENGE_NOT_FOUND'):
            self.session.submit(challenge_id=challenge['challenge_id'],operation_id='evil',answer=card['answer'])
        self.host_role = LearningScope('owner-1','space-1','student-2','student-2','session-study','learner')
        with self.assertRaisesRegex(ValueError, 'CHALLENGE_NOT_FOUND'):
            self.session.submit(challenge_id=challenge['challenge_id'],operation_id='evil',answer=card['answer'])

    def test_submitted_answer_is_scored_and_replay_idempotent(self):
        card, challenge = self._issue()
        result = self.session.submit(challenge_id='challenge-1',operation_id='attempt-1',answer='  AN ATTRACTIVE interaction between objects with Mass.  ')
        self.assertTrue(result['correct'])
        self.assertEqual(result['answer'], card['answer'])
        self.assertEqual(result['source_locator'],card['source_locator'])
        self.assertEqual(result['status'],'RECORDED_NOT_MASTERY_PROOF')
        again = self.session.submit(challenge_id='challenge-1',operation_id='attempt-1',answer='  AN ATTRACTIVE interaction between objects with Mass.  ')
        self.assertEqual(result,again)
        with self.assertRaisesRegex(ValueError,'OPERATION_CONFLICT'):
            self.session.submit(challenge_id='challenge-1',operation_id='attempt-1',answer='wrong')
        with self.assertRaisesRegex(ValueError,'CHALLENGE_ALREADY_ANSWERED'):
            self.session.submit(challenge_id='challenge-1',operation_id='attempt-2',answer=card['answer'])
        reopened=LearningSession(self.db_path,authority=lambda:self.learner,clock_ms=lambda:self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.score_receipt('attempt-1'),result)
        self.assertEqual(reopened.submit(challenge_id='challenge-1',operation_id='attempt-1',answer='  AN ATTRACTIVE interaction between objects with Mass.  '),result)

    def test_score_receipt_not_reusable_from_different_learner_session(self):
        card,_ = self._issue()
        result=self.session.submit(challenge_id='challenge-1',operation_id='attempt-1',answer=card['answer'])
        self.host_role=LearningScope('owner-1','space-1','student-1','student-1','different-session','learner')
        with self.assertRaisesRegex(ValueError,'CHALLENGE_SESSION_MISMATCH'):
            self.session.score_receipt('attempt-1')
        with self.assertRaisesRegex(ValueError,'CHALLENGE_SESSION_MISMATCH'):
            self.session.submit(challenge_id='challenge-1',operation_id='attempt-1',answer=card['answer'])
        self.host_role=self.learner
        self.assertEqual(self.session.score_receipt('attempt-1'),result)

    def test_draft_mutation_after_generation_refused_before_approval(self):
        self._source()
        card=self._drafts()[0]
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute('UPDATE study_drafts SET answer=? WHERE draft_key=?',('fake answer',card['draft_id']))
        self.host_role=self.owner
        with self.assertRaisesRegex(ValueError, 'SOURCE_QUOTE_MISMATCH'):
            self.session.review(draft_id=card['draft_id'], digest=card['digest'], operation_id='tampered',decision='approve')

    def test_wrong_answer_scoring_does_not_infer_synonyms(self):
        card, challenge = self._issue()
        result = self.session.submit(challenge_id='challenge-1',operation_id='attempt-wrong',answer='force')
        self.assertFalse(result['correct'])
        self.assertEqual(result['status'],'RECORDED_NOT_MASTERY_PROOF')

    def test_expired_challenge_at_exact_boundary(self):
        card, challenge = self._issue()
        self.clock=challenge['expires_ms']
        with self.assertRaisesRegex(ValueError,'CHALLENGE_EXPIRED'):
            self.session.submit(challenge_id='challenge-1',operation_id='late',answer=card['answer'])
        self.assertIsNone(self.session.score_receipt('late'))

    def test_due_review_is_pure_projection_of_attempt_history(self):
        card, _ = self._issue()
        q=self.session.review_queue()
        self.assertEqual(q['eligible'],1)
        self.assertEqual(q['queue'][0]['basis'],'NOT_ATTEMPTED')
        receipt=self.session.submit(challenge_id='challenge-1',operation_id='attempt-1',answer=card['answer'])
        q=self.session.review_queue()
        self.assertFalse(q['queue'][0]['due'])
        self.assertEqual(q['queue'][0]['basis'],'CORRECT')
        self.clock += 24*60*60*1000
        q=self.session.review_queue()
        self.assertTrue(q['queue'][0]['due'])
        self.assertEqual(q['queue'][0]['attempts'],1)
        self.assertEqual(q['policy'],'HEURISTIC_V1_NOT_FSRS')

    def test_incorrect_answer_due_immediately_and_bounded_list(self):
        card,_=self._issue()
        self.session.submit(challenge_id='challenge-1',operation_id='wrong',answer='wrong')
        q=self.session.review_queue(limit=1)
        self.assertEqual(q['queue'][0]['basis'],'INCORRECT')
        self.assertTrue(q['queue'][0]['due'])
        with self.assertRaisesRegex(ValueError,'INVALID_LIMIT'):
            self.session.review_queue(limit=0)

    def test_write_failure_rolls_back_score_and_original_challenge(self):
        card,_=self._issue()
        with closing(sqlite3.connect(self.db_path)) as raw, raw:
            raw.execute("CREATE TRIGGER abort_grading BEFORE INSERT ON study_score_receipts BEGIN SELECT RAISE(ABORT, 'blocked'); END")
        with self.assertRaisesRegex(ValueError,'OUTCOME_UNKNOWN_RECONCILE_BY_OPERATION_ID'):
            self.session.submit(challenge_id='challenge-1',operation_id='bad-db',answer=card['answer'])
        self.assertIsNone(self.session.score_receipt('bad-db'))
        with closing(sqlite3.connect(self.db_path)) as raw, raw:
            self.assertEqual(raw.execute("SELECT count(*) FROM study_attempts").fetchone()[0],0)
            raw.execute('DROP TRIGGER abort_grading')
        r=self.session.submit(challenge_id='challenge-1',operation_id='bad-db',answer=card['answer'])
        self.assertTrue(r['correct'])

    def test_two_connections_cannot_double_grade_one_challenge(self):
        card,_=self._issue()
        other=LearningSession(self.db_path,authority=lambda:self.learner,clock_ms=lambda:self.clock)
        self.addCleanup(other.close)
        outcomes=[]
        def worker(service,op):
            try:
                result=service.submit(challenge_id='challenge-1',operation_id=op,answer=card['answer'])
                outcomes.append(result)
            except ValueError as error:
                outcomes.append(str(error))
        t1=threading.Thread(target=worker,args=(self.session,'op-A'))
        t2=threading.Thread(target=worker,args=(other,'op-B'))
        t1.start();t2.start();t1.join();t2.join()
        self.assertEqual(len(outcomes),2)
        self.assertEqual(sum(isinstance(o,dict) for o in outcomes),1)
        self.assertIn('CHALLENGE_ALREADY_ANSWERED',outcomes)
        with closing(sqlite3.connect(self.db_path)) as raw, raw:
            self.assertEqual(raw.execute('SELECT count(*) FROM study_attempts').fetchone()[0],1)

    def test_invalid_clock_and_symlink_database_refused(self):
        self.clock=-1
        with self.assertRaisesRegex(ValueError,'SERVER_CLOCK_INVALID'):
            self._source()
        self.clock=1_800_000_000_000
        target=Path(self.temp.name)/'actual';target.mkdir()
        link=Path(self.temp.name)/'alias'
        try: link.symlink_to(target,target_is_directory=True)
        except (OSError,NotImplementedError): self.skipTest('symlink privilege unavailable')
        with self.assertRaisesRegex(ValueError,'UNSAFE_DATABASE_PATH'):
            LearningSession(link/'data.sqlite',authority=lambda:self.owner)


if __name__=='__main__':
    unittest.main()
