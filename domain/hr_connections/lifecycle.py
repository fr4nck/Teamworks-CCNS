from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .cases import ExpectedDocument, HrCaseType


class HrLifecycleEventKind(str, Enum):
    """Événements administratifs génériques d'un parcours salarié.

    Ces valeurs décrivent un fait de gestion. Elles ne déduisent aucune démarche
    réglementaire à réaliser.
    """

    EMPLOYMENT_START = "employment_start"
    EMPLOYMENT_END = "employment_end"
    CONTRACT_CHANGED = "contract_changed"


@dataclass(frozen=True)
class HrLifecycleEvent:
    event_id: str
    kind: HrLifecycleEventKind
    person_ref: str
    effective_on: date
    source_ref: str | None = None

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        kind: HrLifecycleEventKind,
        person_ref: str,
        effective_on: date,
        source_ref: str | None = None,
    ) -> "HrLifecycleEvent":
        event_id = _required_text(event_id, "L'identifiant d'événement RH est obligatoire.")
        if not isinstance(kind, HrLifecycleEventKind):
            raise TypeError("La nature de l'événement de cycle de vie RH est invalide.")
        person_ref = _required_text(person_ref, "La référence salarié est obligatoire.")
        if not isinstance(effective_on, date):
            raise TypeError("La date d'effet de l'événement RH est invalide.")
        return cls(
            event_id=event_id,
            kind=kind,
            person_ref=person_ref,
            effective_on=effective_on,
            source_ref=_optional_text(source_ref),
        )


@dataclass(frozen=True)
class HrLifecycleTemplate:
    """Règle explicitement configurée qui relie un fait RH à une suggestion.

    Aucun catalogue n'est fourni par défaut : organisme, type de démarche, délai et
    pièces attendues doivent provenir d'une configuration explicite.
    """

    template_id: str
    event_kind: HrLifecycleEventKind
    organization_code: str
    case_type: HrCaseType
    due_offset_days: int | None = None
    expected_documents: tuple[ExpectedDocument, ...] = ()
    enabled: bool = True

    @classmethod
    def create(
        cls,
        *,
        template_id: str,
        event_kind: HrLifecycleEventKind,
        organization_code: str,
        case_type: HrCaseType,
        due_offset_days: int | None = None,
        expected_documents=(),
        enabled: bool = True,
    ) -> "HrLifecycleTemplate":
        template_id = _required_text(template_id, "L'identifiant du modèle RH est obligatoire.")
        if not isinstance(event_kind, HrLifecycleEventKind):
            raise TypeError("La nature d'événement du modèle RH est invalide.")
        organization_code = _required_text(
            organization_code,
            "Le code organisme du modèle RH est obligatoire.",
        )
        if not isinstance(case_type, HrCaseType):
            raise TypeError("Le type de démarche du modèle RH est invalide.")
        if due_offset_days is not None:
            if isinstance(due_offset_days, bool) or not isinstance(due_offset_days, int):
                raise TypeError("Le décalage d'échéance du modèle RH doit être un entier.")
            if abs(due_offset_days) > 3660:
                raise ValueError("Le décalage d'échéance du modèle RH est hors limites.")
        documents = tuple(expected_documents)
        if any(not isinstance(item, ExpectedDocument) for item in documents):
            raise TypeError("Le modèle RH contient une pièce attendue invalide.")
        codes = [item.code for item in documents]
        if len(codes) != len(set(codes)):
            raise ValueError("Le modèle RH contient plusieurs fois la même pièce attendue.")
        if not isinstance(enabled, bool):
            raise TypeError("L'état actif du modèle RH est invalide.")
        return cls(
            template_id=template_id,
            event_kind=event_kind,
            organization_code=organization_code,
            case_type=case_type,
            due_offset_days=due_offset_days,
            expected_documents=documents,
            enabled=enabled,
        )


def _required_text(value, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(message)
    return value.strip()


def _optional_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("La référence source de l'événement RH est invalide.")
    value = value.strip()
    return value or None
