from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from application.services.hr_connections.hr_lifecycle_template_management import (
    HrLifecycleTemplateManagementService,
    HrLifecycleTemplateRequest,
)
from domain.hr_connections import HrLifecycleTemplate
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
class HrLifecycleOrganizationOption:
    code: str
    label: str


@dataclass(frozen=True)
class HrLifecycleTemplateManagementRuntime:
    """Façade de configuration qui masque identité de structure et repositories."""

    _structure_ref: str
    _service: HrLifecycleTemplateManagementService
    _profile_repository: TeamworksHrConnectionsRepository

    def list_templates(self) -> tuple[HrLifecycleTemplate, ...]:
        return self._service.list_templates(structure_ref=self._structure_ref)

    def list_organizations(self) -> tuple[HrLifecycleOrganizationOption, ...]:
        profiles = self._profile_repository.list_profiles(structure_ref=self._structure_ref)
        options = tuple(
            HrLifecycleOrganizationOption(
                code=profile.organization.code,
                label=profile.organization.label,
            )
            for profile in profiles
            if profile.structure_ref == self._structure_ref
        )
        return tuple(sorted(options, key=lambda item: (item.label.casefold(), item.code.casefold())))

    def save(self, request: HrLifecycleTemplateRequest) -> HrLifecycleTemplate:
        return self._service.save(
            structure_ref=self._structure_ref,
            request=request,
        )

    def disable(self, template_id: str) -> HrLifecycleTemplate:
        return self._service.disable(
            structure_ref=self._structure_ref,
            template_id=template_id,
        )


class HrLifecycleTemplateManagementRuntimeFactory:
    """Compose la gestion explicite des modèles sur la base Teamworks active."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_factory = db_factory

    def create(self) -> HrLifecycleTemplateManagementRuntime:
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
        service = HrLifecycleTemplateManagementService(
            repository=template_repository,
            profile_repository=profile_repository,
        )
        return HrLifecycleTemplateManagementRuntime(
            _structure_ref=structure_ref,
            _service=service,
            _profile_repository=profile_repository,
        )
