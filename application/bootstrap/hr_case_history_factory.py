from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from application.services.hr_connections import HrCaseHistory, HrCaseHistoryService
from infrastructure.persistence.teamworks_hr_cases_repository import (
    TeamworksHrCasesRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrCaseHistoryRuntime:
    """Façade de lecture du journal d'une démarche dans la base active."""

    _structure_ref: str
    _service: HrCaseHistoryService

    def build(self, *, case_id: str) -> HrCaseHistory:
        return self._service.build(
            structure_ref=self._structure_ref,
            case_id=case_id,
        )


class HrCaseHistoryRuntimeFactory:
    """Compose l'historique CRH-27 sans exposer la persistance à wxPython."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_factory = db_factory

    def create(self) -> HrCaseHistoryRuntime:
        structure_ref = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        ).get_or_create_structure_ref()
        repository = TeamworksHrCasesRepository(
            db_factory=self._db_factory,
        )
        service = HrCaseHistoryService(repository=repository)
        return HrCaseHistoryRuntime(
            _structure_ref=structure_ref,
            _service=service,
        )
