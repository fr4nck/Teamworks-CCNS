from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Protocol, Tuple

from .capabilities import ConnectorCapability, ConnectorMode, ConnectorState
from .organizations import OrganizationKind
from .profiles import ConnectionProfile


@dataclass(frozen=True)
class ConnectorDescriptor:
    """Métadonnées déclaratives d'un connecteur RH."""

    connector_id: str
    organization_kinds: FrozenSet[OrganizationKind]
    capabilities: FrozenSet[ConnectorCapability]
    version: str
    modes: FrozenSet[ConnectorMode]
    state: ConnectorState = ConnectorState.NOT_CONFIGURED

    def __post_init__(self) -> None:
        if not self.connector_id.strip():
            raise ValueError("L'identifiant du connecteur est obligatoire.")
        if not self.version.strip():
            raise ValueError("La version du connecteur est obligatoire.")
        if not self.organization_kinds:
            raise ValueError("Un connecteur doit cibler au moins une famille d'organismes.")
        if not self.modes:
            raise ValueError("Un connecteur doit annoncer au moins un mode d'intégration.")
        if any(not isinstance(item, OrganizationKind) for item in self.organization_kinds):
            raise TypeError("Une famille d'organismes du connecteur est invalide.")
        if any(not isinstance(item, ConnectorCapability) for item in self.capabilities):
            raise TypeError("Une capacité du connecteur est invalide.")
        if any(not isinstance(item, ConnectorMode) for item in self.modes):
            raise TypeError("Un mode du connecteur est invalide.")
        if not isinstance(self.state, ConnectorState):
            raise TypeError("L'état du connecteur est invalide.")

    @classmethod
    def create(
        cls,
        *,
        connector_id: str,
        organization_kinds: Iterable[OrganizationKind],
        capabilities: Iterable[ConnectorCapability],
        version: str,
        modes: Iterable[ConnectorMode],
        state: ConnectorState = ConnectorState.NOT_CONFIGURED,
    ) -> "ConnectorDescriptor":
        return cls(
            connector_id=connector_id.strip(),
            organization_kinds=frozenset(organization_kinds),
            capabilities=frozenset(capabilities),
            version=version.strip(),
            modes=frozenset(modes),
            state=state,
        )

    def supports(self, capability: ConnectorCapability) -> bool:
        return capability in self.capabilities

    def targets(self, kind: OrganizationKind) -> bool:
        return kind in self.organization_kinds


@dataclass(frozen=True)
class ConfigurationCheck:
    """Résultat sans effet de bord d'une vérification de configuration."""

    configured: bool
    messages: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def ok(cls) -> "ConfigurationCheck":
        return cls(configured=True)

    @classmethod
    def missing(cls, *messages: str) -> "ConfigurationCheck":
        cleaned = tuple(message.strip() for message in messages if message.strip())
        return cls(configured=False, messages=cleaned)


class HrConnector(Protocol):
    """Contrat minimal d'un connecteur enregistré dans Teamworks.

    ``check_configuration`` doit uniquement inspecter la configuration locale qui lui
    est fournie. Il ne doit ni ouvrir un navigateur ni appeler un service externe.
    """

    @property
    def descriptor(self) -> ConnectorDescriptor:
        ...

    def check_configuration(
        self,
        profile: ConnectionProfile | None,
    ) -> ConfigurationCheck:
        ...
