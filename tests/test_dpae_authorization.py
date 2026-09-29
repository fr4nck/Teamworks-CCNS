import unittest

from domain.dpae.authorization import (
    ActorContext, ActorType, AcknowledgeDpaeWarnings, ApplyConfirmedReturn,
    ExceptionallyCloseDpaeCase, ExecuteAuthorizedSubmission, RequestDpaeSubmission,
    ResolveAmbiguousCorrelation, authorize_command,
)
from domain.dpae.case_transition import DpaeCapability
from domain.dpae.model import DpaeDomainError


class DpaeAuthorizationTests(unittest.TestCase):
    def test_human_submit_with_capability_is_allowed(self):
        authorize_command(RequestDpaeSubmission(), ActorContext(ActorType.USER, "u1", frozenset({DpaeCapability.SUBMIT})))

    def test_human_submit_without_capability_is_denied(self):
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(RequestDpaeSubmission(), ActorContext(ActorType.USER, "u1"))
        self.assertEqual("DPAE-A001", caught.exception.code)

    def test_job_cannot_submit_even_if_it_has_human_capability(self):
        actor = ActorContext(ActorType.JOB, "DPAE_SEND_RETRY_JOB", frozenset({DpaeCapability.SUBMIT}))
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(RequestDpaeSubmission(), actor)
        self.assertEqual("DPAE-A002", caught.exception.code)

    def test_service_cannot_acknowledge_warning_even_with_review_capability(self):
        actor = ActorContext(ActorType.SERVICE, "DPAE_VALIDATOR", frozenset({DpaeCapability.REVIEW_RETURN}))
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(AcknowledgeDpaeWarnings(), actor)
        self.assertEqual("DPAE-A002", caught.exception.code)

    def test_job_cannot_resolve_ambiguous_correlation(self):
        actor = ActorContext(ActorType.JOB, "DPAE_CORRELATION_JOB", frozenset({DpaeCapability.REVIEW_RETURN}))
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(ResolveAmbiguousCorrelation(), actor)
        self.assertEqual("DPAE-A002", caught.exception.code)

    def test_job_cannot_exceptionally_close_even_with_all_capabilities(self):
        actor = ActorContext(ActorType.JOB, "DPAE_CLOSURE_JOB", frozenset(DpaeCapability))
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(ExceptionallyCloseDpaeCase(), actor)
        self.assertEqual("DPAE-A002", caught.exception.code)

    def test_gateway_may_execute_already_authorized_submission(self):
        authorize_command(ExecuteAuthorizedSubmission(), ActorContext(ActorType.SERVICE, "DPAE_GATEWAY"))

    def test_retry_job_may_execute_but_not_authorize_submission(self):
        retry = ActorContext(ActorType.JOB, "DPAE_SEND_RETRY_JOB", frozenset({DpaeCapability.SUBMIT}))
        authorize_command(ExecuteAuthorizedSubmission(), retry)
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(RequestDpaeSubmission(), retry)
        self.assertEqual("DPAE-A002", caught.exception.code)

    def test_wrong_service_is_explicitly_denied(self):
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(ApplyConfirmedReturn(), ActorContext(ActorType.SERVICE, "DPAE_GATEWAY"))
        self.assertEqual("DPAE-A003", caught.exception.code)

    def test_unknown_job_is_explicitly_denied(self):
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(ExecuteAuthorizedSubmission(), ActorContext(ActorType.JOB, "SOME_OTHER_JOB"))
        self.assertEqual("DPAE-A004", caught.exception.code)

    def test_unknown_command_fails_closed(self):
        class UnknownCommand: pass
        with self.assertRaises(DpaeDomainError) as caught:
            authorize_command(UnknownCommand(), ActorContext(ActorType.USER, "u1", frozenset(DpaeCapability)))
        self.assertEqual("DPAE-A006", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
