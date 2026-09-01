from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from application.services.hr_connections import HrCaseDashboard, HrCaseDashboardService
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

    structure_ref: str
    _service: HrCaseDashboardService

    def build(self, *, as_of: date) -> HrCaseDashboard:
        if not isinstance(as_of, date):
            raise TypeError("La date du cockpit des démarches RH est invalide.")
        return self._service.build(structure_ref=self.structure_ref, as_of=as_of)


class HrCaseDashboardRuntimeFactory:
    """Compose CRH-21/22 sur l'identité stable de la base active.

    La factory choisit les adaptateurs de production. La future interface wxPython
    consommera uniquement ``HrCaseDashboardRuntime`` et n'aura donc aucune raison
    de connaître ``GestionDB`` ni l'identifiant logique de la structure.
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
        service = HrCaseDashboardService(
            case_repository=case_repository,
            profile_repository=profile_repository,
        )
        return HrCaseDashboardRuntime(
            structure_ref=structure_ref,
            _service=service,
        )
