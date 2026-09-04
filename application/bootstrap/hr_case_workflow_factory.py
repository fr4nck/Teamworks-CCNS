from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from application.services.hr_connections import (
    HrCaseTransitionOptions,
    HrCaseTransitionResult,
    HrCaseWorkflowService,
)
from domain.hr_connections import HrCaseStatus
from infrastructure.persistence.teamworks_hr_case_workflow_repository import (
    TeamworksHrCaseWorkflowRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrCaseWorkflowRuntime:
    """Façade de mutation contrôlée pour la base Teamworks active."""

    _structure_ref: str
    _service: HrCaseWorkflowService

    def available_transitions(self, *, case_id: str) -> HrCaseTransitionOptions:
        return self._service.available_transitions(
            structure_ref=self._structure_ref,
            case_id=case_id,
        )

    def transition(
        self,
        *,
        case_id: str,
        status: HrCaseStatus,
        actor_ref: str | None = None,
        result: str | None = None,
        comment: str | None = None,
    ) -> HrCaseTransitionResult:
        return self._service.transition(
            structure_ref=self._structure_ref,
            case_id=case_id,
            status=status,
            actor_ref=actor_ref,
            source="teamworks-ui",
            result=result,
            comment=comment,
        )


class HrCaseWorkflowRuntimeFactory:
    """Compose le workflow CRH-25 sans exposer l'identité de structure à l'UI."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        now_provider: Callable[[], datetime] | None = None,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._db_factory = db_factory
        self._now_provider = now_provider
        self._event_id_factory = event_id_factory

    def create(self) -> HrCaseWorkflowRuntime:
        structure_ref = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        ).get_or_create_structure_ref()
        repository = TeamworksHrCaseWorkflowRepository(
            db_factory=self._db_factory,
        )
        service = HrCaseWorkflowService(
            repository=repository,
            now_provider=self._now_provider,
            event_id_factory=self._event_id_factory,
        )
        return HrCaseWorkflowRuntime(
            _structure_ref=structure_ref,
            _service=service,
        )
