from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

from application.services.hr_connections import (
    HrCaseDocumentChecklist,
    HrCaseDocumentTrackingResult,
    HrCaseDocumentTrackingService,
)
from infrastructure.persistence.teamworks_hr_case_document_repository import (
    TeamworksHrCaseDocumentRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrCaseDocumentTrackingRuntime:
    """Façade du suivi des pièces sur la structure Teamworks active."""

    _structure_ref: str
    _service: HrCaseDocumentTrackingService

    def build_checklist(self, *, case_id: str) -> HrCaseDocumentChecklist:
        return self._service.build_checklist(
            structure_ref=self._structure_ref,
            case_id=case_id,
        )

    def record_received(
        self,
        *,
        case_id: str,
        document_code: str,
        received_on: date,
        artifact_ref: str | None = None,
        actor_ref: str | None = None,
    ) -> HrCaseDocumentTrackingResult:
        return self._service.record_received(
            structure_ref=self._structure_ref,
            case_id=case_id,
            document_code=document_code,
            received_on=received_on,
            artifact_ref=artifact_ref,
            actor_ref=actor_ref,
            source="teamworks-ui",
        )

    def withdraw_received(
        self,
        *,
        case_id: str,
        document_code: str,
        withdrawn_on: date,
        actor_ref: str | None = None,
    ) -> HrCaseDocumentTrackingResult:
        return self._service.withdraw_received(
            structure_ref=self._structure_ref,
            case_id=case_id,
            document_code=document_code,
            withdrawn_on=withdrawn_on,
            actor_ref=actor_ref,
            source="teamworks-ui",
        )


class HrCaseDocumentTrackingRuntimeFactory:
    """Compose CRH-31 sans exposer la base ou l'identité de structure à l'UI."""

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

    def create(self) -> HrCaseDocumentTrackingRuntime:
        structure_ref = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        ).get_or_create_structure_ref()
        repository = TeamworksHrCaseDocumentRepository(
            db_factory=self._db_factory,
        )
        service = HrCaseDocumentTrackingService(
            repository=repository,
            now_provider=self._now_provider,
            event_id_factory=self._event_id_factory,
        )
        return HrCaseDocumentTrackingRuntime(
            _structure_ref=structure_ref,
            _service=service,
        )
