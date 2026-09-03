from __future__ import annotations

from typing import Sequence

from data_adapter import ContractView, PersonView, TeamworksReadAdapter
from domain.people.person import Person


class DomainPeopleReadAdapter(TeamworksReadAdapter):
    """Adaptateur lecture seule branché sur le domaine Teamworks actuel.

    Il accepte un repository exposant list_all(). Aucun import wxPython et aucune
    requête SQL ne sont autorisés ici. Les champs non encore portés par le domaine
    restent explicitement neutres au lieu d'être inventés.
    """

    def __init__(self, people_repository, contracts_reader=None):
        self._people_repository = people_repository
        self._contracts_reader = contracts_reader

    def list_people(self) -> Sequence[PersonView]:
        return tuple(self._person_to_view(person) for person in self._people_repository.list_all())

    def list_contracts(self, person_id: str) -> Sequence[ContractView]:
        if self._contracts_reader is None:
            return ()
        rows = self._contracts_reader(person_id)
        return tuple(rows)

    @staticmethod
    def _person_to_view(person: Person) -> PersonView:
        return PersonView(
            id=person.id,
            name=person.display_name,
            role="",
            classification="",
            contract="",
            weekly_hours="",
            status="Actif" if person.is_active else "Inactif",
            site="",
            medical="",
            mutual="",
        )


def build_domain_smoke_adapter() -> DomainPeopleReadAdapter:
    """Monte l'adaptateur avec les vraies classes domaine/repository, sans BDD.

    Le but est de prouver que la nouvelle UI sait consommer l'architecture métier
    actuelle avant tout branchement à la persistance de production.
    """
    from infrastructure.repositories.people_repository import PeopleRepository

    repo = PeopleRepository()
    repo.add(Person(code_internal="QT-001", first_name="Aline", last_name="Martin"))
    repo.add(Person(code_internal="QT-002", first_name="Benoît", last_name="Durand"))
    return DomainPeopleReadAdapter(repo)
