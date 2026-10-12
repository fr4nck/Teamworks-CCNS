from __future__ import annotations

from typing import Dict, Iterable, Tuple

from .capabilities import ConnectorCapability, ConnectorState
from .connector import ConfigurationCheck, HrConnector
from .organizations import OrganizationKind
from .profiles import ConnectionProfile


class ConnectorRegistry:
    """Registre en mémoire des connecteurs RH disponibles.

    Le registre n'instancie aucun adaptateur lui-même et n'effectue aucun accès
    réseau. Les connecteurs sont enregistrés explicitement par la couche
    applicative ou d'infrastructure.
    """

    def __init__(self, connectors: Iterable[HrConnector] = ()) -> None:
        self._connectors: Dict[str, HrConnector] = {}
        for connector in connectors:
            self.register(connector)

    def register(self, connector: HrConnector) -> None:
        connector_id = connector.descriptor.connector_id
        if connector_id in self._connectors:
            raise ValueError(f"Le connecteur '{connector_id}' est déjà enregistré.")
        self._connectors[connector_id] = connector

    def get(self, connector_id: str) -> HrConnector:
        key = connector_id.strip()
        if not key:
            raise ValueError("L'identifiant du connecteur est obligatoire.")
        try:
            return self._connectors[key]
        except KeyError as exc:
            raise KeyError(f"Connecteur inconnu : {key}") from exc

    def all(self) -> Tuple[HrConnector, ...]:
        return tuple(self._connectors[key] for key in sorted(self._connectors))

    def find(
        self,
        *,
        organization_kind: OrganizationKind | None = None,
        capability: ConnectorCapability | None = None,
        states: Iterable[ConnectorState] | None = None,
    ) -> Tuple[HrConnector, ...]:
        allowed_states = frozenset(states) if states is not None else None
        matches = []

        for connector in self.all():
            descriptor = connector.descriptor
            if organization_kind is not None and not descriptor.targets(organization_kind):
                continue
            if capability is not None and not descriptor.supports(capability):
                continue
            if allowed_states is not None and descriptor.state not in allowed_states:
                continue
            matches.append(connector)

        return tuple(matches)

    def check_configuration(
        self,
        connector_id: str,
        profile: ConnectionProfile | None,
    ) -> ConfigurationCheck:
        """Déclenche explicitement la vérification locale d'un connecteur."""

        return self.get(connector_id).check_configuration(profile)
