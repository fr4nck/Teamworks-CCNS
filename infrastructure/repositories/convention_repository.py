from infrastructure.repositories.base import InMemoryRepository
from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine


class ClassificationRepository(InMemoryRepository[CCNSClassification]):
    def get_by_code(self, code: str) -> CCNSClassification | None:
        for item in self.list_all():
            if item.code == code:
                return item
        return None


class SalaryGridRepository(InMemoryRepository[SalaryGrid]):
    def get_by_code(self, code: str) -> SalaryGrid | None:
        for item in self.list_all():
            if item.code == code:
                return item
        return None


class SalaryGridLineRepository(InMemoryRepository[SalaryGridLine]):
    def list_by_grid_id(self, salary_grid_id: str) -> list[SalaryGridLine]:
        return [item for item in self.list_all() if item.salary_grid_id == salary_grid_id]
