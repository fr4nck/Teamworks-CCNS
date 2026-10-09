from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import unittest

from domain.dpae.model import DpaeDomainError, DpaeReturn, DpaeReturnType
from domain.dpae.repository import InMemoryDpaeRepository
from domain.dpae.service import DpaeCorrelationService

NOW = datetime(2026, 9, 27, 12, 0)


def make_return(return_id="r1", external_id="ext-1", raw_hash="aaa"):
    return DpaeReturn(
        id=return_id,
        provider="URSSAF",
        return_type=DpaeReturnType.RETURN_41,
        raw_hash=raw_hash,
        received_at=NOW,
        external_return_id=external_id,
    )


class DpaeConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryDpaeRepository()
        self.repo.ingest_return(make_return())
        self.service = DpaeCorrelationService(self.repo)

    def confirm(self, submission, decision):
        return self.service.confirm(
            return_id="r1", submission_id=submission, case_id="c1",
            expected_version=0, actor_id=decision, decision_id=decision,
            decided_at=NOW,
        )

    def test_conc_01_two_workers_same_candidate_are_idempotent(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda d: self.confirm("s1", d), ["w1", "w2"]))
        self.assertEqual(["ALREADY_CONFIRMED", "CONFIRMED"], sorted(results))
        self.assertEqual(1, len(self.repo.decisions))

    def test_conc_02_two_workers_different_candidates_never_overwrite(self):
        def run(args):
            try:
                return self.confirm(*args)
            except DpaeDomainError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, [("s1", "w1"), ("s2", "w2")]))
        self.assertIn("CONFIRMED", results)
        self.assertIn("DPAE_CORRELATION_STALE", results)
        self.assertEqual(1, len(self.repo.decisions))

    def test_replay_01_same_external_return_is_single_logical_return(self):
        _, status = self.repo.ingest_return(make_return(return_id="r2"))
        self.assertEqual("REPLAY", status)
        self.assertEqual(1, len(self.repo.returns))

    def test_replay_04_same_external_id_different_content_is_integrity_conflict(self):
        with self.assertRaises(DpaeDomainError) as ctx:
            self.repo.ingest_return(make_return(return_id="r2", raw_hash="bbb"))
        self.assertEqual("RETURN_INTEGRITY_CONFLICT", ctx.exception.code)
        self.assertEqual(1, len(self.repo.returns))

    def test_effect_exactly_once_after_confirmation(self):
        self.confirm("s1", "w1")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda _: self.service.apply_effect_once(
                    return_id="r1", effect_type="MARK_DPAE_REGISTERED", created_at=NOW
                ),
                range(2),
            ))
        self.assertEqual([False, True], sorted(results))
        self.assertEqual(1, self.repo.effect_count("r1", "MARK_DPAE_REGISTERED"))

    def test_unconfirmed_return_effect_is_rejected(self):
        repo = InMemoryDpaeRepository()
        repo.ingest_return(make_return())
        service = DpaeCorrelationService(repo)
        with self.assertRaises(DpaeDomainError) as ctx:
            service.apply_effect_once(return_id="r1", effect_type="X", created_at=NOW)
        self.assertEqual("DPAE_UNCONFIRMED_RETURN_EFFECT", ctx.exception.code)


if __name__ == "__main__":
    unittest.main()
