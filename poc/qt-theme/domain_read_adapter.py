from __future__ import annotations

from datetime import date
from typing import Sequence

from data_adapter import ContractView, PersonGeneralitiesView, PersonView, TeamworksReadAdapter
from domain.contracts.contract import Contract
from domain.people.person import Person


EMPTY = "—"


class DomainPeopleReadAdapter(TeamworksReadAdapter):
    """Coordonne les lectures du domaine puis agrège des DTO de présentation.

    Le POC reste strictement en mémoire : aucun SQL direct, aucune dépendance wx,
    aucune donnée inventée. Les repositories optionnels représentent les futurs
    points d'agrégation de sous-domaines ; tant qu'une information n'est pas
    garantie par une source canonique, elle reste neutre.
    """

    def __init__(
        self,
        people_repository,
        contracts_repository=None,
        qualifications_repository=None,
        regulatory_repository=None,
        sites_repository=None,
    ):
        self._people_repository = people_repository
        self._contracts_repository = contracts_repository
        self._qualifications_repository = qualifications_repository
        self._regulatory_repository = regulatory_repository
        self._sites_repository = sites_repository
        self._person_ids_by_view_id: dict[str, str] = {}

    def list_people(self) -> Sequence[PersonView]:
        people = tuple(self._people_repository.list_all())
        self._person_ids_by_view_id = {
            (person.code_internal or person.id): person.id for person in people
        }
        return tuple(self._person_to_view(person) for person in people)

    def get_person_generalities(self, person_id: str) -> PersonGeneralitiesView | None:
        # Le domaine in-memory n'expose pas encore la fiche historique complète.
        return None

    def list_contracts(self, person_id: str) -> Sequence[ContractView]:
        if self._contracts_repository is None:
            return ()
        domain_person_id = self._person_ids_by_view_id.get(person_id, person_id)
        contracts = self._contracts_repository.list_by_person_id(domain_person_id)
        return tuple(self._contract_to_view(contract) for contract in contracts)

    def list_scenarios(self, person_id):
        return ()

    def list_trips(self, person_id):
        return ()

    def list_reimbursements(self, person_id):
        return ()

    def _person_to_view(self, person: Person) -> PersonView:
        contracts = self._contracts_for(person.id)
        primary_contract = contracts[0] if contracts else None

        return PersonView(
            id=person.code_internal or person.id or EMPTY,
            id_historique=None,
            name=person.display_name or EMPTY,
            first_name=person.first_name or EMPTY,
            last_name=person.last_name or EMPTY,
            birth_date=_format_date(person.birth_date),
            role=EMPTY,
            classification=(
                primary_contract.ccns_classification_code
                if primary_contract and primary_contract.ccns_classification_code
                else EMPTY
            ),
            contract=(
                primary_contract.contract_type.value
                if primary_contract is not None
                else EMPTY
            ),
            weekly_hours=_format_weekly_hours(primary_contract),
            status="Actif" if person.is_active else "Inactif",
            site=EMPTY,
            medical=EMPTY,
            mutual=EMPTY,
        )

    def _contracts_for(self, person_id: str) -> tuple[Contract, ...]:
        if self._contracts_repository is None:
            return ()
        return tuple(self._contracts_repository.list_by_person_id(person_id))

    @staticmethod
    def _contract_to_view(contract: Contract) -> ContractView:
        return ContractView(
            kind=contract.contract_type.value,
            start=_format_date(contract.start_date),
            end=_format_date(contract.end_date),
            classification=contract.ccns_classification_code or EMPTY,
            duration=_format_weekly_hours(contract),
            status=contract.contract_status or EMPTY,
        )


def _format_date(value: date | None) -> str:
    return EMPTY if value is None else value.strftime("%d/%m/%Y")


def _format_weekly_hours(contract: Contract | None) -> str:
    if contract is None:
        return EMPTY
    weekly = contract.weekly_hours if contract.weekly_hours is not None else contract.weekly_reference_hours
    return EMPTY if weekly is None else f"{weekly:g} h"


def build_domain_smoke_adapter() -> DomainPeopleReadAdapter:
    """Monte les vrais repositories de domaine, toujours sans BDD de production."""
    from infrastructure.repositories.contracts_repository import ContractRepository
    from infrastructure.repositories.people_repository import PeopleRepository
    from domain.contracts.contract_type import ContractType

    people_repo = PeopleRepository()
    contracts_repo = ContractRepository()

    aline = Person(
        code_internal="QT-001",
        first_name="Aline",
        last_name="Martin",
        birth_date=date(1990, 2, 12),
    )
    benoit = Person(
        code_internal="QT-002",
        first_name="Benoît",
        last_name="Durand",
        birth_date=date(1988, 11, 4),
    )
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
