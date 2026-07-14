from __future__ import annotations

from datetime import date
from typing import Iterable, Optional

from domain.contracts.contract import Contract
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine
from domain.convention.minimum_resolver import (
    resolve_minimum_line,
    compute_contract_theoretical_minimum,
)
from domain.engine.anomaly import Anomaly
from domain.engine.anomaly_level import AnomalyLevel
from domain.engine.calculation_result import CalculationResult
from domain.engine.legal_certainty import LegalCertainty
from domain.engine.result_status import ResultStatus

MINIMUM_FROM_GRID_REFERENCE_CODE = "REF_CCNS_MIN_G1_G6_MONTHLY_2026"
MINIMUM_FROM_GRID_LEGAL_CERTAINTY = LegalCertainty.CERTAINE


def check_contract_minimum_from_grid(
    *,
    contract: Contract,
    salary_grid: Optional[SalaryGrid],
    salary_grid_lines: Iterable[SalaryGridLine],
    age: Optional[int] = None,
    execution_year: Optional[int] = None,
    reference_date: Optional[date] = None,
) -> tuple[CalculationResult, Optional[Anomaly]]:
    control_date = reference_date or date.today()
    if not contract.ccns_classification_code:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="MINIMUM_FROM_GRID",
            rule_reference_code=MINIMUM_FROM_GRID_REFERENCE_CODE,
            legal_certainty=MINIMUM_FROM_GRID_LEGAL_CERTAINTY,
            calculation_date=control_date,
            status=ResultStatus.DATA_ERROR,
            readable_message="Classification absente, calcul du minimum impossible",
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
            detection_date=control_date,
        )
        return result, anomaly

    if salary_grid is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="MINIMUM_FROM_GRID",
            rule_reference_code=MINIMUM_FROM_GRID_REFERENCE_CODE,
            legal_certainty=MINIMUM_FROM_GRID_LEGAL_CERTAINTY,
            calculation_date=control_date,
            status=ResultStatus.DATA_ERROR,
            readable_message="Grille salariale absente, calcul du minimum impossible",
            details={"classification_code": contract.ccns_classification_code},
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.BLOCKING,
            code="CONTRAT_SANS_GRILLE",
            message="Aucune grille salariale n'est renseignée pour ce contrat.",
            detection_date=control_date,
        )
        return result, anomaly

    line = resolve_minimum_line(
        salary_grid=salary_grid,
        salary_grid_lines=salary_grid_lines,
        classification_code=contract.ccns_classification_code,
        age=age,
        execution_year=execution_year,
    )

    if line is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="MINIMUM_FROM_GRID",
            rule_reference_code=MINIMUM_FROM_GRID_REFERENCE_CODE,
            legal_certainty=MINIMUM_FROM_GRID_LEGAL_CERTAINTY,
            calculation_date=control_date,
            status=ResultStatus.DATA_ERROR,
            readable_message="Aucune ligne de grille applicable n'a été trouvée",
            details={
                "classification_code": contract.ccns_classification_code,
                "salary_grid_code": salary_grid.code,
            },
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.BLOCKING,
            code="REGLE_INTROUVABLE",
            message="Aucune ligne de grille applicable n'a été trouvée pour ce contrat.",
            detection_date=control_date,
        )
        return result, anomaly

    theoretical_minimum = compute_contract_theoretical_minimum(
        line=line,
        weekly_reference_hours=contract.weekly_reference_hours,
        work_ratio=contract.work_ratio,
    )

    if theoretical_minimum is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="MINIMUM_FROM_GRID",
            rule_reference_code=MINIMUM_FROM_GRID_REFERENCE_CODE,
            legal_certainty=MINIMUM_FROM_GRID_LEGAL_CERTAINTY,
            calculation_date=control_date,
            status=ResultStatus.DATA_ERROR,
            readable_message="Le minimum théorique n'a pas pu être calculé à partir de la grille",
            details={
                "classification_code": contract.ccns_classification_code,
                "salary_grid_code": salary_grid.code,
                "line_id": line.id,
            },
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.ATTENTION,
            code="MINIMUM_THEORIQUE_NON_CALCULABLE",
            message="Le minimum théorique n'a pas pu être calculé à partir de la ligne de grille.",
            detection_date=control_date,
        )
        return result, anomaly

    actual_salary = contract.base_salary_amount
    if actual_salary is None:
        result = CalculationResult(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            rule_code="MINIMUM_FROM_GRID",
            rule_reference_code=MINIMUM_FROM_GRID_REFERENCE_CODE,
            legal_certainty=MINIMUM_FROM_GRID_LEGAL_CERTAINTY,
            calculation_date=control_date,
            retained_base=line.minimum_type.value,
            actual_value=None,
            theoretical_value=theoretical_minimum,
            retained_coefficient=contract.work_ratio if contract.work_ratio is not None else 1.0,
            gap=None,
            status=ResultStatus.DATA_ERROR,
            readable_message="Rémunération de base absente, comparaison impossible",
            details={"salary_grid_code": salary_grid.code, "line_id": line.id},
        )
        anomaly = Anomaly(
            object_type="contract",
            object_id=contract.id,
            person_id=contract.person_id,
            contract_id=contract.id,
            calculation_result_id=result.id,
            level=AnomalyLevel.ATTENTION,
            code="REMUNERATION_BASE_ABSENTE",
            message="La rémunération de base du contrat est absente.",
            detection_date=control_date,
        )
        return result, anomaly

    gap = round(actual_salary - theoretical_minimum, 2)
    ok = gap >= 0

    result = CalculationResult(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        rule_code="MINIMUM_FROM_GRID",
        rule_reference_code=MINIMUM_FROM_GRID_REFERENCE_CODE,
        legal_certainty=MINIMUM_FROM_GRID_LEGAL_CERTAINTY,
        calculation_date=control_date,
        retained_base=line.minimum_type.value,
        actual_value=actual_salary,
        theoretical_value=theoretical_minimum,
        retained_coefficient=contract.work_ratio if contract.work_ratio is not None else 1.0,
        gap=gap,
        status=ResultStatus.COMPLIANT if ok else ResultStatus.WARNING,
        readable_message="Rémunération conforme à la grille" if ok else "Rémunération inférieure au minimum de grille",
        details={
            "salary_grid_code": salary_grid.code,
            "salary_grid_line_id": line.id,
            "classification_code": contract.ccns_classification_code,
        },
    )

    if ok:
        return result, None

    anomaly = Anomaly(
        object_type="contract",
        object_id=contract.id,
        person_id=contract.person_id,
        contract_id=contract.id,
        calculation_result_id=result.id,
        level=AnomalyLevel.ATTENTION,
        code="MINIMUM_CCNS_NON_ATTEINT",
        message="La rémunération saisie est inférieure au minimum conventionnel calculé.",
        detection_date=control_date,
        details={
            "actual_salary": actual_salary,
            "theoretical_minimum": theoretical_minimum,
            "gap": gap,
        },
    )
    return result, anomaly
