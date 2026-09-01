from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from domain.hr_connections import ConnectorRegistry, OrganizationKind

from .manual_portal import ManualPortalConnector


@dataclass(frozen=True)
class ReferenceManualConnectorSpec:
    """Spécification stable d'un connecteur manuel de référence."""

    connector_id: str
    label: str
    organization_kind: OrganizationKind

    def __post_init__(self) -> None:
        if not self.connector_id.strip():
            raise ValueError("L'identifiant du connecteur de référence est obligatoire.")
        if not self.label.strip():
            raise ValueError("Le libellé du connecteur de référence est obligatoire.")
        if not isinstance(self.organization_kind, OrganizationKind):
            raise TypeError("La famille d'organisme du connecteur de référence est invalide.")
        if self.organization_kind is OrganizationKind.OTHER:
            raise ValueError("Un connecteur de référence doit cibler une famille d'organismes connue.")


_REFERENCE_MANUAL_CONNECTOR_SPECS: Tuple[ReferenceManualConnectorSpec, ...] = (
    ReferenceManualConnectorSpec(
        connector_id="urssaf_manual_portal",
        label="URSSAF — portail manuel",
        organization_kind=OrganizationKind.URSSAF,
    ),
    ReferenceManualConnectorSpec(
        connector_id="net_entreprises_manual_portal",
        label="Net-entreprises — portail manuel",
        organization_kind=OrganizationKind.NET_ENTREPRISES,
    ),
    ReferenceManualConnectorSpec(
        connector_id="mutuelle_manual_portal",
        label="Mutuelle — portail manuel",
        organization_kind=OrganizationKind.MUTUELLE,
    ),
    ReferenceManualConnectorSpec(
        connector_id="prevoyance_manual_portal",
        label="Prévoyance — portail manuel",
        organization_kind=OrganizationKind.PREVOYANCE,
    ),
    ReferenceManualConnectorSpec(
        connector_id="retraite_complementaire_manual_portal",
        label="Retraite complémentaire — portail manuel",
        organization_kind=OrganizationKind.RETRAITE_COMPLEMENTAIRE,
    ),
    ReferenceManualConnectorSpec(
        connector_id="opco_manual_portal",
        label="OPCO — portail manuel",
        organization_kind=OrganizationKind.OPCO,
    ),
    ReferenceManualConnectorSpec(
        connector_id="spst_manual_portal",
        label="SPST / service de prévention — portail manuel",
        organization_kind=OrganizationKind.SPST,
    ),
    ReferenceManualConnectorSpec(
        connector_id="france_travail_manual_portal",
        label="France Travail — portail manuel",
        organization_kind=OrganizationKind.FRANCE_TRAVAIL,
    ),
)


def reference_manual_connector_specs() -> Tuple[ReferenceManualConnectorSpec, ...]:
    """Retourne le catalogue immuable des familles actuellement prévues."""

    return _REFERENCE_MANUAL_CONNECTOR_SPECS


def build_reference_manual_connectors() -> Tuple[ManualPortalConnector, ...]:
    """Construit les connecteurs de référence sans authentification ni réseau."""

    return tuple(
        ManualPortalConnector(
            connector_id=spec.connector_id,
            version="1",
            organization_kinds=(spec.organization_kind,),
        )
        for spec in _REFERENCE_MANUAL_CONNECTOR_SPECS
    )


def build_reference_connector_registry() -> ConnectorRegistry:
    """Construit un registre prêt à être consommé par la couche applicative."""

    return ConnectorRegistry(build_reference_manual_connectors())
