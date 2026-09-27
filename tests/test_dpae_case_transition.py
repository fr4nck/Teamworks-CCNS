from datetime import datetime
import unittest
from domain.dpae.case_transition import DpaeCapability,DpaeCaseEvent,DpaeCaseTransitionService,RULES,TransitionContext
from domain.dpae.model import DpaeCase,DpaeCaseStatus,DpaeDomainError
ALL_CAPS=frozenset(DpaeCapability)

def make_case(status=DpaeCaseStatus.DRAFT,version=0): return DpaeCase(id="c1",case_key="key",contract_id="ct1",created_at=datetime(2026,10,1,8),status=status,version=version)
def valid_context(**changes):
 values=dict(actor_id="tester",capabilities=ALL_CAPS,expected_version=0,contract_complete=True,validation_blocking_errors=0,validation_fresh=True,source_data_changed=False,correction_applied=True,submission_started=False,uncertain_submission_exists=False,return_confirmed=True,positive_evidence=True,definitive_rejection=True,transport_acceptance_proven=True,pending_transmission_proven=True,timeout_reached=True,evidence_archived=True,reason_code="TEST_REASON"); values.update(changes); return TransitionContext(**values)

class DpaeCaseTransitionTests(unittest.TestCase):
 def setUp(self): self.service=DpaeCaseTransitionService()
 def test_every_declared_rule_reaches_its_target_with_valid_context(self):
  for (source,event),rule in RULES.items():
   with self.subTest(source=source,event=event):
    case=make_case(source); ctx=valid_context(positive_evidence=event not in {DpaeCaseEvent.RETURN_RESOLVED_REJECTED,DpaeCaseEvent.REJECTION_RETURN,DpaeCaseEvent.RECONCILED_REJECTED,DpaeCaseEvent.CANCEL_CASE},definitive_rejection=event in {DpaeCaseEvent.RETURN_RESOLVED_REJECTED,DpaeCaseEvent.REJECTION_RETURN,DpaeCaseEvent.RECONCILED_REJECTED,DpaeCaseEvent.DEFINITIVE_REJECTION},source_data_changed=event is DpaeCaseEvent.SOURCE_DATA_CHANGED,validation_blocking_errors=1 if event is DpaeCaseEvent.VALIDATION_FAILED else 0); self.assertEqual(rule.target,self.service.transition(case,event,ctx)); self.assertEqual(1,case.version)
 def test_unknown_transition_is_rejected(self):
  case=make_case(DpaeCaseStatus.CLOSED)
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(case,DpaeCaseEvent.CONFIRM_SUBMISSION,valid_context())
  self.assertEqual("DPAE-T001",caught.exception.code)
 def test_stale_version_wins_before_any_business_guard(self):
  case=make_case(DpaeCaseStatus.READY,version=3)
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(case,DpaeCaseEvent.CONFIRM_SUBMISSION,valid_context(expected_version=2))
  self.assertEqual("DPAE-I010",caught.exception.code); self.assertEqual(DpaeCaseStatus.READY,case.status)
 def test_submit_requires_capability(self):
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(make_case(DpaeCaseStatus.READY),DpaeCaseEvent.CONFIRM_SUBMISSION,valid_context(capabilities=frozenset()))
  self.assertEqual("DPAE-A001",caught.exception.code)
 def test_outcome_unknown_has_no_direct_resubmit_transition(self):
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(make_case(DpaeCaseStatus.OUTCOME_UNKNOWN),DpaeCaseEvent.CONFIRM_SUBMISSION,valid_context())
  self.assertEqual("DPAE-T001",caught.exception.code)
 def test_ready_submit_is_blocked_by_uncertain_previous_submission(self):
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(make_case(DpaeCaseStatus.READY),DpaeCaseEvent.CONFIRM_SUBMISSION,valid_context(uncertain_submission_exists=True))
  self.assertEqual("DPAE-I006",caught.exception.code)
 def test_positive_return_requires_confirmed_return(self):
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(make_case(DpaeCaseStatus.WAITING_RETURN),DpaeCaseEvent.POSITIVE_RETURN,valid_context(return_confirmed=False))
  self.assertEqual("DPAE-P006",caught.exception.code)
 def test_registered_cannot_close_without_archived_evidence(self):
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(make_case(DpaeCaseStatus.REGISTERED),DpaeCaseEvent.ARCHIVE_EVIDENCE,valid_context(evidence_archived=False))
  self.assertEqual("DPAE-P016",caught.exception.code)
 def test_exceptional_close_requires_reason(self):
  with self.assertRaises(DpaeDomainError) as caught:self.service.transition(make_case(DpaeCaseStatus.REJECTED),DpaeCaseEvent.CLOSE_WITHOUT_RESUBMISSION,valid_context(reason_code=None))
  self.assertEqual("DPAE-P015",caught.exception.code)

if __name__=="__main__": unittest.main()
