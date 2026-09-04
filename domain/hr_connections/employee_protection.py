from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Iterable, Tuple

from .organizations import EffectivePeriod, OrganizationKind


class EmployeeProtectionRelationKind(str, Enum):
    """Nature administrative du lien entre un salarié et un organisme."""

    AFFILIATION = "affiliation"
    WAIVER = "waiver"
    REGISTRATION = "registration"
    MONITORING = "monitoring"


class EmployeeProtectionStatus(str, Enum):
    """État d'un lien de protection sociale, distinct de sa nature."""

    TODO = "todo"
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


_ALLOWED_ORGANIZATION_KINDS = frozenset(
    {
        OrganizationKind.MUTUELLE,
        OrganizationKind.PREVOYANCE,
        OrganizationKind.RETRAITE_COMPLEMENTAIRE,
        OrganizationKind.SPST,
    }
)


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@dataclass(frozen=True)
class EmployeeProtectionRecord:
    """Donnée historisable de protection sociale rattachée à un salarié.

    Le modèle conserve uniquement des métadonnées administratives utiles au suivi RH
    et à une future préparation de paie : organisme, période d'effet, régime/option,
    profil de cotisation, référence externe et justificatif opaque. Le contenu des
    justificatifs et les données de santé ne font pas partie de cet objet.
    """

    record_id: str
    structure_ref: str
    employee_ref: str
    organization_code: str
    organization_kind: OrganizationKind
    relation_kind: EmployeeProtectionRelationKind
    status: EmployeeProtectionStatus = EmployeeProtectionStatus.TODO
    effective_period: EffectivePeriod = field(default_factory=EffectivePeriod)
    scheme_code: str | None = None
    option_code: str | None = None
    contribution_profile_code: str | None = None
    waiver_reason_code: str | None = None
    external_reference: str | None = None
    document_ref: str | None = None
    administrative_deadline: date | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("L'identifiant du suivi de protection sociale est obligatoire.")
        if not self.structure_ref.strip():
            raise ValueError("La référence de structure est obligatoire.")
        if not self.employee_ref.strip():
            raise ValueError("La référence du salarié est obligatoire.")
        if not self.organization_code.strip():
            raise ValueError("Le code de l'organisme est obligatoire.")
        if not isinstance(self.organization_kind, OrganizationKind):
            raise TypeError("La famille d'organisme est invalide.")
        if self.organization_kind not in _ALLOWED_ORGANIZATION_KINDS:
            raise ValueError(
                "Ce suivi salarié est réservé à la mutuelle, la prévoyance, "
                "la retraite complémentaire et au SPST."
            )
        if not isinstance(self.relation_kind, EmployeeProtectionRelationKind):
            raise TypeError("La nature du lien de protection sociale est invalide.")
        if not isinstance(self.status, EmployeeProtectionStatus):
            raise TypeError("Le statut du lien de protection sociale est invalide.")
        if not isinstance(self.effective_period, EffectivePeriod):
            raise TypeError("La période d'effet du lien de protection sociale est invalide.")
        if self.administrative_deadline is not None and not isinstance(
            self.administrative_deadline, date
        ):
            raise TypeError("L'échéance administrative est invalide.")

        if self.relation_kind is EmployeeProtectionRelationKind.WAIVER:
            if self.organization_kind is not OrganizationKind.MUTUELLE:
                raise ValueError("Une dispense est rattachée à un organisme de mutuelle.")
            if not self.waiver_reason_code:
                raise ValueError("Le motif codifié de dispense est obligatoire.")
        elif self.waiver_reason_code is not None:
            raise ValueError("Un motif de dispense ne peut être porté que par une dispense.")

        if self.relation_kind is EmployeeProtectionRelationKind.MONITORING:
            if self.organization_kind is not OrganizationKind.SPST:
                raise ValueError("Le suivi administratif salarié est réservé au SPST.")
        elif self.organization_kind is OrganizationKind.SPST and self.relation_kind not in {
            EmployeeProtectionRelationKind.REGISTRATION,
            EmployeeProtectionRelationKind.MONITORING,
        }:
            raise ValueError("Le SPST utilise un enregistrement ou un suivi administratif.")

        if self.status in {EmployeeProtectionStatus.ACTIVE, EmployeeProtectionStatus.ENDED}:
            if self.effective_period.starts_on is None:
                raise ValueError("Une donnée effective doit avoir une date de début.")
        if self.status is EmployeeProtectionStatus.ENDED:
            if self.effective_period.ends_on is None:
                raise ValueError("Une donnée terminée doit avoir une date de fin.")

    @classmethod
    def create(
        cls,
        *,
        record_id: str,
        structure_ref: str,
        employee_ref: str,
        organization_code: str,
        organization_kind: OrganizationKind,
        relation_kind: EmployeeProtectionRelationKind,
        status: EmployeeProtectionStatus = EmployeeProtectionStatus.TODO,
        effective_period: EffectivePeriod | None = None,
        scheme_code: str | None = None,
        option_code: str | None = None,
        contribution_profile_code: str | None = None,
        waiver_reason_code: str | None = None,
        external_reference: str | None = None,
        document_ref: str | None = None,
        administrative_deadline: date | None = None,
        source: str | None = None,
    ) -> "EmployeeProtectionRecord":
        return cls(
            record_id=record_id.strip(),
            structure_ref=structure_ref.strip(),
            employee_ref=employee_ref.strip(),
            organization_code=organization_code.strip(),
            organization_kind=organization_kind,
            relation_kind=relation_kind,
            status=status,
            effective_period=effective_period or EffectivePeriod(),
            scheme_code=_optional_text(scheme_code),
            option_code=_optional_text(option_code),
            contribution_profile_code=_optional_text(contribution_profile_code),
            waiver_reason_code=_optional_text(waiver_reason_code),
            external_reference=_optional_text(external_reference),
            document_ref=_optional_text(document_ref),
            administrative_deadline=administrative_deadline,
            source=_optional_text(source),
        )

    @property
    def is_closed(self) -> bool:
        return self.status in {EmployeeProtectionStatus.ENDED, EmployeeProtectionStatus.CANCELLED}

    def is_effective_on(self, *, as_of: date) -> bool:
        if not isinstance(as_of, date):
            raise TypeError("La date de consultation est invalide.")
        if self.status not in {EmployeeProtectionStatus.ACTIVE, EmployeeProtectionStatus.ENDED}:
            return False
        return self.effective_period.includes(as_of)

    def is_due_on_or_before(self, *, as_of: date) -> bool:
        if not isinstance(as_of, date):
            raise TypeError("La date de consultation est invalide.")
        return (
            self.administrative_deadline is not None
            and not self.is_closed
            and self.administrative_deadline <= as_of
        )


class EmployeeProtectionPortfolio:
    """Collection métier légère, isolée de la persistance et de l'interface."""

    def __init__(self, records: Iterable[EmployeeProtectionRecord] = ()) -> None:
        self._records: list[EmployeeProtectionRecord] = []
        self._by_id: dict[str, EmployeeProtectionRecord] = {}
        for record in records:
            self.add(record)

    def add(self, record: EmployeeProtectionRecord) -> None:
        if not isinstance(record, EmployeeProtectionRecord):
            raise TypeError("Le suivi de protection sociale est invalide.")
        if record.record_id in self._by_id:
            raise ValueError(
                f"Le suivi de protection sociale '{record.record_id}' existe déjà."
            )
        self._records.append(record)
        self._by_id[record.record_id] = record

    def all(self) -> Tuple[EmployeeProtectionRecord, ...]:
        return tuple(self._records)

    def for_employee(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
    ) -> Tuple[EmployeeProtectionRecord, ...]:
        normalized_structure = structure_ref.strip()
        normalized_employee = employee_ref.strip()
        if not normalized_structure:
            raise ValueError("La référence de structure est obligatoire.")
        if not normalized_employee:
            raise ValueError("La référence du salarié est obligatoire.")
        return tuple(
            record
            for record in self._records
            if record.structure_ref == normalized_structure
            and record.employee_ref == normalized_employee
        )

    def effective_for_employee(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        as_of: date,
    ) -> Tuple[EmployeeProtectionRecord, ...]:
        return tuple(
            record
            for record in self.for_employee(
                structure_ref=structure_ref,
                employee_ref=employee_ref,
            )
            if record.is_effective_on(as_of=as_of)
        )

    def due_for_employee(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        as_of: date,
    ) -> Tuple[EmployeeProtectionRecord, ...]:
        return tuple(
            record
            for record in self.for_employee(
                structure_ref=structure_ref,
                employee_ref=employee_ref,
            )
            if record.is_due_on_or_before(as_of=as_of)
        )
