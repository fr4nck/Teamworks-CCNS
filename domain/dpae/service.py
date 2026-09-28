"""Service métier de corrélation des retours DPAE."""
from __future__ import annotations

from datetime import datetime

from .model import DpaeCorrelationDecision, DpaeReturnEffect
from .repository import InMemoryDpaeRepository


class DpaeCorrelationService:
    def __init__(self, repository: InMemoryDpaeRepository) -> None:
        self.repository = repository

    def confirm(
        self,
        *,
        return_id: str,
        submission_id: str,
        case_id: str,
        expected_version: int,
        actor_id: str,
        decision_id: str,
        decided_at: datetime,
    ) -> str:
        result = self.repository.confirm_correlation(
            return_id, submission_id, case_id, expected_version
        )
        if result == "CONFIRMED":
            self.repository.append_decision(
                DpaeCorrelationDecision(
                    id=decision_id,
                    return_id=return_id,
                    action="CONFIRM_MATCH",
                    actor_id=actor_id,
                    decided_at=decided_at,
                    candidate_submission_id=submission_id,
                )
            )
        return result

    def apply_effect_once(
        self, *, return_id: str, effect_type: str, created_at: datetime
    ) -> bool:
        return self.repository.record_effect_once(
            DpaeReturnEffect(return_id, effect_type, created_at)
        )
