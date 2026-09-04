from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from application.services.hr_connections import HrLifecyclePlan, HrLifecyclePlanningService
from domain.hr_connections import HrLifecycleEvent
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_hr_lifecycle_template_repository import (
    TeamworksHrLifecycleTemplateRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrLifecyclePlanningRuntime:
    """Façade de planification sur la structure Teamworks active."""

    _structure_ref: str
    _service: HrLifecyclePlanningService

    def plan(self, *, event: HrLifecycleEvent) -> HrLifecyclePlan:
        if not isinstance(event, HrLifecycleEvent):
            raise TypeError("L'événement de cycle de vie RH est invalide.")
        return self._service.plan(structure_ref=self._structure_ref, event=event)


class HrLifecyclePlanningRuntimeFactory:
    """Compose identité stable, modèles locaux et organismes configurés."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_factory = db_factory

    def create(self) -> HrLifecyclePlanningRuntime:
        identity_repository = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        )
        structure_ref = identity_repository.get_or_create_structure_ref()
        template_repository = TeamworksHrLifecycleTemplateRepository(
            db_factory=self._db_factory,
        )
        profile_repository = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        service = HrLifecyclePlanningService(
            template_repository=template_repository,
            profile_repository=profile_repository,
        )
        return HrLifecyclePlanningRuntime(
            _structure_ref=structure_ref,
            _service=service,
        )
