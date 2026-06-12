from __future__ import annotations

from datetime import date
from typing import Optional

from domain.contracts.contract import Contract
from domain.engine.anomaly import Anomaly
from domain.engine.anomaly_level import AnomalyLevel
from domain.engine.calculation_result import CalculationResult
from domain.engine.result_status import ResultStatus


def check_contract_has_classification(contract: Contract) -> tuple[CalculationResult, Optional[Anomaly]]:
    ok = bool(contract.ccns_classification_code)
    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="CONTRACT_HAS_CLASSIFICATION",
        calculation_date=date.today(),
        status=ResultStatus.COMPLIANT if ok else ResultStatus.DATA_ERROR,
        readable_message="Classification conventionnelle présente" if ok else "Classification conventionnelle manquante",
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
        code="CONTRAT_SANS_CLASSIFICATION",
        message="La classification conventionnelle du contrat est manquante.",
        detection_date=date.today(),
    )
    return result, anomaly


def check_contract_has_salary_grid(contract: Contract) -> tuple[CalculationResult, Optional[Anomaly]]:
    ok = bool(contract.salary_grid_code)
    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="CONTRACT_HAS_SALARY_GRID",
        calculation_date=date.today(),
        status=ResultStatus.COMPLIANT if ok else ResultStatus.DATA_ERROR,
        readable_message="Grille salariale présente" if ok else "Grille salariale manquante",
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
        code="CONTRAT_SANS_GRILLE",
        message="Aucune grille salariale n'est renseignée pour ce contrat.",
        detection_date=date.today(),
    )
    return result, anomaly
