from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from application.control import ContractSalaryControlContractProvider
from domain.contracts.contract import Contract
from infrastructure.repositories.contracts_repository import ContractRepository


@dataclass(frozen=True, slots=True)
class ContractRepositorySalaryControlProvider(ContractSalaryControlContractProvider):
    """Adaptateur du dépôt de contrats vers le port de consultation salariale."""

    contracts_repository: ContractRepository

    def __post_init__(self) -> None:
        if type(self.contracts_repository) is not ContractRepository:
            raise TypeError("contracts_repository doit être un ContractRepository strict.")

    def list_for_salary_control(
        self,
        *,
        contract_ids: tuple[UUID, ...] = (),
        employee_ids: tuple[UUID, ...] = (),
    ) -> Iterable[Contract]:
        """Sélectionne les contrats du dépôt sans modifier leur ordre ni leurs instances."""

        _strict_uuid_tuple(contract_ids, "contract_ids")
        _strict_uuid_tuple(employee_ids, "employee_ids")

        contracts = self.contracts_repository.list_all()
        if not contract_ids and not employee_ids:
            return contracts

        selected_contract_ids = set(contract_ids)
        selected_employee_ids = set(employee_ids)
        result: list[Contract] = []
        seen_contract_ids: set[UUID] = set()

        for contract in contracts:
            if type(contract) is not Contract:
                raise TypeError("contracts_repository doit retourner uniquement des Contract.")
            contract_id = _contract_uuid(contract)
            employee_id = _employee_uuid(contract)
            if contract_ids and contract_id not in selected_contract_ids:
                continue
            if employee_ids and employee_id not in selected_employee_ids:
                continue
            if contract_id in seen_contract_ids:
                continue
            result.append(contract)
            seen_contract_ids.add(contract_id)
        return result


def _strict_uuid_tuple(value: object, field_name: str) -> tuple[UUID, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} doit être un tuple strict.")
    seen: set[UUID] = set()
    for item in value:
        if type(item) is not UUID:
            raise TypeError(f"{field_name} doit contenir uniquement des UUID stricts.")
        if item in seen:
            raise ValueError(f"{field_name} ne doit pas contenir de doublons.")
        seen.add(item)
    return value


def _contract_uuid(contract: Contract) -> UUID:
    raw = contract.id
    if type(raw) is UUID:
        return raw
    if type(raw) is str:
        try:
            return UUID(raw)
        except ValueError as exc:
            raise ValueError("L'identifiant historique du contrat doit être une chaîne UUID valide.") from exc
    raise TypeError("L'identifiant du contrat doit être un UUID strict ou une chaîne UUID historique.")


def _employee_uuid(contract: Contract) -> UUID:
    raw = contract.person_id
    if type(raw) is UUID:
        return raw
    if type(raw) is str:
        try:
            return UUID(raw)
        except ValueError as exc:
            raise ValueError("L'identifiant historique du salarié doit être une chaîne UUID valide.") from exc
    raise TypeError("L'identifiant du salarié doit être un UUID strict ou une chaîne UUID historique.")
