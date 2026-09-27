from datetime import datetime
import unittest
from domain.dpae import CorrelationStatus,DpaeDomainError,DpaeReturn,DpaeReturnType,DpaeSubmission,DpaeSubmissionState

class DpaeDomainTests(unittest.TestCase):
    def submission(self): return DpaeSubmission("s1","c1","snap1",1,"cmd-1","hash-1")
    def test_submission_transition_matrix_accepts_expected_path(self):
        s=self.submission(); s.transition_to(DpaeSubmissionState.SENDING); s.transition_to(DpaeSubmissionState.TECHNICALLY_ACCEPTED); s.transition_to(DpaeSubmissionState.PROCESSED); self.assertEqual(DpaeSubmissionState.PROCESSED,s.state)
    def test_rejected_submission_cannot_be_sent_again(self):
        s=self.submission(); s.transition_to(DpaeSubmissionState.SENDING); s.transition_to(DpaeSubmissionState.REJECTED)
        with self.assertRaises(DpaeDomainError) as ctx:s.transition_to(DpaeSubmissionState.SENDING)
        self.assertEqual("DPAE-I-TRANSITION",ctx.exception.code)
    def test_unconfirmed_return_cannot_have_business_effect(self):
        r=self._return(); self.assertFalse(r.may_have_business_effect); r.correlation_status=CorrelationStatus.MANUAL_REVIEW_REQUIRED; self.assertFalse(r.may_have_business_effect)
    def test_same_concurrent_confirmation_is_idempotent(self):
        r=self._return(); self.assertEqual("CONFIRMED",r.confirm_correlation("s1","c1",0)); self.assertEqual("ALREADY_CONFIRMED",r.confirm_correlation("s1","c1",0)); self.assertEqual(1,r.version)
    def test_different_concurrent_confirmation_is_rejected(self):
        r=self._return(); r.confirm_correlation("s1","c1",0)
        with self.assertRaises(DpaeDomainError) as ctx:r.confirm_correlation("s2","c1",0)
        self.assertEqual("DPAE_CORRELATION_STALE",ctx.exception.code); self.assertEqual("s1",r.submission_id)
    def test_confirmed_return_is_only_state_allowed_to_have_business_effect(self):
        r=self._return(); r.confirm_correlation("s1","c1",0); self.assertTrue(r.may_have_business_effect)
    @staticmethod
    def _return(): return DpaeReturn(id="r1",provider="URSSAF",return_type=DpaeReturnType.RETURN_41,raw_hash="abc",received_at=datetime(2026,9,27,10,0))

if __name__=="__main__": unittest.main()
