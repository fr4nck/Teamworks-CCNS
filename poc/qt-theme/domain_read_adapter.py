from __future__ import annotations

from datetime import date
from typing import Sequence

from data_adapter import ContractView, PersonView, TeamworksReadAdapter
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.people.person import Person


class DomainPeopleReadAdapter(TeamworksReadAdapter):
    """Adaptateur lecture seule branché sur le domaine Teamworks actuel.

    Il accepte les repositories de domaine existants. Aucun import wxPython et
    aucune requête SQL ne sont autorisés ici. Les champs absents du domaine restent
    explicitement neutres au lieu d'être inventés.
    """

    def __init__(self, people_repository, contracts_repository=None):
        self._people_repository = people_repository
        self._contracts_repository = contracts_repository

    def list_people(self) -> Sequence[PersonView]:
        return tuple(self._person_to_view(person) for person in self._people_repository.list_all())

    def list_contracts(self, person_id: str) -> Sequence[ContractView]:
        if self._contracts_repository is None:
            return ()
        contracts = self._contracts_repository.list_by_person_id(person_id)
        return tuple(self._contract_to_view(contract) for contract in contracts)

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

    @staticmethod
    def _contract_to_view(contract: Contract) -> ContractView:
        weekly = (
            contract.weekly_hours
            if contract.weekly_hours is not None
            else contract.weekly_reference_hours
        )
        return ContractView(
            kind=contract.contract_type.value,
            start=_format_date(contract.start_date),
            end=_format_date(contract.end_date),
            classification=contract.ccns_classification_code or "—",
            duration="—" if weekly is None else f"{weekly:g} h",
            status=contract.contract_status or "—",
        )


def _format_date(value: date | None) -> str:
    return "—" if value is None else value.strftime("%d/%m/%Y")


def build_domain_smoke_adapter() -> DomainPeopleReadAdapter:
    """Monte les vrais repositories de domaine, toujours sans BDD de production.

    Le smoke test valide le double flux Person/Contract et le mapping de présentation
    en lecture seule, sans modifier domain/ ni infrastructure/.
    """
    from infrastructure.repositories.contracts_repository import ContractRepository
    from infrastructure.repositories.people_repository import PeopleRepository

    people_repo = PeopleRepository()
    contracts_repo = ContractRepository()

    aline = Person(code_internal="QT-001", first_name="Aline", last_name="Martin")
    benoit = Person(code_internal="QT-002", first_name="Benoît", last_name="Durand")
    people_repo.add(aline)
    people_repo.add(benoit)

    contracts_repo.add(
        Contract(
            person_id=aline.id,
            contract_type=ContractType.CDI,
            start_date=date(2024, 9, 1),
            weekly_reference_hours=35.0,
            ccns_classification_code="Groupe 3",
            contract_status="draft",
        )
    )
    contracts_repo.add(
        Contract(
            person_id=benoit.id,
            contract_type=ContractType.CDD,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 31),
            weekly_reference_hours=30.0,
            ccns_classification_code="Groupe 1",
            contract_status="draft",
        )
    )

    return DomainPeopleReadAdapter(people_repo, contracts_repo)
