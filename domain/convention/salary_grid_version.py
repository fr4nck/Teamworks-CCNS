from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from domain.convention.salary_grid_entry import SalaryGridEntry
from domain.engine.rule_reference import RuleReference
from domain.engine.rule_version import RuleVersion, RuleVersionValidationLevel


class SalaryGridVersionStatus(str, Enum):
    """Statut historique conservé pour les consommateurs existants."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


SALARY_GRID_SCHEDULED_APPLICABLE_VALIDATION_LEVELS = {
    RuleVersionValidationLevel.LEGAL_REVIEWED,
    RuleVersionValidationLevel.BUSINESS_VALIDATED,
}


_ENTRIES_NOT_PROVIDED = object()


def _strict_date(value: object, field_name: str) -> date:
    if type(value) is not date:
        raise TypeError(f"{field_name} doit être une date stricte.")
    return value


@dataclass(frozen=True, slots=True, init=False)
class SalaryGridVersion:
    """Version immuable des minima d'une grille salariale CCNS.

    Les alias historiques (``grid_code``, ``version``, ``effective_date`` et
    ``end_date``) restent lisibles afin de ne pas rompre le raccord existant.
    Une construction historique sans ``entries`` est tolérée uniquement pour
    les métadonnées déjà utilisées par le runtime. Toute construction métier
    explicite doit fournir un tuple non vide.
    """

    code: str
    name: str
    effective_from: date
    entries: tuple[SalaryGridEntry, ...]
    effective_until: Optional[date] = None
    source_reference: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4)

    # Métadonnées de traçabilité déjà présentes avant TW-026.
    status: SalaryGridVersionStatus = SalaryGridVersionStatus.ACTIVE
    comment: str = ""
    rule_version: Optional[RuleVersion] = None
    rule_reference: Optional[RuleReference] = None
    validation_level: RuleVersionValidationLevel = RuleVersionValidationLevel.DRAFT
    validation_date: Optional[date] = None
    legacy_version_label: str = ""

    def __init__(
        self,
        code: Optional[str] = None,
        name: Optional[str] = None,
        effective_from: Optional[date] = None,
        entries: object = _ENTRIES_NOT_PROVIDED,
        effective_until: Optional[date] = None,
        source_reference: Optional[str] = None,
        active: bool = True,
        *,
        id: Optional[UUID] = None,
        grid_code: Optional[str] = None,
        version: Optional[str] = None,
        effective_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: SalaryGridVersionStatus = SalaryGridVersionStatus.ACTIVE,
        comment: str = "",
        rule_version: Optional[RuleVersion] = None,
        rule_reference: Optional[RuleReference] = None,
        validation_level: RuleVersionValidationLevel = RuleVersionValidationLevel.DRAFT,
        validation_date: Optional[date] = None,
    ) -> None:
        legacy_construction = entries is _ENTRIES_NOT_PROVIDED and grid_code is not None
        raw_code = code if code is not None else grid_code
        raw_name = name if name is not None else version
        raw_start = effective_from if effective_from is not None else effective_date
        raw_end = effective_until if effective_until is not None else end_date

        if type(raw_code) is not str or not raw_code.strip():
            raise ValueError("code est obligatoire.")
        if type(raw_name) is not str or not raw_name.strip():
            raise ValueError("name est obligatoire.")
        normalized_code = raw_code.strip().upper()
        normalized_name = raw_name.strip()
        start = _strict_date(raw_start, "effective_from")
        if raw_end is not None:
            raw_end = _strict_date(raw_end, "effective_until")
            if raw_end < start:
                raise ValueError("effective_until ne peut pas précéder effective_from.")

        if entries is _ENTRIES_NOT_PROVIDED:
            if not legacy_construction:
                raise TypeError("entries doit être fourni sous forme de tuple non vide.")
            normalized_entries: tuple[SalaryGridEntry, ...] = ()
        else:
            if type(entries) is not tuple:
                raise TypeError("entries doit être un tuple non vide.")
            if not entries:
                raise ValueError("entries doit être un tuple non vide.")
            if any(type(entry) is not SalaryGridEntry for entry in entries):
                raise TypeError("Chaque entrée doit être un SalaryGridEntry.")
            normalized_entries = entries
            self._validate_entries(normalized_entries)

        if source_reference is not None:
            if type(source_reference) is not str or not source_reference.strip():
                raise ValueError("source_reference doit être une chaîne non vide.")
            source_reference = source_reference.strip()
        if type(active) is not bool:
            raise TypeError("active doit être un booléen strict.")
        if type(status) is not SalaryGridVersionStatus:
            raise TypeError("status doit être un SalaryGridVersionStatus.")
        if id is None:
            id = uuid4()
        elif type(id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        if validation_date is not None:
            _strict_date(validation_date, "validation_date")

        object.__setattr__(self, "code", normalized_code)
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "effective_from", start)
        object.__setattr__(self, "entries", normalized_entries)
        object.__setattr__(self, "effective_until", raw_end)
        object.__setattr__(self, "source_reference", source_reference)
        object.__setattr__(self, "active", active)
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "comment", comment)
        object.__setattr__(self, "rule_version", rule_version)
        object.__setattr__(self, "rule_reference", rule_reference)
        object.__setattr__(self, "validation_level", validation_level)
        object.__setattr__(self, "validation_date", validation_date)
        object.__setattr__(self, "legacy_version_label", version.strip() if type(version) is str else normalized_name)

    @staticmethod
    def _validate_entries(entries: tuple[SalaryGridEntry, ...]) -> None:
        seen: set[str] = set()
        for entry in entries:
            group_code = entry.classification_group.code.strip().upper()
            if group_code in seen:
                raise ValueError("Un seul minimum est autorisé par groupe dans une version.")
            seen.add(group_code)
            entry.validate_ccns_periodicity()

    @property
    def grid_code(self) -> str:
        return self.code

    @property
    def version(self) -> str:
        return self.legacy_version_label

    @property
    def effective_date(self) -> date:
        return self.effective_from

    @property
    def end_date(self) -> Optional[date]:
        return self.effective_until

    @property
    def rule_version_code(self) -> Optional[str]:
        return None if self.rule_version is None else self.rule_version.rule_code

    @property
    def rule_reference_code(self) -> Optional[str]:
        if self.rule_reference is not None:
            return self.rule_reference.code
        return None if self.rule_version is None else self.rule_version.rule_reference_code

    def is_active(self) -> bool:
        return self.active

    def is_open_ended(self) -> bool:
        return self.effective_until is None

    def applies_on(self, reference_date: date) -> bool:
        reference_date = _strict_date(reference_date, "reference_date")
        return reference_date >= self.effective_from and (
            self.effective_until is None or reference_date <= self.effective_until
        )

    def is_applicable_on(self, reference_date: date) -> bool:
        if not self.active:
            return False
        if self.status == SalaryGridVersionStatus.SCHEDULED and (
            self.validation_level not in SALARY_GRID_SCHEDULED_APPLICABLE_VALIDATION_LEVELS
        ):
            return False
        if self.status not in {SalaryGridVersionStatus.ACTIVE, SalaryGridVersionStatus.SCHEDULED}:
            return False
        return self.applies_on(reference_date)

    @staticmethod
    def _group_code(classification_group: object) -> str:
        from domain.convention.classification import CCNSClassification

        if type(classification_group) is not CCNSClassification:
            raise TypeError("classification_group doit être un CCNSClassification.")
        return classification_group.code.strip().upper()

    def entry_for_group(self, classification_group: object) -> SalaryGridEntry:
        requested_code = self._group_code(classification_group)
        for entry in self.entries:
            if entry.classification_group.code.strip().upper() == requested_code:
                return entry
        raise ValueError("Le groupe demandé n’est pas présent dans cette grille salariale.")

    def amount_for_group(self, classification_group: object) -> Decimal:
        return self.entry_for_group(classification_group).amount

    def contains_group(self, classification_group: object) -> bool:
        requested_code = self._group_code(classification_group)
        return any(entry.classification_group.code.strip().upper() == requested_code for entry in self.entries)

    def entry_count(self) -> int:
        return len(self.entries)
