from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from application.services.hr_connections import HrCaseDashboard, HrCaseDashboardService
from infrastructure.persistence.teamworks_hr_case_dashboard_documents_repository import (
    TeamworksHrCaseDashboardDocumentRepository,
)
from infrastructure.persistence.teamworks_hr_cases_repository import (
    TeamworksHrCasesRepository,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrCaseDashboardRuntime:
    """Façade de lecture du cockpit RH pour la base Teamworks active."""

    _structure_ref: str
    _service: HrCaseDashboardService

    def build(self, *, as_of: date) -> HrCaseDashboard:
        if not isinstance(as_of, date):
            raise TypeError("La date du cockpit des démarches RH est invalide.")
        return self._service.build(structure_ref=self._structure_ref, as_of=as_of)


class HrCaseDashboardRuntimeFactory:
    """Compose le cockpit et son suivi documentaire sur la base active.

    La factory choisit les adaptateurs de production. L'interface wxPython
    consomme uniquement ``HrCaseDashboardRuntime`` et ne connaît donc ni
    ``GestionDB`` ni l'identifiant logique de la structure.
    """

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_factory = db_factory

    def create(self) -> HrCaseDashboardRuntime:
        identity_repository = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        )
        structure_ref = identity_repository.get_or_create_structure_ref()
        case_repository = TeamworksHrCasesRepository(
            db_factory=self._db_factory,
        )
        profile_repository = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        document_repository = TeamworksHrCaseDashboardDocumentRepository(
            db_factory=self._db_factory,
        )
        service = HrCaseDashboardService(
            case_repository=case_repository,
            profile_repository=profile_repository,
            document_repository=document_repository,
        )
        return HrCaseDashboardRuntime(
            _structure_ref=structure_ref,
            _service=service,
        )
