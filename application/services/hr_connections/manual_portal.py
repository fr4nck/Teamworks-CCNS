from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Tuple

from domain.hr_connections import (
    ConfigurationCheck,
    ConnectionProfile,
    ConnectorCapability,
    ConnectorDescriptor,
    ConnectorMode,
    ConnectorState,
    ExpectedDocument,
    HrAuditEvent,
    HrAuditField,
    HrCase,
    HrCaseStatus,
    HrEventKind,
    HrEventTargetKind,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)


@dataclass(frozen=True)
class ManualPortalPlan:
    """Données préparées pour une démarche effectuée manuellement sur un portail.

    Le plan ne déclenche aucune ouverture de navigateur et n'effectue aucun échange.
    Il rassemble seulement les liens, références et pièces déjà connues de Teamworks.
    """

    connector_id: str
    case_id: str
    organization_code: str
    portal_links: Tuple[PortalLink, ...]
    references: Tuple[OrganizationReference, ...]
    required_documents: Tuple[ExpectedDocument, ...]
    optional_documents: Tuple[ExpectedDocument, ...]


@dataclass(frozen=True)
class PortalOpenRequest:
    """Demande explicite d'ouverture d'un portail à exécuter par la couche UI."""

    connector_id: str
    organization_code: str
    portal_link: PortalLink


@dataclass(frozen=True)
class ManualStatusUpdate:
    """Résultat pur d'une mise à jour de statut déclarée manuellement par l'utilisateur."""

    updated_case: HrCase
    external_reference: str | None
    audit_event: HrAuditEvent


class ManualPortalConnector:
    """Connecteur de repli pour les organismes accessibles uniquement par portail.

    Ce connecteur ne sait pas ouvrir un navigateur, ne transmet rien et ne prétend
    jamais qu'une démarche a été acceptée automatiquement. Il prépare les données
    nécessaires et produit des intentions explicites que l'interface pourra exécuter.
    """

    def __init__(
        self,
        *,
        connector_id: str = "manual_portal",
        version: str = "1",
        organization_kinds: Iterable[OrganizationKind] = tuple(OrganizationKind),
        state: ConnectorState = ConnectorState.AVAILABLE,
    ) -> None:
        self._descriptor = ConnectorDescriptor.create(
            connector_id=connector_id,
            organization_kinds=organization_kinds,
            capabilities=(
                ConnectorCapability.DEEP_LINK,
                ConnectorCapability.MANUAL_STATUS,
            ),
            version=version,
            modes=(ConnectorMode.MANUAL,),
            state=state,
        )

    @property
    def descriptor(self) -> ConnectorDescriptor:
        return self._descriptor

    def check_configuration(
        self,
        profile: ConnectionProfile | None,
    ) -> ConfigurationCheck:
        if profile is None:
            return ConfigurationCheck.missing(
                "Aucun profil d'organisme n'est configuré pour ce connecteur."
            )
        if not self.descriptor.targets(profile.organization.kind):
            return ConfigurationCheck.missing(
                "Le connecteur manuel ne cible pas cette famille d'organismes."
            )
        if not profile.portal_links:
            return ConfigurationCheck.missing(
                "Aucun portail n'est configuré pour cet organisme."
            )
        return ConfigurationCheck.ok()

    def prepare_case(
        self,
        *,
        case: HrCase,
        profile: ConnectionProfile,
    ) -> ManualPortalPlan:
        self._validate_case_profile(case=case, profile=profile)
        check = self.check_configuration(profile)
        if not check.configured:
            raise ValueError("Le connecteur manuel n'est pas correctement configuré.")

        required_documents = tuple(
            sorted(
                (item for item in case.expected_documents if item.required),
                key=lambda item: item.code,
            )
        )
        optional_documents = tuple(
            sorted(
                (item for item in case.expected_documents if not item.required),
                key=lambda item: item.code,
            )
        )
        return ManualPortalPlan(
            connector_id=self.descriptor.connector_id,
            case_id=case.case_id,
            organization_code=profile.organization.code,
            portal_links=profile.portal_links,
            references=profile.references,
            required_documents=required_documents,
            optional_documents=optional_documents,
        )

    def request_portal_open(
        self,
        *,
        profile: ConnectionProfile,
        user_confirmed: bool,
        portal_index: int = 0,
    ) -> PortalOpenRequest:
        """Prépare une ouverture uniquement après action explicite de l'utilisateur.

        La méthode retourne une intention. L'ouverture réelle du navigateur appartient
        à l'interface ou à un adaptateur de plateforme ultérieur.
        """

        if user_confirmed is not True:
            raise PermissionError("L'ouverture du portail exige une action utilisateur explicite.")
        check = self.check_configuration(profile)
        if not check.configured:
            raise ValueError("Le connecteur manuel n'est pas correctement configuré.")
        if not isinstance(portal_index, int) or isinstance(portal_index, bool):
            raise TypeError("L'index du portail est invalide.")
        try:
            portal_link = profile.portal_links[portal_index]
        except IndexError as exc:
            raise IndexError("Le portail demandé n'existe pas dans ce profil.") from exc

        return PortalOpenRequest(
            connector_id=self.descriptor.connector_id,
            organization_code=profile.organization.code,
            portal_link=portal_link,
        )

    def record_manual_status(
        self,
        *,
        case: HrCase,
        new_status: HrCaseStatus,
        event_id: str,
        occurred_at: datetime,
        actor_ref: str,
        external_reference: str | None = None,
        comment: str | None = None,
    ) -> ManualStatusUpdate:
        """Enregistre une déclaration utilisateur sans simuler de transmission externe."""

        if not actor_ref.strip():
            raise ValueError("L'auteur de la mise à jour manuelle est obligatoire.")
        normalized_reference = (
            external_reference.strip() if external_reference is not None else None
        )
        normalized_reference = normalized_reference or None

        updated_case = case.transition_to(new_status, comment=comment)
        fields = [
            HrAuditField.create(key="previous_status", value=case.status.value),
            HrAuditField.create(key="new_status", value=updated_case.status.value),
        ]
        if normalized_reference is not None:
            fields.append(
                HrAuditField.create(
                    key="external_reference",
                    value=normalized_reference,
                )
            )

        audit_event = HrAuditEvent.create(
            event_id=event_id,
            kind=HrEventKind.CASE_STATUS_CHANGED,
            target_kind=HrEventTargetKind.CASE,
            target_ref=case.case_id,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            source=self.descriptor.connector_id,
            fields=fields,
        )
        return ManualStatusUpdate(
            updated_case=updated_case,
            external_reference=normalized_reference,
            audit_event=audit_event,
        )

    def _validate_case_profile(
        self,
        *,
        case: HrCase,
        profile: ConnectionProfile,
    ) -> None:
        if not isinstance(case, HrCase):
            raise TypeError("Le dossier RH à préparer est invalide.")
        if not isinstance(profile, ConnectionProfile):
            raise TypeError("Le profil d'organisme à utiliser est invalide.")
        if case.organization_code != profile.organization.code:
            raise ValueError(
                "Le dossier RH et le profil de connexion ne ciblent pas le même organisme."
            )
        if not self.descriptor.targets(profile.organization.kind):
            raise ValueError("Le connecteur manuel ne cible pas cette famille d'organismes.")
