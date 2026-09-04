from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Callable
from uuid import uuid4

from domain.hr_connections import (
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    OrganizationKind,
)

from .employee_protection import EmployeeProtectionService, EmployeeProtectionView


@dataclass(frozen=True)
class EmployeeProtectionCreateRequest:
    """Données saisissables pour créer un suivi salarié sans exposer ses clés techniques."""

    organization_code: str
    organization_kind: OrganizationKind
    relation_kind: EmployeeProtectionRelationKind
    status: EmployeeProtectionStatus
    starts_on: date | None = None
    ends_on: date | None = None
    scheme_code: str | None = None
    option_code: str | None = None
    contribution_profile_code: str | None = None
    waiver_reason_code: str | None = None
    external_reference: str | None = None
    document_ref: str | None = None
    administrative_deadline: date | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.organization_code, str) or not self.organization_code.strip():
            raise ValueError("Le code de l'organisme est obligatoire.")
        if not isinstance(self.organization_kind, OrganizationKind):
            raise TypeError("La famille d'organisme est invalide.")
        if not isinstance(self.relation_kind, EmployeeProtectionRelationKind):
            raise TypeError("La nature du lien de protection sociale est invalide.")
        if not isinstance(self.status, EmployeeProtectionStatus):
            raise TypeError("Le statut du lien de protection sociale est invalide.")
        for field_name, value in (
            ("date d'effet", self.starts_on),
            ("date de fin", self.ends_on),
            ("échéance administrative", self.administrative_deadline),
        ):
            if value is not None and not isinstance(value, date):
                raise TypeError(f"La {field_name} est invalide.")
        EffectivePeriod(starts_on=self.starts_on, ends_on=self.ends_on)

    def to_record(
        self,
        *,
        record_id: str,
        structure_ref: str,
        employee_ref: str,
    ) -> EmployeeProtectionRecord:
        return EmployeeProtectionRecord.create(
            record_id=record_id,
            structure_ref=structure_ref,
            employee_ref=employee_ref,
            organization_code=self.organization_code,
            organization_kind=self.organization_kind,
            relation_kind=self.relation_kind,
            status=self.status,
            effective_period=EffectivePeriod(
                starts_on=self.starts_on,
                ends_on=self.ends_on,
            ),
            scheme_code=self.scheme_code,
            option_code=self.option_code,
            contribution_profile_code=self.contribution_profile_code,
            waiver_reason_code=self.waiver_reason_code,
            external_reference=self.external_reference,
            document_ref=self.document_ref,
            administrative_deadline=self.administrative_deadline,
            source=self.source,
        )


@dataclass(frozen=True)
class EmployeeProtectionSuccessionResult:
    """Résultat explicite d'une clôture et création atomiques de périodes."""

    previous: EmployeeProtectionView
    successor: EmployeeProtectionView


def _new_record_id() -> str:
    return str(uuid4())


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


class EmployeeProtectionActionService:
    """Frontière d'écriture contrôlée du suivi de protection sociale salarié.

    Le service ne fournit volontairement ni édition libre ni suppression. Une création
    reçoit un identifiant opaque généré par l'application. Une clôture conserve les
    métadonnées de la période. Une modification structurante passe par ``supersede`` :
    l'ancienne période est clôturée et la nouvelle est créée atomiquement.
    """

    def __init__(
        self,
        *,
        protection_service: EmployeeProtectionService,
        record_id_factory: Callable[[], str] | None = None,
    ) -> None:
        if not isinstance(protection_service, EmployeeProtectionService):
            raise TypeError("Le service de protection sociale est invalide.")
        self._protection_service = protection_service
        self._record_id_factory = record_id_factory or _new_record_id

    def register(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        request: EmployeeProtectionCreateRequest,
    ) -> EmployeeProtectionView:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        employee_ref = _required_text(
            employee_ref,
            "La référence du salarié est obligatoire.",
        )
        if not isinstance(request, EmployeeProtectionCreateRequest):
            raise TypeError("La demande de création du suivi salarié est invalide.")

        record_id = self._unused_record_id(structure_ref=structure_ref)
        return self._protection_service.save(
            request.to_record(
                record_id=record_id,
                structure_ref=structure_ref,
                employee_ref=employee_ref,
            )
        )

    def end(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        record_id: str,
        ends_on: date,
    ) -> EmployeeProtectionView:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        employee_ref = _required_text(
            employee_ref,
            "La référence du salarié est obligatoire.",
        )
        record_id = _required_text(
            record_id,
            "L'identifiant du suivi de protection sociale est obligatoire.",
        )
        if not isinstance(ends_on, date):
            raise TypeError("La date de fin du suivi de protection sociale est invalide.")

        current = self._active_record(
            structure_ref=structure_ref,
            employee_ref=employee_ref,
            record_id=record_id,
            purpose="clôturer",
        )
        ended = self._ended_record(current=current, ends_on=ends_on)
        return self._protection_service.save(ended)

    def supersede(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        record_id: str,
        request: EmployeeProtectionCreateRequest,
    ) -> EmployeeProtectionSuccessionResult:
        """Clôture une période et crée sa successeure sans fenêtre d'état intermédiaire."""
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        employee_ref = _required_text(
            employee_ref,
            "La référence du salarié est obligatoire.",
        )
        record_id = _required_text(
            record_id,
            "L'identifiant du suivi de protection sociale est obligatoire.",
        )
        if not isinstance(request, EmployeeProtectionCreateRequest):
            raise TypeError("La demande de succession du suivi salarié est invalide.")
        if request.status is not EmployeeProtectionStatus.ACTIVE:
            raise ValueError("Une période successeure doit être créée avec le statut actif.")
        if request.starts_on is None:
            raise ValueError("La période successeure doit avoir une date d'effet explicite.")

        current = self._active_record(
            structure_ref=structure_ref,
            employee_ref=employee_ref,
            record_id=record_id,
            purpose="remplacer",
        )
        current_start = current.effective_period.starts_on
        if current_start is None:
            raise RuntimeError("Un suivi actif doit conserver sa date d'effet.")
        if request.starts_on <= current_start:
            raise ValueError(
                "La période successeure doit commencer après la date d'effet de la période active."
            )

        previous_end = request.starts_on - timedelta(days=1)
        current_end = current.effective_period.ends_on
        if current_end is not None and previous_end > current_end:
            raise ValueError(
                "Une succession ne peut pas prolonger une période qui possède déjà une date de fin."
            )

        successor_id = self._unused_record_id(structure_ref=structure_ref)
        successor = request.to_record(
            record_id=successor_id,
            structure_ref=structure_ref,
            employee_ref=employee_ref,
        )
        ended = self._ended_record(current=current, ends_on=previous_end)
        previous_view, successor_view = self._protection_service.supersede(
            ended_record=ended,
            successor_record=successor,
        )
        return EmployeeProtectionSuccessionResult(
            previous=previous_view,
            successor=successor_view,
        )

    def _active_record(
        self,
        *,
        structure_ref: str,
        employee_ref: str,
        record_id: str,
        purpose: str,
    ) -> EmployeeProtectionRecord:
        current_view = self._protection_service.get(
            structure_ref=structure_ref,
            record_id=record_id,
        )
        if current_view is None:
            raise LookupError(
                f"Le suivi de protection sociale à {purpose} est introuvable."
            )
        current = current_view.record
        if current.employee_ref != employee_ref:
            raise ValueError("Le suivi de protection sociale n'appartient pas à ce salarié.")
        if current.status is not EmployeeProtectionStatus.ACTIVE:
            raise ValueError("Seul un suivi actif peut être modifié par cette action.")
        return current

    @staticmethod
    def _ended_record(
        *,
        current: EmployeeProtectionRecord,
        ends_on: date,
    ) -> EmployeeProtectionRecord:
        starts_on = current.effective_period.starts_on
        if starts_on is None:
            raise RuntimeError("Un suivi actif doit conserver sa date d'effet.")
        if ends_on < starts_on:
            raise ValueError("La date de fin ne peut pas précéder la date d'effet.")
        current_end = current.effective_period.ends_on
        if current_end is not None and ends_on > current_end:
            raise ValueError(
                "La clôture ne peut pas prolonger une date de fin déjà enregistrée."
            )
        return replace(
            current,
            status=EmployeeProtectionStatus.ENDED,
            effective_period=EffectivePeriod(
                starts_on=starts_on,
                ends_on=ends_on,
            ),
        )

    def _unused_record_id(self, *, structure_ref: str) -> str:
        record_id = self._next_record_id()
        if self._protection_service.get(
            structure_ref=structure_ref,
            record_id=record_id,
        ) is not None:
            raise RuntimeError(
                "Collision d'identifiant lors de la création du suivi de protection sociale."
            )
        return record_id

    def _next_record_id(self) -> str:
        record_id = self._record_id_factory()
        if not isinstance(record_id, str):
            raise TypeError("La fabrique d'identifiant du suivi salarié doit retourner du texte.")
        record_id = record_id.strip()
        if not record_id:
            raise ValueError("La fabrique d'identifiant du suivi salarié a retourné une valeur vide.")
        return record_id
