from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from application.services.hr_connections.hr_case_creation import (
    HrCaseCreationRequest,
    HrCaseCreationResult,
    HrCaseCreationService,
)
from infrastructure.persistence.teamworks_hr_case_creation_repository import (
    TeamworksHrCaseCreationRepository,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrCaseCreationRuntime:
    """Façade de création contrôlée sur la structure Teamworks active."""

    _structure_ref: str
    _service: HrCaseCreationService

    def create(
        self,
        request: HrCaseCreationRequest,
        *,
        actor_ref: str | None = None,
    ) -> HrCaseCreationResult:
        return self._service.create(
            structure_ref=self._structure_ref,
            request=request,
            actor_ref=actor_ref,
            source="teamworks-ui",
        )


class HrCaseCreationRuntimeFactory:
    """Compose CRH-29 sans exposer GestionDB ou l'identité de structure à l'UI."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        now_provider: Callable[[], datetime] | None = None,
        case_id_factory: Callable[[], str] | None = None,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._db_factory = db_factory
        self._now_provider = now_provider
        self._case_id_factory = case_id_factory
        self._event_id_factory = event_id_factory

    def create(self) -> HrCaseCreationRuntime:
        structure_ref = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        ).get_or_create_structure_ref()
        repository = TeamworksHrCaseCreationRepository(
            db_factory=self._db_factory,
        )
        profiles = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        service = HrCaseCreationService(
            repository=repository,
            profile_repository=profiles,
            now_provider=self._now_provider,
            case_id_factory=self._case_id_factory,
            event_id_factory=self._event_id_factory,
        )
        return HrCaseCreationRuntime(
            _structure_ref=structure_ref,
            _service=service,
        )
