from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from application.control.contract_compensation_preflight import ContractCompensationPreflight
from domain.contracts.contract_rules_preflight import (
    CCNSContractRulesPreflightService,
    ContractRulesPreflightResult,
)
from domain.convention.seniority import CCNSSeniorityService
from domain.convention.seniority_timeline import CCNSContractSeniorityTimelineService


_FULL_TIME_WEEKLY_HOURS = Decimal("35.00")


def build_ccns_creation_rules_preflight(
    *,
    group_code: str,
    reference_date: date,
    current_contract_start: date,
    evaluation_date: date,
    weekly_hours: Decimal,
    compensation: ContractCompensationPreflight,
    current_contract_end: Optional[date] = None,
    recognized_effective_work_months_at_start: Optional[int] = None,
    recognized_company_seniority_months_at_start: Optional[int] = None,
    excluded_current_contract_effective_months: int = 0,
    history_known_absent: bool = False,
) -> ContractRulesPreflightResult:
    """Construit le préflight CCNS utilisable par l'assistant historique.

    Le bridge reste sans dépendance wx/SQL. La couche Teamworks peut fournir une
    ancienneté reconnue issue d'une chaîne explicite de contrats, ou indiquer
    qu'aucun historique antérieur n'existe. En l'absence de ces informations,
    le moteur calcule l'ancienneté minimale connue sur le contrat courant et
    demande une revue au lieu d'inventer un historique nul.
    """
    if type(group_code) is not str or not group_code.strip():
        raise ValueError("group_code est obligatoire.")
    if type(reference_date) is not date:
        raise TypeError("reference_date doit être une date stricte.")
    if type(current_contract_start) is not date:
        raise TypeError("current_contract_start doit être une date stricte.")
    if type(evaluation_date) is not date:
        raise TypeError("evaluation_date doit être une date stricte.")
    if type(weekly_hours) is not Decimal:
        raise TypeError("weekly_hours doit être un Decimal strict.")
    if weekly_hours <= Decimal("0.00"):
        raise ValueError("weekly_hours doit être strictement positif.")
    if type(compensation) is not ContractCompensationPreflight:
        raise TypeError("compensation doit être un ContractCompensationPreflight.")
    if type(history_known_absent) is not bool:
        raise TypeError("history_known_absent doit être un booléen strict.")

    if history_known_absent:
        if recognized_effective_work_months_at_start is None:
            recognized_effective_work_months_at_start = 0
        if recognized_company_seniority_months_at_start is None:
            recognized_company_seniority_months_at_start = 0

    timeline = CCNSContractSeniorityTimelineService().evaluate(
        current_contract_start=current_contract_start,
        evaluation_date=evaluation_date,
        current_contract_end=current_contract_end,
        recognized_effective_work_months_at_start=recognized_effective_work_months_at_start,
        recognized_company_seniority_months_at_start=recognized_company_seniority_months_at_start,
        excluded_current_contract_effective_months=excluded_current_contract_effective_months,
    )

    choices = CCNSContractCompliancePresenter().group_choices(reference_date)
    group3 = next((choice for choice in choices if choice.code == "G3"), None)
    if group3 is None:
        raise ValueError("Le SMC du groupe 3 est introuvable pour la date de référence.")

    work_ratio = min(weekly_hours, _FULL_TIME_WEEKLY_HOURS) / _FULL_TIME_WEEKLY_HOURS
    seniority = CCNSSeniorityService().evaluate(
        group_code=group_code,
        effective_work_months=timeline.effective_work_months,
        company_seniority_months=timeline.company_seniority_months,
        smc_group3_monthly_amount=group3.minimum_amount,
        work_ratio=work_ratio,
    )

    return CCNSContractRulesPreflightService().evaluate(
        seniority_timeline=timeline,
        seniority=seniority,
        mentions=None,
        mentions_check_required=False,
        compensation_compliant=compensation.compliant,
        compensation_message=compensation.message,
    )
