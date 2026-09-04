from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256
from typing import Protocol

from domain.hr_connections import (
    ExpectedDocument,
    HrCaseType,
    HrLifecycleEvent,
    HrLifecycleEventKind,
    HrLifecycleTemplate,
)

from .structure_configuration import ConnectionProfileRepository


class HrLifecycleTemplateRepository(Protocol):
    """Port de lecture des modèles explicitement configurés par structure."""

    def list_templates(
        self,
        *,
        structure_ref: str,
        event_kind: HrLifecycleEventKind,
    ) -> tuple[HrLifecycleTemplate, ...]:
        ...


@dataclass(frozen=True)
class HrLifecycleSuggestion:
    """Suggestion descriptive ; elle ne crée ni ne transmet aucune démarche."""

    suggestion_key: str
    lifecycle_event_id: str
    template_id: str
    person_ref: str
    event_kind: HrLifecycleEventKind
    organization_code: str
    organization_configured: bool
    case_type: HrCaseType
    opened_on: date
    due_on: date | None
    expected_documents: tuple[ExpectedDocument, ...]
    source_ref: str | None


@dataclass(frozen=True)
class HrLifecyclePlan:
    """Résultat de planification d'un fait RH à partir de règles locales explicites."""

    structure_ref: str
    event: HrLifecycleEvent
    suggestions: tuple[HrLifecycleSuggestion, ...]

    @property
    def suggestion_count(self) -> int:
        return len(self.suggestions)

    @property
    def unconfigured_organization_count(self) -> int:
        return sum(1 for item in self.suggestions if not item.organization_configured)


class HrLifecyclePlanningService:
    """Projette des suggestions sans inventer de règle réglementaire.

    Le service n'embarque aucun catalogue DPAE/DSN/France Travail, aucune échéance
    légale et aucune pièce obligatoire implicite. Sans modèle configuré, un événement
    de cycle de vie produit un plan vide. La matérialisation d'une suggestion en
    démarche RH restera un cas d'usage séparé avec confirmation explicite.
    """

    def __init__(
        self,
        *,
        template_repository: HrLifecycleTemplateRepository,
        profile_repository: ConnectionProfileRepository,
    ) -> None:
        self._template_repository = template_repository
        self._profile_repository = profile_repository

    def plan(
        self,
        *,
        structure_ref: str,
        event: HrLifecycleEvent,
    ) -> HrLifecyclePlan:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(event, HrLifecycleEvent):
            raise TypeError("L'événement de cycle de vie RH est invalide.")

        templates = self._template_repository.list_templates(
            structure_ref=structure_ref,
            event_kind=event.kind,
        )
        if any(not isinstance(item, HrLifecycleTemplate) for item in templates):
            raise TypeError("Le repository a retourné un modèle de cycle de vie RH invalide.")

        enabled_templates = tuple(item for item in templates if item.enabled)
        template_ids = [item.template_id for item in enabled_templates]
        if len(template_ids) != len(set(template_ids)):
            raise ValueError(
                "Le repository a retourné plusieurs modèles actifs avec le même identifiant."
            )
        if any(item.event_kind is not event.kind for item in enabled_templates):
            raise ValueError(
                "Le repository a retourné un modèle étranger au type d'événement demandé."
            )

        profiles = self._profile_repository.list_profiles(structure_ref=structure_ref)
        configured_organizations = {
            profile.organization.code
            for profile in profiles
            if profile.structure_ref == structure_ref
        }

        suggestions = tuple(
            self._suggestion(
                structure_ref=structure_ref,
                event=event,
                template=template,
                organization_configured=(
                    template.organization_code in configured_organizations
                ),
            )
            for template in sorted(enabled_templates, key=lambda item: item.template_id)
        )
        return HrLifecyclePlan(
            structure_ref=structure_ref,
            event=event,
            suggestions=suggestions,
        )

    @staticmethod
    def _suggestion(
        *,
        structure_ref: str,
        event: HrLifecycleEvent,
        template: HrLifecycleTemplate,
        organization_configured: bool,
    ) -> HrLifecycleSuggestion:
        due_on = (
            event.effective_on + timedelta(days=template.due_offset_days)
            if template.due_offset_days is not None
            else None
        )
        return HrLifecycleSuggestion(
            suggestion_key=_suggestion_key(
                structure_ref=structure_ref,
                lifecycle_event_id=event.event_id,
                template_id=template.template_id,
            ),
            lifecycle_event_id=event.event_id,
            template_id=template.template_id,
            person_ref=event.person_ref,
            event_kind=event.kind,
            organization_code=template.organization_code,
            organization_configured=organization_configured,
            case_type=template.case_type,
            opened_on=event.effective_on,
            due_on=due_on,
            expected_documents=template.expected_documents,
            source_ref=event.source_ref,
        )


def _suggestion_key(
    *,
    structure_ref: str,
    lifecycle_event_id: str,
    template_id: str,
) -> str:
    payload = "\0".join((structure_ref, lifecycle_event_id, template_id)).encode("utf-8")
    return sha256(payload).hexdigest()


def _required_text(value, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(message)
    return value.strip()
