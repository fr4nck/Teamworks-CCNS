from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from domain.hr_connections import (
    ConnectionProfile,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)

from .structure_configuration import ConnectionProfileRepository


class EmployeeProtectionRepository(Protocol):
    """Port applicatif minimal pour le suivi de protection sociale salarié."""

    def save_employee_protection(
        self,
        record: EmployeeProtectionRecord,
    ) -> EmployeeProtectionRecord:
        ...

    def get_employee_protection(
        self,
        *,
        structure_ref: str,
        record_id: str,
    ) -> EmployeeProtectionRecord | None:
        ...

    def list_employee_protection(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
    ) -> tuple[EmployeeProtectionRecord, ...]:
        ...

    def supersede_employee_protection(
        self,
        *,
        ended_record: EmployeeProtectionRecord,
        successor_record: EmployeeProtectionRecord,
    ) -> tuple[EmployeeProtectionRecord, EmployeeProtectionRecord]:
        ...


@dataclass(frozen=True)
class EmployeeProtectionView:
    """Projection UI-agnostique d'un suivi salarié et de son organisme."""

    record: EmployeeProtectionRecord
    organization_label: str | None
    organization_configured: bool

    @property
    def payroll_relevant(self) -> bool:
        return (
            self.record.organization_kind
            in {
                OrganizationKind.MUTUELLE,
                OrganizationKind.PREVOYANCE,
                OrganizationKind.RETRAITE_COMPLEMENTAIRE,
            }
            and self.record.relation_kind
            in {
                EmployeeProtectionRelationKind.AFFILIATION,
                EmployeeProtectionRelationKind.WAIVER,
                EmployeeProtectionRelationKind.REGISTRATION,
            }
        )


class EmployeeProtectionService:
    """Cas d'usage du futur onglet « Protection sociale & organismes ».

    L'écriture exige qu'un organisme correspondant soit configuré pour la structure,
    afin d'éviter les références orphelines. La lecture reste tolérante : l'historique
    salarié doit demeurer consultable même si une ancienne configuration d'organisme
    a ensuite été retirée.

    Ce service prépare des vues et des filtres utiles à la future préparation de paie,
    mais ne calcule aucune cotisation et ne dépend ni de l'UI ni d'un backend précis.
    """

    def __init__(
        self,
        *,
        repository: EmployeeProtectionRepository,
        profile_repository: ConnectionProfileRepository,
    ) -> None:
        self._repository = repository
        self._profile_repository = profile_repository

    def save(self, record: EmployeeProtectionRecord) -> EmployeeProtectionView:
        profile = self._validated_profile(record)
        saved = self._repository.save_employee_protection(record)
        return self._view(saved, profile)

    def supersede(
        self,
        *,
        ended_record: EmployeeProtectionRecord,
        successor_record: EmployeeProtectionRecord,
    ) -> tuple[EmployeeProtectionView, EmployeeProtectionView]:
        """Remplace une période active par sa période successeure en une transaction.

        Le profil de l'ancien organisme peut avoir été retiré : l'historique doit
        rester clôturable. En revanche, l'organisme de la période successeure doit
        être configuré au moment de l'écriture.
        """
        self._validate_succession_pair(
            ended_record=ended_record,
            successor_record=successor_record,
        )
        successor_profile = self._validated_profile(successor_record)
        saved_ended, saved_successor = self._repository.supersede_employee_protection(
            ended_record=ended_record,
            successor_record=successor_record,
        )
        return (
            self._view(saved_ended, self._profile_for(saved_ended)),
            self._view(saved_successor, successor_profile),
        )

    def get(
        self,
        *,
        structure_ref: str,
        record_id: str,
    ) -> EmployeeProtectionView | None:
        record = self._repository.get_employee_protection(
            structure_ref=structure_ref,
            record_id=record_id,
        )
        if record is None:
            return None
        return self._view(record, self._profile_for(record))

    def list_for_employee(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
    ) -> tuple[EmployeeProtectionView, ...]:
        return tuple(
            self._view(record, self._profile_for(record))
            for record in self._repository.list_employee_protection(
                structure_ref=structure_ref,
                employee_ref=employee_ref,
            )
        )

    def effective_on(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        as_of: date,
    ) -> tuple[EmployeeProtectionView, ...]:
        return tuple(
            view
            for view in self.list_for_employee(
                structure_ref=structure_ref,
                employee_ref=employee_ref,
            )
            if view.record.is_effective_on(as_of=as_of)
        )

    def due_on_or_before(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        as_of: date,
    ) -> tuple[EmployeeProtectionView, ...]:
        return tuple(
            view
            for view in self.list_for_employee(
                structure_ref=structure_ref,
                employee_ref=employee_ref,
            )
            if view.record.is_due_on_or_before(as_of=as_of)
        )

    def payroll_relevant_on(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        as_of: date,
    ) -> tuple[EmployeeProtectionView, ...]:
        return tuple(
            view
            for view in self.effective_on(
                structure_ref=structure_ref,
                employee_ref=employee_ref,
                as_of=as_of,
            )
            if view.payroll_relevant
        )

    def _validated_profile(self, record: EmployeeProtectionRecord) -> ConnectionProfile:
        if not isinstance(record, EmployeeProtectionRecord):
            raise TypeError("Le suivi de protection sociale à enregistrer est invalide.")
        profile = self._profile_repository.get_profile(
            structure_ref=record.structure_ref,
            organization_code=record.organization_code,
        )
        if profile is None:
            raise ValueError(
                "L'organisme doit être configuré pour la structure avant de rattacher "
                "un suivi salarié."
            )
        self._check_organization_kind(record=record, profile=profile)
        return profile

    @staticmethod
    def _validate_succession_pair(
        *,
        ended_record: EmployeeProtectionRecord,
        successor_record: EmployeeProtectionRecord,
    ) -> None:
        if not isinstance(ended_record, EmployeeProtectionRecord):
            raise TypeError("La période à clôturer est invalide.")
        if not isinstance(successor_record, EmployeeProtectionRecord):
            raise TypeError("La période successeure est invalide.")
        if ended_record.status is not EmployeeProtectionStatus.ENDED:
            raise ValueError("La période précédente doit être préparée comme terminée.")
        if successor_record.status is not EmployeeProtectionStatus.ACTIVE:
            raise ValueError("La période successeure doit être active.")
        if ended_record.structure_ref != successor_record.structure_ref:
            raise ValueError("Les deux périodes doivent appartenir à la même structure.")
        if ended_record.employee_ref != successor_record.employee_ref:
            raise ValueError("Les deux périodes doivent appartenir au même salarié.")
        if ended_record.record_id == successor_record.record_id:
            raise ValueError("La période successeure doit recevoir un nouvel identifiant.")

        ended_on = ended_record.effective_period.ends_on
        successor_starts_on = successor_record.effective_period.starts_on
        if ended_on is None or successor_starts_on is None:
            raise ValueError("La succession exige des dates de fin et de début explicites.")
        if ended_on + timedelta(days=1) != successor_starts_on:
            raise ValueError("Les périodes successives doivent être contiguës et sans chevauchement.")

    def _profile_for(self, record: EmployeeProtectionRecord) -> ConnectionProfile | None:
        return self._profile_repository.get_profile(
            structure_ref=record.structure_ref,
            organization_code=record.organization_code,
        )

    @staticmethod
    def _check_organization_kind(
        *,
        record: EmployeeProtectionRecord,
        profile: ConnectionProfile,
    ) -> None:
        if profile.organization.kind is not record.organization_kind:
            raise ValueError(
                "La famille d'organisme du suivi salarié ne correspond pas à la "
                "configuration de la structure."
            )

    @staticmethod
    def _view(
        record: EmployeeProtectionRecord,
        profile: ConnectionProfile | None,
    ) -> EmployeeProtectionView:
        return EmployeeProtectionView(
            record=record,
            organization_label=profile.organization.label if profile is not None else None,
            organization_configured=profile is not None,
        )
