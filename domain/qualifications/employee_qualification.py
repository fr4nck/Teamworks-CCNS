"""Lien métier immutable entre un salarié et une qualification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from domain.people.employee import Employee

from .qualification import Qualification
from .qualification_status import QualificationStatus


@dataclass(frozen=True, slots=True)
class EmployeeQualification:
    """Qualification détenue par un salarié, sans logique de renouvellement.

    Le statut est fourni par le métier. Les dates sont conservées telles
    qu'elles sont déclarées : cet objet ne déduit donc pas d'expiration à partir
    de la date du jour ou de la durée de validité de la qualification.
    """

    employee: Employee
    qualification: Qualification
    status: QualificationStatus
    obtained_at: Optional[date] = None
    expires_at: Optional[date] = None
    issuing_organization: Optional[str] = None
    certificate_number: Optional[str] = None
    observations: Optional[str] = None
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant de la qualification du salarié doit être un UUID.")
        if not isinstance(self.employee, Employee):
            raise ValueError("Le salarié est obligatoire et doit être un Employee.")
        if not isinstance(self.qualification, Qualification):
            raise ValueError("La qualification est obligatoire et doit être une Qualification.")
        if not isinstance(self.status, QualificationStatus):
            raise ValueError("Le statut de la qualification du salarié est invalide.")
        if not isinstance(self.active, bool):
            raise ValueError("Le statut actif de la qualification du salarié doit être un booléen.")

        obtained_at = _validated_date(self.obtained_at, "d'obtention")
        expires_at = _validated_date(self.expires_at, "d'expiration")
        if obtained_at is not None and expires_at is not None and expires_at < obtained_at:
            raise ValueError("La date d'expiration ne peut pas être antérieure à la date d'obtention.")

        object.__setattr__(self, "obtained_at", obtained_at)
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(
            self,
            "issuing_organization",
            _normalized_optional_text(self.issuing_organization, "organisme délivrant"),
        )
        object.__setattr__(
            self,
            "certificate_number",
            _normalized_optional_text(self.certificate_number, "numéro de certificat"),
        )
        object.__setattr__(
            self,
            "observations",
            _normalized_optional_text(self.observations, "observations"),
        )

    def is_valid(self) -> bool:
        """Indique si le statut déclaré est valide, sans calcul de date."""

        return self.status is QualificationStatus.VALID

    def is_expired(self) -> bool:
        """Indique si le statut déclaré est expiré, sans calcul de date."""

        return self.status is QualificationStatus.EXPIRED

    def has_expiration(self) -> bool:
        """Indique si une date d'expiration est déclarée."""

        return self.expires_at is not None


def _validated_date(value: Optional[date], field_name: str) -> Optional[date]:
    if value is None:
        return None
    if not isinstance(value, date):
        raise ValueError(f"La date {field_name} doit être une date.")
    return value


def _normalized_optional_text(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not (normalized := value.strip()):
        raise ValueError(f"Le champ {field_name} est invalide.")
    return normalized
