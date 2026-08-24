from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from domain.convention.part_time_working_time import CCNSPartTimeWorkingTimeService


CCNS_PART_TIME_MODULATION_SOURCE = "CCNS, article 5.2.4"
CODE_PART_TIME_FULL_TIME_THRESHOLD_SOURCE = "Code du travail, article L.3123-9"
CCNS_WEEKLY_MAXIMUM_SOURCE = "CCNS, article 5.1.3"
CCNS_COMPLEMENTARY_HOURS_SOURCE = "CCNS, article 5.1.5 — Heures complémentaires"

_ZERO = Decimal("0.00")
_LEGAL_WEEKLY_DURATION = Decimal("35.00")
_ABSOLUTE_WEEKLY_MAXIMUM = Decimal("48.00")


class PartTimePlannedWeekStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    COMPLEMENTARY_HOURS_LIMIT_EXCEEDED = "COMPLEMENTARY_HOURS_LIMIT_EXCEEDED"
    FULL_TIME_THRESHOLD_REACHED = "FULL_TIME_THRESHOLD_REACHED"
    ABSOLUTE_WEEKLY_MAXIMUM_EXCEEDED = "ABSOLUTE_WEEKLY_MAXIMUM_EXCEEDED"


@dataclass(frozen=True, slots=True)
class PartTimePlannedWeekResult:
    contractual_weekly_hours: Decimal
    planned_weekly_hours: Decimal
    status: PartTimePlannedWeekStatus
    compliant: bool
    recording_allowed: bool
    manual_override_used: bool
    manual_override_reason: str
    can_be_marked_compliant: bool
    source_references: tuple[str, ...]

    @property
    def requires_manual_override(self) -> bool:
        return not self.compliant

    @property
    def exceeds_or_reaches_full_time(self) -> bool:
        return self.planned_weekly_hours >= _LEGAL_WEEKLY_DURATION


class CCNSPartTimePlannedWeekService:
    """Contrôle une semaine planifiée sans empêcher la saisie de la réalité.

    Une non-conformité peut être enregistrée avec un motif explicite. Ce motif
    n'efface jamais le statut réglementaire : il autorise seulement la saisie
    du planning réel ou d'un scénario à auditer.
    """

    def __init__(self, base_service: CCNSPartTimeWorkingTimeService | None = None) -> None:
        self._base_service = base_service or CCNSPartTimeWorkingTimeService()

    def evaluate(
        self,
        *,
        contractual_weekly_hours: Decimal,
        planned_weekly_hours: Decimal,
        manual_override_reason: str = "",
    ) -> PartTimePlannedWeekResult:
        if type(contractual_weekly_hours) is not Decimal:
            raise TypeError("contractual_weekly_hours doit être un Decimal strict.")
        if type(planned_weekly_hours) is not Decimal:
            raise TypeError("planned_weekly_hours doit être un Decimal strict.")
        if type(manual_override_reason) is not str:
            raise TypeError("manual_override_reason doit être une chaîne.")
        if not _ZERO < contractual_weekly_hours < _LEGAL_WEEKLY_DURATION:
            raise ValueError("contractual_weekly_hours doit être > 0 et < 35 heures.")
        if planned_weekly_hours <= _ZERO:
            raise ValueError("planned_weekly_hours doit être strictement positif.")

        reason = manual_override_reason.strip()
        if planned_weekly_hours > _ABSOLUTE_WEEKLY_MAXIMUM:
            status = PartTimePlannedWeekStatus.ABSOLUTE_WEEKLY_MAXIMUM_EXCEEDED
            sources = (CCNS_WEEKLY_MAXIMUM_SOURCE, CCNS_PART_TIME_MODULATION_SOURCE)
        elif planned_weekly_hours >= _LEGAL_WEEKLY_DURATION:
            status = PartTimePlannedWeekStatus.FULL_TIME_THRESHOLD_REACHED
            sources = (CCNS_PART_TIME_MODULATION_SOURCE, CODE_PART_TIME_FULL_TIME_THRESHOLD_SOURCE)
        elif planned_weekly_hours > contractual_weekly_hours:
            complementary = self._base_service.evaluate_complementary_hours(
                contractual_weekly_hours=contractual_weekly_hours,
                complementary_hours=planned_weekly_hours - contractual_weekly_hours,
            )
            if complementary.compliant:
                status = PartTimePlannedWeekStatus.COMPLIANT
            else:
                status = PartTimePlannedWeekStatus.COMPLEMENTARY_HOURS_LIMIT_EXCEEDED
            sources = (CCNS_COMPLEMENTARY_HOURS_SOURCE,)
        else:
            status = PartTimePlannedWeekStatus.COMPLIANT
            sources = (CCNS_PART_TIME_MODULATION_SOURCE,)

        compliant = status is PartTimePlannedWeekStatus.COMPLIANT
        override_used = (not compliant) and bool(reason)
        return PartTimePlannedWeekResult(
            contractual_weekly_hours=contractual_weekly_hours,
            planned_weekly_hours=planned_weekly_hours,
            status=status,
            compliant=compliant,
            recording_allowed=compliant or override_used,
            manual_override_used=override_used,
            manual_override_reason=reason,
            can_be_marked_compliant=compliant,
            source_references=sources,
        )
