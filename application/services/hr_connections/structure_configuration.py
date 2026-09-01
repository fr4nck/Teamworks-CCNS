from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple

from domain.hr_connections import (
    ConfigurationCheck,
    ConnectionProfile,
    ConnectorCapability,
    ConnectorMode,
    ConnectorRegistry,
    ConnectorState,
    OrganizationKind,
)


class ConnectionProfileRepository(Protocol):
    """Port applicatif minimal pour la configuration des organismes d'une structure."""

    def save_profile(self, profile: ConnectionProfile) -> ConnectionProfile:
        ...

    def get_profile(
        self,
        *,
        structure_ref: str,
        organization_code: str,
    ) -> ConnectionProfile | None:
        ...

    def list_profiles(self, *, structure_ref: str) -> tuple[ConnectionProfile, ...]:
        ...


@dataclass(frozen=True)
class ConnectorConfigurationView:
    """Projection UI-agnostique de l'état local d'un connecteur."""

    connector_id: str
    state: ConnectorState
    modes: Tuple[ConnectorMode, ...]
    capabilities: Tuple[ConnectorCapability, ...]
    configured: bool
    messages: Tuple[str, ...]


@dataclass(frozen=True)
class OrganizationConfigurationView:
    """Projection complète d'un organisme configuré pour une structure."""

    profile: ConnectionProfile
    connectors: Tuple[ConnectorConfigurationView, ...]

    @property
    def has_configured_connector(self) -> bool:
        return any(item.configured for item in self.connectors)


class StructureHrConnectionsService:
    """Cas d'usage de configuration des organismes RH d'une structure.

    Ce service ne dépend ni de wxPython ni d'un backend particulier. Il prépare les
    données nécessaires au futur écran « Organismes & connexions RH » et délègue les
    vérifications locales au registre CRH-02. Aucune vérification réseau n'est lancée.
    """

    def __init__(
        self,
        *,
        repository: ConnectionProfileRepository,
        registry: ConnectorRegistry,
    ) -> None:
        self._repository = repository
        self._registry = registry

    def save_profile(self, profile: ConnectionProfile) -> OrganizationConfigurationView:
        if not isinstance(profile, ConnectionProfile):
            raise TypeError("Le profil de connexion à enregistrer est invalide.")
        saved = self._repository.save_profile(profile)
        return self.inspect_profile(saved)

    def get_configuration(
        self,
        *,
        structure_ref: str,
        organization_code: str,
    ) -> OrganizationConfigurationView | None:
        profile = self._repository.get_profile(
            structure_ref=structure_ref,
            organization_code=organization_code,
        )
        if profile is None:
            return None
        return self.inspect_profile(profile)

    def list_configurations(
        self,
        *,
        structure_ref: str,
    ) -> tuple[OrganizationConfigurationView, ...]:
        return tuple(
            self.inspect_profile(profile)
            for profile in self._repository.list_profiles(structure_ref=structure_ref)
        )

    def connector_options(
        self,
        *,
        organization_kind: OrganizationKind,
    ) -> tuple[ConnectorConfigurationView, ...]:
        if not isinstance(organization_kind, OrganizationKind):
            raise TypeError("La famille d'organisme est invalide.")
        return tuple(
            self._view(connector, ConfigurationCheck.missing("Profil non encore configuré."))
            for connector in self._registry.find(organization_kind=organization_kind)
        )

    def inspect_profile(self, profile: ConnectionProfile) -> OrganizationConfigurationView:
        if not isinstance(profile, ConnectionProfile):
            raise TypeError("Le profil de connexion à inspecter est invalide.")
        connector_views = []
        for connector in self._registry.find(
            organization_kind=profile.organization.kind,
        ):
            check = self._registry.check_configuration(
                connector.descriptor.connector_id,
                profile,
            )
            connector_views.append(self._view(connector, check))
        return OrganizationConfigurationView(
            profile=profile,
            connectors=tuple(connector_views),
        )

    @staticmethod
    def _view(connector, check: ConfigurationCheck) -> ConnectorConfigurationView:
        descriptor = connector.descriptor
        return ConnectorConfigurationView(
            connector_id=descriptor.connector_id,
            state=descriptor.state,
            modes=tuple(sorted(descriptor.modes, key=lambda item: item.value)),
            capabilities=tuple(
                sorted(descriptor.capabilities, key=lambda item: item.value)
            ),
            configured=check.configured,
            messages=check.messages,
        )
