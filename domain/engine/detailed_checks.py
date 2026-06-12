from __future__ import annotations

from datetime import date
from typing import Optional

from domain.contracts.contract import Contract
from domain.engine.anomaly import Anomaly
from domain.engine.anomaly_level import AnomalyLevel
from domain.engine.calculation_result import CalculationResult
from domain.engine.result_status import ResultStatus


def _today() -> date:
    return date.today()


def check_short_part_time_majoration(contract: Contract) -> tuple[CalculationResult, Optional[Anomaly]]:
    hours = contract.weekly_reference_hours
    if hours is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="SHORT_PART_TIME_MAJO",
            calculation_date=_today(),
            status=ResultStatus.NOT_APPLICABLE,
            readable_message="Durée hebdomadaire absente, contrôle temps partiel court non applicable",
        )
        return result, None

    if hours <= 10:
        coefficient = 1.05
        message = "Majoration temps partiel court palier ≤ 10 h"
    elif hours < 24:
        coefficient = 1.02
        message = "Majoration temps partiel court palier > 10 h et < 24 h"
    else:
        coefficient = 1.00
        message = "Pas de majoration temps partiel court"

    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="SHORT_PART_TIME_MAJO",
        calculation_date=_today(),
        retained_base="weekly_reference_hours",
        actual_value=hours,
        theoretical_value=coefficient,
        retained_coefficient=coefficient,
        gap=0.0,
        status=ResultStatus.INFO,
        readable_message=message,
        details={"weekly_reference_hours": hours, "multiplier": coefficient},
    )
    return result, None


def check_seniority_applicability(contract: Contract) -> tuple[CalculationResult, Optional[Anomaly]]:
    classification_code = contract.ccns_classification_code
    if not classification_code:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="SENIORITY_APPLICABILITY",
            calculation_date=_today(),
            status=ResultStatus.DATA_ERROR,
            readable_message="Classification absente, contrôle ancienneté impossible",
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.BLOCKING,
            code="CONTRAT_SANS_CLASSIFICATION",
            message="La classification conventionnelle du contrat est manquante.",
            detection_date=_today(),
        )
        return result, anomaly

    group_number = _extract_group_number(classification_code)
    if group_number is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="SENIORITY_APPLICABILITY",
            calculation_date=_today(),
            status=ResultStatus.DATA_ERROR,
            readable_message="Classification non interprétable pour le contrôle ancienneté",
            details={"classification_code": classification_code},
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.ATTENTION,
            code="CLASSIFICATION_NON_INTERPRETABLE",
            message="La classification du contrat ne permet pas de déterminer la règle d'ancienneté.",
            detection_date=_today(),
        )
        return result, anomaly

    applies = 1 <= group_number <= 6
    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="SENIORITY_APPLICABILITY",
        calculation_date=_today(),
        retained_base="classification_group",
        actual_value=float(group_number),
        theoretical_value=1.0 if applies else 0.0,
        retained_coefficient=1.0 if applies else 0.0,
        gap=0.0,
        status=ResultStatus.INFO,
        readable_message="Prime d'ancienneté standard applicable" if applies else "Prime d'ancienneté standard non applicable",
        details={"classification_code": classification_code, "group_number": group_number},
    )
    return result, None


def check_cee_max_days(days_rolling_12_months: int, contract: Contract) -> tuple[CalculationResult, Optional[Anomaly]]:
    limit = 80
    ok = days_rolling_12_months <= limit
    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="CEE_MAX_80J",
        calculation_date=_today(),
        retained_base="rolling_12_month_days",
        actual_value=float(days_rolling_12_months),
        theoretical_value=float(limit),
        retained_coefficient=1.0,
        gap=float(days_rolling_12_months - limit),
        status=ResultStatus.COMPLIANT if ok else ResultStatus.WARNING,
        readable_message="Plafond CEE respecté" if ok else "Plafond CEE dépassé",
        details={"days_rolling_12_months": days_rolling_12_months, "limit": limit},
    )
    if ok:
        return result, None

    anomaly = Anomaly(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        calculation_result_id=result.id,
        level=AnomalyLevel.BLOCKING,
        code="CEE_DEPASSEMENT_80_JOURS",
        message="Le seuil de 80 jours en CEE sur 12 mois glissants est dépassé.",
        detection_date=_today(),
        details={"days_rolling_12_months": days_rolling_12_months, "limit": limit},
    )
    return result, anomaly


def check_apprenticeship_bar_scale(age: int, execution_year: int, contract: Contract) -> tuple[CalculationResult, Optional[Anomaly]]:
    percent = _apprenticeship_percent(age=age, execution_year=execution_year)
    if percent is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="APPRENTICESHIP_SCALE",
            calculation_date=_today(),
            status=ResultStatus.DATA_ERROR,
            readable_message="Barème apprentissage introuvable",
            details={"age": age, "execution_year": execution_year},
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.ATTENTION,
            code="REGLE_INTROUVABLE",
            message="Aucun barème apprentissage n'a été trouvé pour cet âge et cette année d'exécution.",
            detection_date=_today(),
            details={"age": age, "execution_year": execution_year},
        )
        return result, anomaly

    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="APPRENTICESHIP_SCALE",
        calculation_date=_today(),
        retained_base="age_and_execution_year",
        actual_value=float(age),
        theoretical_value=float(percent),
        retained_coefficient=percent / 100.0,
        gap=0.0,
        status=ResultStatus.INFO,
        readable_message=f"Barème apprentissage trouvé : {percent} %",
        details={"age": age, "execution_year": execution_year, "percent": percent},
    )
    return result, None


def _extract_group_number(classification_code: str) -> Optional[int]:
    digits = "".join(ch for ch in classification_code if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _apprenticeship_percent(age: int, execution_year: int) -> Optional[int]:
    if execution_year not in (1, 2, 3):
        return None

    if 16 <= age <= 17:
        return {1: 27, 2: 39, 3: 55}.get(execution_year)
    if 18 <= age <= 20:
        return {1: 43, 2: 51, 3: 67}.get(execution_year)
    if 21 <= age <= 25:
        return {1: 53, 2: 61, 3: 78}.get(execution_year)
    if age >= 26:
        return 100
    return None
