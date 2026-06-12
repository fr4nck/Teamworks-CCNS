from infrastructure.repositories.base import InMemoryRepository
from domain.people.person import Person
from domain.people.legal_profile import LegalProfile


class PeopleRepository(InMemoryRepository[Person]):
    pass


class LegalProfileRepository(InMemoryRepository[LegalProfile]):
    def get_by_person_id(self, person_id: str) -> LegalProfile | None:
        for item in self.list_all():
            if item.person_id == person_id:
                return item
        return None
