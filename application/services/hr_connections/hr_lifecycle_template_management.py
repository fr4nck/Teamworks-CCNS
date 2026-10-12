from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from domain.hr_connections import (
    ExpectedDocument,
    HrCaseType,
    HrLifecycleEventKind,
    HrLifecycleTemplate,
)

from .structure_configuration import ConnectionProfileRepository


class HrLifecycleTemplateManagementRepository(Protocol):
    """Port de gestion des modèles locaux de cycle de vie RH."""

    def get_template(
        self,
        *,
        structure_ref: str,
        template_id: str,
    ) -> HrLifecycleTemplate | None:
        ...

    def list_all_templates(
        self,
        *,
        structure_ref: str,
    ) -> tuple[HrLifecycleTemplate, ...]:
        ...

    def save_template(
        self,
        *,
        structure_ref: str,
        template: HrLifecycleTemplate,
    ) -> HrLifecycleTemplate:
        ...


@dataclass(frozen=True)
class HrLifecycleTemplateRequest:
    """Configuration explicitement saisie par la structure.

    Aucun type de démarche, délai ou document n'est déduit par ce cas d'usage.
    """

    template_id: str
    event_kind: HrLifecycleEventKind
    organization_code: str
    case_type_code: str
    case_type_label: str
    due_offset_days: int | None = None
    expected_documents: tuple[ExpectedDocument, ...] = ()
    enabled: bool = True

    def to_template(self) -> HrLifecycleTemplate:
        return HrLifecycleTemplate.create(
            template_id=self.template_id,
            event_kind=self.event_kind,
            organization_code=self.organization_code,
            case_type=HrCaseType.create(
                code=self.case_type_code,
                label=self.case_type_label,
            ),
            due_offset_days=self.due_offset_days,
            expected_documents=self.expected_documents,
            enabled=self.enabled,
        )


class HrLifecycleTemplateManagementService:
    """Gère les modèles locaux sans embarquer de catalogue réglementaire.

    L'organisme doit avoir été configuré explicitement dans Connexions RH. Un modèle
    n'est jamais supprimé : la sortie d'usage passe par ``enabled=False`` afin de
    conserver la configuration et de préparer une traçabilité stable.
    """

    def __init__(
        self,
        *,
        repository: HrLifecycleTemplateManagementRepository,
        profile_repository: ConnectionProfileRepository,
    ) -> None:
        self._repository = repository
        self._profile_repository = profile_repository

    def list_templates(self, *, structure_ref: str) -> tuple[HrLifecycleTemplate, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        templates = self._repository.list_all_templates(structure_ref=structure_ref)
        if any(not isinstance(item, HrLifecycleTemplate) for item in templates):
            raise TypeError("Le repository a retourné un modèle de cycle de vie RH invalide.")
        ids = [item.template_id for item in templates]
        if len(ids) != len(set(ids)):
            raise ValueError("Le repository a retourné plusieurs modèles RH avec le même identifiant.")
        return tuple(templates)

    def save(
        self,
        *,
        structure_ref: str,
        request: HrLifecycleTemplateRequest,
    ) -> HrLifecycleTemplate:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(request, HrLifecycleTemplateRequest):
            raise TypeError("La demande de configuration du modèle RH est invalide.")
        template = request.to_template()
        self._require_configured_organization(
            structure_ref=structure_ref,
            organization_code=template.organization_code,
        )
        return self._repository.save_template(
            structure_ref=structure_ref,
            template=template,
        )

    def disable(
        self,
        *,
        structure_ref: str,
        template_id: str,
    ) -> HrLifecycleTemplate:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        template_id = _required_text(
            template_id,
            "L'identifiant du modèle RH est obligatoire.",
        )
        current = self._repository.get_template(
            structure_ref=structure_ref,
            template_id=template_id,
        )
        if current is None:
            raise LookupError("Le modèle de cycle de vie RH demandé est introuvable.")
        if not isinstance(current, HrLifecycleTemplate):
            raise TypeError("Le repository a retourné un modèle de cycle de vie RH invalide.")
        if not current.enabled:
            return current
        disabled = HrLifecycleTemplate.create(
            template_id=current.template_id,
            event_kind=current.event_kind,
            organization_code=current.organization_code,
            case_type=current.case_type,
            due_offset_days=current.due_offset_days,
            expected_documents=current.expected_documents,
            enabled=False,
        )
        return self._repository.save_template(
            structure_ref=structure_ref,
            template=disabled,
        )

    def _require_configured_organization(
        self,
        *,
        structure_ref: str,
        organization_code: str,
    ) -> None:
        profile = self._profile_repository.get_profile(
            structure_ref=structure_ref,
            organization_code=organization_code,
        )
        if profile is None:
            raise LookupError(
                "L'organisme doit être configuré dans « Organismes & connexions RH » "
                "avant d'être utilisé dans un modèle de cycle de vie."
            )


def _required_text(value, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    value = value.strip()
    if not value:
        raise ValueError(message)
    return value
