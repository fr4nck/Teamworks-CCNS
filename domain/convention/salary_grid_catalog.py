from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid_entry import SalaryGridEntry
from domain.convention.salary_grid_version import SalaryGridVersion


def _strict_date(value: object) -> date:
    if type(value) is not date:
        raise TypeError("reference_date doit être une date stricte.")
    return value


@dataclass(frozen=True, slots=True)
class SalaryGridCatalog:
    versions: tuple[SalaryGridVersion, ...]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        if type(self.versions) is not tuple:
            raise TypeError("versions doit être un tuple non vide.")
        if not self.versions:
            raise ValueError("versions doit être un tuple non vide.")
        if any(type(version) is not SalaryGridVersion for version in self.versions):
            raise TypeError("Chaque version doit être un SalaryGridVersion.")
        if len({version.id for version in self.versions}) != len(self.versions):
            raise ValueError("Les UUID des versions doivent être uniques.")
        if len({version.code for version in self.versions}) != len(self.versions):
            raise ValueError("Les codes des versions doivent être uniques.")
        for index, left in enumerate(self.versions):
            for right in self.versions[index + 1 :]:
                if self._overlap(left, right):
                    raise ValueError("Les périodes d’application des grilles ne doivent pas se chevaucher.")

    @staticmethod
    def _overlap(left: SalaryGridVersion, right: SalaryGridVersion) -> bool:
        left_ends_after_right_starts = left.effective_until is None or left.effective_until >= right.effective_from
        right_ends_after_left_starts = right.effective_until is None or right.effective_until >= left.effective_from
        return left_ends_after_right_starts and right_ends_after_left_starts

    def version_count(self) -> int:
        return len(self.versions)

    def version_applicable_on(self, reference_date: date) -> SalaryGridVersion:
        reference_date = _strict_date(reference_date)
        for version in self.versions:
            if version.applies_on(reference_date):
                return version
        raise ValueError("Aucune grille salariale n’est applicable à la date demandée.")

    def entry_for(self, classification_group: CCNSClassification, reference_date: date) -> SalaryGridEntry:
        return self.version_applicable_on(reference_date).entry_for_group(classification_group)

    def amount_for(self, classification_group: CCNSClassification, reference_date: date) -> Decimal:
        return self.entry_for(classification_group, reference_date).amount

    def has_version_for(self, reference_date: date) -> bool:
        reference_date = _strict_date(reference_date)
        return any(version.applies_on(reference_date) for version in self.versions)
