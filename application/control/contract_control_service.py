from __future__ import annotations

from domain.contracts.contract import Contract
from domain.engine.anomaly import Anomaly
from domain.engine.calculation_result import CalculationResult
from application.control.models import ContractControlView


class ContractControlService:
    def build_view(
        self,
        *,
        contract: Contract,
        calculation_results: list[CalculationResult],
        anomalies: list[Anomaly],
    ) -> ContractControlView:
        contract_results = [r for r in calculation_results if r.contract_id == contract.id]
        contract_anomalies = [a for a in anomalies if a.contract_id == contract.id and not a.resolved]

        return ContractControlView(
            contract_id=contract.id,
            person_id=contract.person_id,
            classification_code=contract.ccns_classification_code,
            salary_grid_code=contract.salary_grid_code,
            base_salary_amount=contract.base_salary_amount,
            salary_unit=contract.salary_unit,
            result_messages=[r.readable_message for r in contract_results],
            anomaly_codes=[a.code for a in contract_anomalies],
        )
