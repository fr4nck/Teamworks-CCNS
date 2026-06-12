from infrastructure.repositories.base import InMemoryRepository
from domain.engine.calculation_rule import CalculationRule
from domain.engine.calculation_result import CalculationResult
from domain.engine.anomaly import Anomaly
from domain.engine.individual_counter import IndividualCounter


class CalculationRuleRepository(InMemoryRepository[CalculationRule]):
    def list_active(self) -> list[CalculationRule]:
        return [item for item in self.list_all() if item.is_active]


class CalculationResultRepository(InMemoryRepository[CalculationResult]):
    def list_by_contract_id(self, contract_id: str) -> list[CalculationResult]:
        return [item for item in self.list_all() if item.contract_id == contract_id]

    def list_by_assignment_id(self, assignment_id: str) -> list[CalculationResult]:
        return [item for item in self.list_all() if item.assignment_id == assignment_id]


class AnomalyRepository(InMemoryRepository[Anomaly]):
    def list_active(self) -> list[Anomaly]:
        return [item for item in self.list_all() if not item.resolved]

    def list_by_contract_id(self, contract_id: str) -> list[Anomaly]:
        return [item for item in self.list_all() if item.contract_id == contract_id]

    def list_by_assignment_id(self, assignment_id: str) -> list[Anomaly]:
        return [item for item in self.list_all() if item.assignment_id == assignment_id]


class IndividualCounterRepository(InMemoryRepository[IndividualCounter]):
    def list_by_person_id(self, person_id: str) -> list[IndividualCounter]:
        return [item for item in self.list_all() if item.person_id == person_id]
