from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from application.services.hr_connections import (
    OrganizationConfigurationView,
    StructureConnectionProfileRequest,
    StructureHrConnectionsService,
    build_reference_connector_registry,
)
from domain.hr_connections import OrganizationKind
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class StructureHrConnectionsRuntime:
    """Façade de configuration des organismes de la structure active."""

    structure_ref: str
    _service: StructureHrConnectionsService

    def list_configurations(self) -> tuple[OrganizationConfigurationView, ...]:
        return self._service.list_configurations(structure_ref=self.structure_ref)

    def get_configuration(
        self,
        organization_code: str,
    ) -> OrganizationConfigurationView | None:
        return self._service.get_configuration(
            structure_ref=self.structure_ref,
            organization_code=organization_code,
        )

    def connector_options(self, organization_kind: OrganizationKind):
        return self._service.connector_options(organization_kind=organization_kind)

    def save_profile(
        self,
        request: StructureConnectionProfileRequest,
    ) -> OrganizationConfigurationView:
        if not isinstance(request, StructureConnectionProfileRequest):
            raise TypeError("La demande de configuration de l'organisme est invalide.")

        existing = self.get_configuration(request.organization_code)
        if (
            existing is not None
            and existing.profile.organization.kind is not request.organization_kind
        ):
            raise ValueError(
                "La famille d'un organisme déjà enregistré ne peut pas être modifiée. "
                "Créez un nouvel organisme afin de préserver les historiques salariés."
            )

        # Une modification effectuée depuis l'écran CRH-10B ne doit ni inventer
        # ni effacer les capacités qu'un autre lot a explicitement qualifiées.
        capabilities = (
            existing.profile.capabilities
            if existing is not None
            else ()
        )
        profile = request.to_profile(
            structure_ref=self.structure_ref,
            capabilities=capabilities,
        )
        return self._service.save_profile(profile)


class StructureHrConnectionsRuntimeFactory:
    """Compose CRH-10A/10B sur la base Teamworks active via GestionDB."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_factory = db_factory

    def create(self) -> StructureHrConnectionsRuntime:
        identity_repository = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        )
        structure_ref = identity_repository.get_or_create_structure_ref()
        repository = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        service = StructureHrConnectionsService(
            repository=repository,
            registry=build_reference_connector_registry(),
        )
        return StructureHrConnectionsRuntime(
            structure_ref=structure_ref,
            _service=service,
        )
