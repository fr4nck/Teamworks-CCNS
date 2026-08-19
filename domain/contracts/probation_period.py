from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from enum import Enum

from domain.contracts.contract_operation import ContractOperation
from domain.contracts.contract_type import ContractType


class ProbationUnit(str, Enum):
    DAY = "DAY"
    MONTH = "MONTH"


@dataclass(frozen=True, slots=True)
class ProbationPeriodProposal:
    value: int
    unit: ProbationUnit
    automatic: bool
    reason: str

    def is_zero(self) -> bool:
        return self.value == 0


def _add_calendar_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _inclusive_days(start_date: date, end_date: date) -> int:
    if end_date < start_date:
        raise ValueError("La date de fin ne peut pas précéder la date de début.")
    return (end_date - start_date).days + 1


def probation_calendar_days(*, start_date: date, value: int, unit: ProbationUnit) -> int:
    """Convertit une durée structurée en jours calendaires pour le champ legacy.

    Le champ historique ``essai`` de Teamworks est un entier en jours. La
    conversion des mois dépend donc de la date réelle de début ; elle ne doit
    jamais être remplacée par une approximation fixe de 30 jours.
    """
    if type(start_date) is not date:
        raise TypeError("start_date doit être une date stricte.")
    if type(value) is not int or value < 0:
        raise ValueError("value doit être un entier positif ou nul.")
    if unit is ProbationUnit.DAY:
        return value
    if unit is ProbationUnit.MONTH:
        return (_add_calendar_months(start_date, value) - start_date).days
    raise ValueError("Unité de période d'essai inconnue.")


def _ccns_cdi_months(group_code: str) -> int:
    code = (group_code or "").strip().upper()
    if code in ("G1", "G2"):
        return 1
    if code in ("G3", "G4", "G5"):
        return 2
    if code in ("G6", "G7", "G8"):
        return 3
    raise ValueError("Groupe CCNS requis pour calculer la période d'essai du CDI.")


def propose_ccns_probation_period(
    *,
    contract_type: ContractType,
    operation: ContractOperation,
    start_date: date,
    end_date: date | None = None,
    ccns_group: str | None = None,
    previous_contract_start: date | None = None,
    previous_contract_end: date | None = None,
) -> ProbationPeriodProposal:
    """Propose la période d'essai maximale applicable au parcours CCNS.

    Le résultat reste une proposition : la période d'essai n'est jamais
    obligatoire et doit être stipulée au contrat. Les règles automatiques sont
    volontairement limitées aux cas juridiquement déterministes raccordés ici.
    """

    if type(start_date) is not date:
        raise TypeError("start_date doit être une date stricte.")

    if contract_type is ContractType.CEE:
        return ProbationPeriodProposal(
            value=0,
            unit=ProbationUnit.DAY,
            automatic=True,
            reason="Le CEE n'utilise pas le moteur de période d'essai CDI/CDD.",
        )

    if operation is ContractOperation.CDD_RENEWAL:
        if contract_type is not ContractType.CDD:
            raise ValueError("Un renouvellement CDD doit produire un CDD.")
        return ProbationPeriodProposal(
            value=0,
            unit=ProbationUnit.DAY,
            automatic=True,
            reason="Renouvellement du CDD : aucune nouvelle période d'essai.",
        )

    if operation is ContractOperation.CDD_TO_CDI:
        if contract_type is not ContractType.CDI:
            raise ValueError("Une poursuite CDD vers CDI doit produire un CDI.")
        if previous_contract_start is None or previous_contract_end is None:
            raise ValueError("Le CDD précédent est requis pour déduire sa durée de la période d'essai CDI.")
        theoretical_months = _ccns_cdi_months(ccns_group or "")
        theoretical_end_exclusive = _add_calendar_months(start_date, theoretical_months)
        theoretical_days = (theoretical_end_exclusive - start_date).days
        previous_days = _inclusive_days(previous_contract_start, previous_contract_end)
        remaining_days = max(0, theoretical_days - previous_days)
        return ProbationPeriodProposal(
            value=remaining_days,
            unit=ProbationUnit.DAY,
            automatic=True,
            reason=(
                "CDD vers CDI : durée du CDD précédent déduite de la période d'essai CDI théorique."
            ),
        )

    if operation is not ContractOperation.NEW:
        raise ValueError("Nature d'opération non prise en charge.")

    if contract_type is ContractType.CDI:
        return ProbationPeriodProposal(
            value=_ccns_cdi_months(ccns_group or ""),
            unit=ProbationUnit.MONTH,
            automatic=True,
            reason="CDI CCNS : durée proposée selon la catégorie correspondant au groupe.",
        )

    if contract_type is ContractType.CDD:
        if end_date is None:
            return ProbationPeriodProposal(
                value=0,
                unit=ProbationUnit.DAY,
                automatic=False,
                reason="CDD sans terme exploitable : durée minimale du contrat requise pour calculer l'essai.",
            )
        duration_days = _inclusive_days(start_date, end_date)
        # Une semaine entamée est comptée comme une semaine pour proposer le
        # plafond d'un jour par semaine ; le plafond légal reste prioritaire.
        weeks = max(1, (duration_days + 6) // 7)
        six_month_limit = _add_calendar_months(start_date, 6)
        if end_date < six_month_limit:
            return ProbationPeriodProposal(
                value=min(14, weeks),
                unit=ProbationUnit.DAY,
                automatic=True,
                reason="CDD de six mois au plus : un jour par semaine, plafonné à deux semaines.",
            )
        return ProbationPeriodProposal(
            value=1,
            unit=ProbationUnit.MONTH,
            automatic=True,
            reason="CDD de plus de six mois : période d'essai plafonnée à un mois.",
        )

    return ProbationPeriodProposal(
        value=0,
        unit=ProbationUnit.DAY,
        automatic=False,
        reason="Type de contrat non encore raccordé au moteur de période d'essai.",
    )
