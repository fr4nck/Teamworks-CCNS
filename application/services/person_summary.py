from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class PersonSummaryIdentity:
    civilite: str | None
    nom: str | None
    prenom: str | None
    date_naiss: str | None
    ville_naiss: str | None
    adresse_resid: str | None
    cp_resid: str | int | None
    ville_resid: str | None


@dataclass(frozen=True)
class PersonSummaryContract:
    classification: str
    date_debut: str
    date_fin: str | None
    date_rupture: str | None
    duree_indeterminee: str


@dataclass(frozen=True)
class PersonSummary:
    identity: PersonSummaryIdentity
    coordinates: tuple[str, ...]
    contracts: tuple[PersonSummaryContract, ...]


@dataclass(frozen=True)
class ContractSummary:
    kind: str
    contract: PersonSummaryContract | None
    active: bool


class PersonSummaryRepository(Protocol):
    def get_identity(self, person_id: int) -> PersonSummaryIdentity | None: ...
    def get_coordinates(self, person_id: int) -> Sequence[str]: ...
    def get_contracts(self, person_id: int) -> Sequence[PersonSummaryContract]: ...


def get_person_summary(person_id: int, repository: PersonSummaryRepository) -> PersonSummary | None:
    identity = repository.get_identity(person_id)
    if identity is None:
        return None
    return PersonSummary(
        identity=identity,
        coordinates=tuple(repository.get_coordinates(person_id)),
        contracts=tuple(repository.get_contracts(person_id)),
    )


def select_contract_summary(
    contracts: Sequence[PersonSummaryContract],
    today: datetime.date | None = None,
) -> ContractSummary:
    """Reproduit l'arbitrage historique du panneau wx sans dépendre de wx."""
    if not contracts:
        return ContractSummary("none", None, False)

    today_text = str(today or datetime.date.today())
    selected = ContractSummary("none", None, False)

    for contract in contracts:
        start = contract.date_debut
        end = contract.date_fin
        rupture = contract.date_rupture
        indefinite = contract.duree_indeterminee != "non"

        if not indefinite:
            if start <= today_text <= end:
                return ContractSummary("current_fixed", contract, True)
            if end < today_text:
                selected = ContractSummary("last_fixed", contract, False)
            elif start > today_text:
                selected = ContractSummary("next_fixed", contract, False)
        elif rupture not in ("", None):
            if start <= today_text <= rupture:
                return ContractSummary("current_ended", contract, True)
            if rupture < today_text:
                selected = ContractSummary("last_ended", contract, False)
            elif start > today_text:
                selected = ContractSummary("next_ended", contract, False)
        else:
            if start <= today_text:
                return ContractSummary("current_indefinite", contract, True)
            if start > today_text:
                selected = ContractSummary("next_indefinite", contract, False)

    return selected
