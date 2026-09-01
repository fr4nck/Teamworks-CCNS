from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from application.services.hr_connections import (
    EmployeeProtectionActionService,
    EmployeeProtectionCreateRequest,
    EmployeeProtectionService,
    EmployeeProtectionSuccessionResult,
    EmployeeProtectionView,
)
from domain.hr_connections import EmployeeProtectionRecord, OrganizationKind
from infrastructure.persistence.teamworks_employee_protection_succession_repository import (
    TeamworksEmployeeProtectionSuccessionRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


_EMPLOYEE_PROTECTION_ORGANIZATION_KINDS = frozenset(
    {
        OrganizationKind.MUTUELLE,
        OrganizationKind.PREVOYANCE,
        OrganizationKind.RETRAITE_COMPLEMENTAIRE,
        OrganizationKind.SPST,
    }
)


@dataclass(frozen=True)
class EmployeeProtectionOrganizationOption:
    """Organisme configuré pouvant être proposé à l'interface salarié."""

    code: str
    label: str
    kind: OrganizationKind


@dataclass(frozen=True)
class EmployeeProtectionActionsRuntime:
    """Façade d'écriture verrouillée sur la structure Teamworks active."""

    structure_ref: str
    _action_service: EmployeeProtectionActionService
    _repository: TeamworksEmployeeProtectionSuccessionRepository

    def register(
        self,
        *,
        employee_ref: str,
        request: EmployeeProtectionCreateRequest,
    ) -> EmployeeProtectionView:
        return self._action_service.register(
            structure_ref=self.structure_ref,
            employee_ref=employee_ref,
            request=request,
        )

    def end(
        self,
        *,
        employee_ref: str,
        record_id: str,
        ends_on: date,
    ) -> EmployeeProtectionView:
        return self._action_service.end(
            structure_ref=self.structure_ref,
            employee_ref=employee_ref,
            record_id=record_id,
            ends_on=ends_on,
        )

    def supersede(
        self,
        *,
        employee_ref: str,
        record_id: str,
        request: EmployeeProtectionCreateRequest,
    ) -> EmployeeProtectionSuccessionResult:
        return self._action_service.supersede(
            structure_ref=self.structure_ref,
            employee_ref=employee_ref,
            record_id=record_id,
            request=request,
        )

    def available_organizations(self) -> tuple[EmployeeProtectionOrganizationOption, ...]:
        """Liste les organismes configurés qui acceptent un suivi salarié permanent."""
        profiles = self._repository.list_profiles(structure_ref=self.structure_ref)
        options = (
            EmployeeProtectionOrganizationOption(
                code=profile.organization.code,
                label=profile.organization.label,
                kind=profile.organization.kind,
            )
            for profile in profiles
            if profile.organization.kind in _EMPLOYEE_PROTECTION_ORGANIZATION_KINDS
        )
        return tuple(
            sorted(
                options,
                key=lambda option: (
                    option.kind.value,
                    option.label.casefold(),
                    option.code,
                ),
            )
        )

    def get_record(
        self,
        *,
        employee_ref: str,
        record_id: str,
    ) -> EmployeeProtectionRecord:
        """Relit un suivi sélectionné sans exposer le repository au code wxPython."""
        employee_ref = _required_text(
            employee_ref,
            "La référence du salarié est obligatoire.",
        )
        record_id = _required_text(
            record_id,
            "L'identifiant du suivi de protection sociale est obligatoire.",
        )
        record = self._repository.get_employee_protection(
            structure_ref=self.structure_ref,
            record_id=record_id,
        )
        if record is None:
            raise LookupError("Le suivi de protection sociale sélectionné est introuvable.")
        if record.employee_ref != employee_ref:
            raise ValueError("Le suivi de protection sociale n'appartient pas à ce salarié.")
        return record


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


class EmployeeProtectionActionsRuntimeFactory:
    """Compose les actions CRH-18/19/20 sur la base Teamworks active."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        record_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._db_factory = db_factory
        self._record_id_factory = record_id_factory

    def create(self) -> EmployeeProtectionActionsRuntime:
        identity_repository = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        )
        structure_ref = identity_repository.get_or_create_structure_ref()
        repository = TeamworksEmployeeProtectionSuccessionRepository(
            db_factory=self._db_factory,
        )
        protection_service = EmployeeProtectionService(
            repository=repository,
            profile_repository=repository,
        )
        action_service = EmployeeProtectionActionService(
            protection_service=protection_service,
            record_id_factory=self._record_id_factory,
        )
        return EmployeeProtectionActionsRuntime(
            structure_ref=structure_ref,
            _action_service=action_service,
            _repository=repository,
        )
