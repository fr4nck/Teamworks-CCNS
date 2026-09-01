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
from infrastructure.persistence.teamworks_employee_protection_succession_repository import (
    TeamworksEmployeeProtectionSuccessionRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class EmployeeProtectionActionsRuntime:
    """Façade d'écriture verrouillée sur la structure Teamworks active."""

    structure_ref: str
    _action_service: EmployeeProtectionActionService

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


class EmployeeProtectionActionsRuntimeFactory:
    """Compose les actions CRH-18/19 sur la base Teamworks active."""

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
        )
