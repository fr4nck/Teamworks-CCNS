from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from domain.contracts.contract import Contract
from domain.engine.anomaly import Anomaly
from domain.engine.anomaly_level import AnomalyLevel
from domain.engine.calculation_result import CalculationResult
from domain.engine.detailed_checks import _extract_group_number
from domain.engine.legal_certainty import LegalCertainty
from domain.engine.result_status import ResultStatus


SENIORITY_REFERENCE_CODE = "REF_CCNS_SENIORITY_G1_G6_2026"
SENIORITY_LEGAL_CERTAINTY = LegalCertainty.MAJORITAIRE


def check_ccns_seniority_amount(
    contract: Contract,
    reference_date: date,
    smc_group_3_amount: float,
    actual_seniority_amount: float,
) -> tuple[CalculationResult, Optional[Anomaly]]:
    """Contrôle la prime d'ancienneté standard CCNS déjà utilisée par l'audit.

    Règle couverte par la documentation existante : groupes 1 à 6, palier de
    3 % tous les 2 ans, plafond à 15 %, sur base SMC groupe 3. Les cas plus
    détaillés restent hors périmètre de ce contrôle historique.
    """
    group_number = _extract_group_number(contract.ccns_classification_code or "")
    start_date = _as_date(contract.start_date)
    actual_amount = float(actual_seniority_amount or 0.0)

    if group_number is None or start_date is None:
        result = _result(
            contract=contract,
            reference_date=reference_date,
            theoretical_amount=0.0,
            actual_amount=actual_amount,
            status=ResultStatus.NOT_APPLICABLE,
            message="Prime d'ancienneté non calculable",
            details={"group_number": group_number, "start_date": start_date},
        )
        return result, None

    applies = 1 <= group_number <= 6
    if not applies:
        result = _result(
            contract=contract,
            reference_date=reference_date,
            theoretical_amount=0.0,
            actual_amount=actual_amount,
            status=ResultStatus.COMPLIANT if actual_amount <= 0 else ResultStatus.WARNING,
            message="Prime d'ancienneté non applicable",
            details={"group_number": group_number, "rate": 0.0},
        )
        if actual_amount > 0:
            return result, _anomaly(contract, result, "ANCIENNETE_APPLIQUEE_A_TORT", "Une prime d'ancienneté est saisie alors que la règle standard ne s'applique pas.", reference_date)
        return result, None

    completed_years = _completed_years(start_date, reference_date)
    rate = min((completed_years // 2) * 0.03, 0.15)
    theoretical_amount = round(float(smc_group_3_amount or 0.0) * rate, 2)
    compliant = actual_amount + 0.005 >= theoretical_amount
    result = _result(
        contract=contract,
        reference_date=reference_date,
        theoretical_amount=theoretical_amount,
        actual_amount=actual_amount,
        status=ResultStatus.COMPLIANT if compliant else ResultStatus.WARNING,
        message="Prime d'ancienneté conforme" if compliant else "Prime d'ancienneté inférieure au théorique",
        details={"group_number": group_number, "completed_years": completed_years, "rate": rate},
    )
    if compliant:
        return result, None
    code = "ANCIENNETE_OUBLIEE" if actual_amount <= 0 else "ANCIENNETE_INFERIEURE_THEORIQUE"
    message = "La prime d'ancienneté attendue est absente." if actual_amount <= 0 else "La prime d'ancienneté saisie est inférieure au montant théorique."
    return result, _anomaly(contract, result, code, message, reference_date)


def _result(contract, reference_date, theoretical_amount, actual_amount, status, message, details):
    return CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="CCNS_SENIORITY_AMOUNT",
        rule_reference_code=SENIORITY_REFERENCE_CODE,
        legal_certainty=SENIORITY_LEGAL_CERTAINTY,
        calculation_date=reference_date,
        retained_base="smc_group_3",
        actual_value=actual_amount,
        theoretical_value=theoretical_amount,
        gap=round(actual_amount - theoretical_amount, 2),
        status=status,
        readable_message=message,
        details=details,
    )


def _anomaly(contract, result, code, message, reference_date):
    return Anomaly(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        calculation_result_id=result.id,
        level=AnomalyLevel.ATTENTION,
        code=code,
        message=message,
        detection_date=reference_date,
    )


def _as_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _completed_years(start_date: date, reference_date: date) -> int:
    years = reference_date.year - start_date.year
    if (reference_date.month, reference_date.day) < (start_date.month, start_date.day):
        years -= 1
    return max(years, 0)
