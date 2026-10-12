from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from application.services.hr_connections import EmployeeProtectionService
from application.services.hr_connections.employee_protection_summary import (
    EmployeeProtectionSummary,
    EmployeeProtectionSummaryService,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class EmployeeProtectionSummaryRuntime:
    """Façade minimale consommable par la future page salarié.

    La structure active est verrouillée lors de la composition. L'interface fournit
    uniquement la référence du salarié et la date de consultation : elle n'a donc ni
    à connaître le backend ni à fabriquer elle-même une référence de structure.
    """

    structure_ref: str
    _summary_service: EmployeeProtectionSummaryService

    def build(self, *, employee_ref: str, as_of: date) -> EmployeeProtectionSummary:
        if not isinstance(employee_ref, str):
            raise TypeError("La référence du salarié est invalide.")
        employee_ref = employee_ref.strip()
        if not employee_ref:
            raise ValueError("La référence du salarié est obligatoire.")
        if not isinstance(as_of, date):
            raise TypeError("La date de consultation est invalide.")
        return self._summary_service.build(
            structure_ref=self.structure_ref,
            employee_ref=employee_ref,
            as_of=as_of,
        )


class EmployeeProtectionSummaryRuntimeFactory:
    """Point de composition du suivi salarié sur la base Teamworks active."""

    def __init__(self, *, db_factory: Callable[[], object] | None = None) -> None:
        self._db_factory = db_factory

    def create(self) -> EmployeeProtectionSummaryRuntime:
        identity_repository = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        )
        structure_ref = identity_repository.get_or_create_structure_ref()

        repository = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        protection_service = EmployeeProtectionService(
            repository=repository,
            profile_repository=repository,
        )
        summary_service = EmployeeProtectionSummaryService(
            protection_service=protection_service,
        )
        return EmployeeProtectionSummaryRuntime(
            structure_ref=structure_ref,
            _summary_service=summary_service,
        )
