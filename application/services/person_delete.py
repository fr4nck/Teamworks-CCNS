from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PersonDeleteCheck:
    allowed: bool
    blocking_reason: str | None = None


class PersonDeleteRepository(Protocol):
    def has_contracts(self, person_id: int) -> bool: ...
    def has_presences(self, person_id: int) -> bool: ...
    def has_travel(self, person_id: int) -> bool: ...
    def has_reimbursements(self, person_id: int) -> bool: ...
    def delete_person_with_dependents(self, person_id: int) -> None: ...


BLOCK_CONTRACTS = "contracts"
BLOCK_PRESENCES = "presences"
BLOCK_TRAVEL = "travel"
BLOCK_REIMBURSEMENTS = "reimbursements"


def check_person_deletion(person_id: int, repository: PersonDeleteRepository) -> PersonDeleteCheck:
    if repository.has_contracts(person_id):
        return PersonDeleteCheck(False, BLOCK_CONTRACTS)
    if repository.has_presences(person_id):
        return PersonDeleteCheck(False, BLOCK_PRESENCES)
    if repository.has_travel(person_id):
        return PersonDeleteCheck(False, BLOCK_TRAVEL)
    if repository.has_reimbursements(person_id):
        return PersonDeleteCheck(False, BLOCK_REIMBURSEMENTS)
    return PersonDeleteCheck(True)


def delete_person(person_id: int, repository: PersonDeleteRepository) -> PersonDeleteCheck:
    check = check_person_deletion(person_id, repository)
    if not check.allowed:
        return check
    repository.delete_person_with_dependents(person_id)
    return check
