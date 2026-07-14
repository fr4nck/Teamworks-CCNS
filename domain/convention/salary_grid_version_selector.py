from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

from domain.convention.salary_grid_version import SalaryGridVersion


@dataclass(slots=True)
class SalaryGridVersionSelector:
    """Sélectionne la version descriptive d'une grille applicable à une date."""

    versions: tuple[SalaryGridVersion, ...]

    @classmethod
    def from_iterable(cls, versions: Iterable[SalaryGridVersion]) -> "SalaryGridVersionSelector":
        return cls(tuple(versions))

    def find_applicable_version(self, grid_code: str, reference_date: date) -> Optional[SalaryGridVersion]:
        candidates = [
            version
            for version in self.versions
            if version.grid_code == grid_code and version.is_applicable_on(reference_date)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda version: (version.effective_date, version.version))

    def require_applicable_version(self, grid_code: str, reference_date: date) -> SalaryGridVersion:
        version = self.find_applicable_version(grid_code, reference_date)
        if version is None:
            raise LookupError(f"No salary grid version found for {grid_code} on {reference_date.isoformat()}")
        return version
