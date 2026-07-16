"""Objet métier immutable représentant l'engagement d'un salarié."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from .contract_status import ContractStatus
from .contract_type import ContractType
from .employee import Employee


@dataclass(frozen=True, slots=True)
class Contract:
    """Contrat liant un :class:`Employee` à l'association.

    Cet objet porte uniquement le cycle de vie contractuel. Les éléments de
    rémunération, de classification, de temps de travail ou de planning ne
    relèvent pas de ce modèle.
    """

    employee: Employee
    contract_type: ContractType
    start_date: date
    status: ContractStatus
    id: UUID = field(default_factory=uuid4, kw_only=True)
    end_date: Optional[date] = None
    signature_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    internal_reference: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du contrat doit être un UUID.")
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié du contrat doit être un Employee valide.")
        if not isinstance(self.contract_type, ContractType):
            raise ValueError("Le type de contrat est invalide.")
        if not isinstance(self.status, ContractStatus):
            raise ValueError("Le statut du contrat est invalide.")

        _require_date(self.start_date, "La date de début du contrat")
        _validate_optional_date(self.end_date, "La date de fin du contrat")
        _validate_optional_date(self.signature_date, "La date de signature")
        _validate_optional_date(
            self.probation_end_date,
            "La date de fin de période d'essai",
        )

        if self.contract_type is not ContractType.CDI and self.end_date is None:
            raise ValueError("Ce type de contrat doit comporter une date de fin.")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("La date de fin ne peut pas être antérieure à la date de début.")
        if self.signature_date is not None and self.signature_date > self.start_date:
            raise ValueError("La date de signature ne peut pas être postérieure au début.")
        if self.probation_end_date is not None:
            if self.probation_end_date < self.start_date:
                raise ValueError(
                    "La fin de période d'essai ne peut pas être antérieure au début."
                )
            if self.end_date is not None and self.probation_end_date > self.end_date:
                raise ValueError(
                    "La fin de période d'essai ne peut pas être postérieure à la fin du contrat."
                )

        object.__setattr__(
            self,
            "internal_reference",
            _normalize_optional_reference(self.internal_reference),
        )

    def is_effective(self, on_date: date) -> bool:
        """Indique si le contrat est actif à la date fournie."""

        _require_date(on_date, "La date d'évaluation")
        return (
            self.status is ContractStatus.ACTIVE
            and self.start_date <= on_date
            and (self.end_date is None or on_date <= self.end_date)
        )


def _require_date(value: date, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError(f"{field_name} doit être une date.")


def _validate_optional_date(value: Optional[date], field_name: str) -> None:
    if value is not None:
        _require_date(value, field_name)


def _normalize_optional_reference(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError("La référence interne du contrat est invalide.")
    return normalized
