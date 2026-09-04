from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Tuple

from .capabilities import ConnectorCapability
from .organizations import (
    EffectivePeriod,
    HrOrganization,
    OrganizationReference,
    PortalLink,
)


@dataclass(frozen=True)
class ConnectionProfile:
    """Configuration métier non secrète d'un organisme pour une structure."""

    structure_ref: str
    organization: HrOrganization
    capabilities: FrozenSet[ConnectorCapability] = field(default_factory=frozenset)
    references: Tuple[OrganizationReference, ...] = ()
    portal_links: Tuple[PortalLink, ...] = ()
    effective_period: EffectivePeriod | None = None

    def __post_init__(self) -> None:
        if not self.structure_ref.strip():
            raise ValueError("La référence de structure est obligatoire.")
        if not isinstance(self.organization, HrOrganization):
            raise TypeError("L'organisme du profil est invalide.")
        if any(not isinstance(item, ConnectorCapability) for item in self.capabilities):
            raise TypeError("Une capacité déclarée est invalide.")
        if any(not isinstance(item, OrganizationReference) for item in self.references):
            raise TypeError("Une référence d'organisme est invalide.")
        if any(not isinstance(item, PortalLink) for item in self.portal_links):
            raise TypeError("Un lien de portail est invalide.")

    @classmethod
    def create(
        cls,
        *,
        structure_ref: str,
        organization: HrOrganization,
        capabilities: Iterable[ConnectorCapability] = (),
        references: Iterable[OrganizationReference] = (),
        portal_links: Iterable[PortalLink] = (),
        effective_period: EffectivePeriod | None = None,
    ) -> "ConnectionProfile":
        return cls(
            structure_ref=structure_ref.strip(),
            organization=organization,
            capabilities=frozenset(capabilities),
            references=tuple(references),
            portal_links=tuple(portal_links),
            effective_period=effective_period,
        )

    def supports(self, capability: ConnectorCapability) -> bool:
        return capability in self.capabilities
