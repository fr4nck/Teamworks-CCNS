from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

from domain.engine.rule_version import RuleVersion


@dataclass(slots=True)
class RuleVersionSelector:
    """Sélectionne la version d'une règle applicable à une date donnée."""

    versions: tuple[RuleVersion, ...]

    @classmethod
    def from_iterable(cls, versions: Iterable[RuleVersion]) -> "RuleVersionSelector":
        return cls(tuple(versions))

    def find_applicable_version(self, rule_code: str, reference_date: date) -> Optional[RuleVersion]:
        candidates = [
            version
            for version in self.versions
            if version.rule_code == rule_code and version.is_applicable_on(reference_date)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda version: (version.effective_date, version.version))

    def require_applicable_version(self, rule_code: str, reference_date: date) -> RuleVersion:
        version = self.find_applicable_version(rule_code, reference_date)
        if version is None:
            raise LookupError(f"No rule version found for {rule_code} on {reference_date.isoformat()}")
        return version
