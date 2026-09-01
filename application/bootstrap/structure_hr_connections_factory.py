from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

from application.services.hr_connections import (
    OrganizationConfigurationView,
    StructureHrConnectionsService,
    build_reference_connector_registry,
    reference_manual_connector_specs,
)
from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class StructureOrganizationProfileRequest:
    """Données non secrètes saisissables pour un organisme RH de la structure."""

    code: str
    label: str
    kind: OrganizationKind
    references: tuple[OrganizationReference, ...] = ()
    portal_links: tuple[PortalLink, ...] = ()
    starts_on: date | None = None
    ends_on: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("Le code interne de l'organisme est obligatoire.")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("Le nom de l'organisme est obligatoire.")
        if not isinstance(self.kind, OrganizationKind):
            raise TypeError("La famille d'organisme est invalide.")
        if self.kind is OrganizationKind.OTHER:
            raise ValueError("La famille 'autre' n'a pas encore de connecteur de référence.")
        if any(not isinstance(item, OrganizationReference) for item in self.references):
            raise TypeError("Une référence d'organisme est invalide.")
        if any(not isinstance(item, PortalLink) for item in self.portal_links):
            raise TypeError("Un lien de portail est invalide.")
        for value, label in (
            (self.starts_on, "date d'effet"),
            (self.ends_on, "date de fin"),
        ):
            if value is not None and not isinstance(value, date):
                raise TypeError("La %s est invalide." % label)
        EffectivePeriod(starts_on=self.starts_on, ends_on=self.ends_on)


@dataclass(frozen=True)
class StructureHrConnectionsRuntime:
    """Façade de configuration verrouillée sur la structure Teamworks active."""

    structure_ref: str
    _service: StructureHrConnectionsService
    _supported_kinds: tuple[OrganizationKind, ...]

    def supported_kinds(self) -> tuple[OrganizationKind, ...]:
        return self._supported_kinds

    def list_configurations(self) -> tuple[OrganizationConfigurationView, ...]:
        return self._service.list_configurations(structure_ref=self.structure_ref)

    def get_configuration(
        self,
        *,
        organization_code: str,
    ) -> OrganizationConfigurationView | None:
        if not isinstance(organization_code, str):
            raise TypeError("Le code de l'organisme est invalide.")
        organization_code = organization_code.strip()
        if not organization_code:
            raise ValueError("Le code de l'organisme est obligatoire.")
        return self._service.get_configuration(
            structure_ref=self.structure_ref,
            organization_code=organization_code,
        )

    def save_configuration(
        self,
        request: StructureOrganizationProfileRequest,
    ) -> OrganizationConfigurationView:
        if not isinstance(request, StructureOrganizationProfileRequest):
            raise TypeError("La demande de configuration d'organisme est invalide.")
        if request.kind not in self._supported_kinds:
            raise ValueError("Cette famille d'organisme n'est pas prise en charge.")

        connector_options = self._service.connector_options(
            organization_kind=request.kind,
        )
        capabilities = {
            capability
            for connector in connector_options
            for capability in connector.capabilities
        }
        period = (
            EffectivePeriod(starts_on=request.starts_on, ends_on=request.ends_on)
            if request.starts_on is not None or request.ends_on is not None
            else None
        )
        profile = ConnectionProfile.create(
            structure_ref=self.structure_ref,
            organization=HrOrganization.create(
                code=request.code,
                label=request.label,
                kind=request.kind,
            ),
            capabilities=capabilities,
            references=request.references,
            portal_links=request.portal_links,
            effective_period=period,
        )
        return self._service.save_profile(profile)


class StructureHrConnectionsRuntimeFactory:
    """Compose la configuration Connexions RH sur la base Teamworks active."""

    def __init__(self, *, db_factory: Callable[[], object] | None = None) -> None:
        self._db_factory = db_factory

    def create(self) -> StructureHrConnectionsRuntime:
        identity_repository = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        )
        structure_ref = identity_repository.get_or_create_structure_ref()
        repository = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        registry = build_reference_connector_registry()
        service = StructureHrConnectionsService(
            repository=repository,
            registry=registry,
        )
        supported_kinds = _unique_kinds(
            spec.organization_kind for spec in reference_manual_connector_specs()
        )
        return StructureHrConnectionsRuntime(
            structure_ref=structure_ref,
            _service=service,
            _supported_kinds=supported_kinds,
        )


def _unique_kinds(kinds: Iterable[OrganizationKind]) -> tuple[OrganizationKind, ...]:
    seen = set()
    result = []
    for kind in kinds:
        if kind not in seen:
            seen.add(kind)
            result.append(kind)
    return tuple(result)
