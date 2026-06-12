from infrastructure.repositories.base import InMemoryRepository
from domain.contracts.contract import Contract


class ContractRepository(InMemoryRepository[Contract]):
    def list_by_person_id(self, person_id: str) -> list[Contract]:
        return [item for item in self.list_all() if item.person_id == person_id]
