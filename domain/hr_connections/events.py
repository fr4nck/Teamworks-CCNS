from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, Tuple


class HrEventKind(str, Enum):
    """Événements sensibles suivis par le chantier Connexions RH."""

    CASE_CREATED = "case_created"
    CASE_STATUS_CHANGED = "case_status_changed"
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_REMOVED = "document_removed"
    EXPORT_GENERATED = "export_generated"
    RETURN_IMPORTED = "return_imported"
    SYNC_STARTED = "sync_started"
    SYNC_SUCCEEDED = "sync_succeeded"
    SYNC_FAILED = "sync_failed"
    CONNECTOR_CONFIGURATION_CHANGED = "connector_configuration_changed"


class HrEventTargetKind(str, Enum):
    """Nature de l'objet auquel se rattache un événement d'audit."""

    CASE = "case"
    CONNECTOR = "connector"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    EXCHANGE = "exchange"


_FORBIDDEN_FIELD_NAMES = {
    "password",
    "mot_de_passe",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "cookie",
    "session",
    "api_key",
    "private_key",
    "medical_data",
    "health_data",
    "diagnosis",
    "pathology",
    "note_medicale",
    "contenu_medical",
}


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _is_forbidden_field_name(value: str) -> bool:
    normalized = _normalize_key(value)
    if normalized in _FORBIDDEN_FIELD_NAMES:
        return True
    forbidden_fragments = (
        "password",
        "mot_de_passe",
        "secret",
        "token",
        "cookie",
        "session",
        "api_key",
        "private_key",
        "medical",
        "medicale",
        "health",
        "diagnosis",
        "pathology",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)


@dataclass(frozen=True)
class HrAuditField:
    """Métadonnée d'audit explicitement non secrète et non médicale."""

    key: str
    value: str

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("La clé d'une métadonnée d'audit est obligatoire.")
        if not self.value.strip():
            raise ValueError("La valeur d'une métadonnée d'audit est obligatoire.")
        if _is_forbidden_field_name(self.key):
            raise ValueError(
                "Une métadonnée sensible ne peut pas être enregistrée dans le journal RH."
            )

    @classmethod
    def create(cls, *, key: str, value: str) -> "HrAuditField":
        return cls(key=_normalize_key(key), value=value.strip())


@dataclass(frozen=True)
class HrAuditEvent:
    """Événement d'audit immuable, indépendant de la persistance et de l'UI."""

    event_id: str
    kind: HrEventKind
    target_kind: HrEventTargetKind
    target_ref: str
    occurred_at: datetime
    actor_ref: str | None = None
    source: str | None = None
    fields: Tuple[HrAuditField, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("L'identifiant de l'événement RH est obligatoire.")
        if not isinstance(self.kind, HrEventKind):
            raise TypeError("Le type d'événement RH est invalide.")
        if not isinstance(self.target_kind, HrEventTargetKind):
            raise TypeError("La nature de la cible d'audit est invalide.")
        if not self.target_ref.strip():
            raise ValueError("La référence de la cible d'audit est obligatoire.")
        if not isinstance(self.occurred_at, datetime):
            raise TypeError("La date de l'événement RH est invalide.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("La date de l'événement RH doit être associée à un fuseau horaire.")
        if any(not isinstance(item, HrAuditField) for item in self.fields):
            raise TypeError("Les métadonnées de l'événement RH sont invalides.")
        field_keys = tuple(item.key for item in self.fields)
        if len(field_keys) != len(set(field_keys)):
            raise ValueError("Deux métadonnées d'audit ne peuvent pas partager la même clé.")

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        kind: HrEventKind,
        target_kind: HrEventTargetKind,
        target_ref: str,
        occurred_at: datetime,
        actor_ref: str | None = None,
        source: str | None = None,
        fields: Iterable[HrAuditField] = (),
    ) -> "HrAuditEvent":
        normalized_actor = actor_ref.strip() if actor_ref is not None else None
        normalized_source = source.strip() if source is not None else None
        return cls(
            event_id=event_id.strip(),
            kind=kind,
            target_kind=target_kind,
            target_ref=target_ref.strip(),
            occurred_at=occurred_at,
            actor_ref=normalized_actor or None,
            source=normalized_source or None,
            fields=tuple(fields),
        )


class HrEventJournal:
    """Journal append-only en mémoire des événements RH.

    Ce service de domaine n'offre volontairement aucune opération de mise à jour ou
    de suppression. La persistance append-only éventuelle sera traitée dans un lot
    distinct.
    """

    def __init__(self, events: Iterable[HrAuditEvent] = ()) -> None:
        self._events: list[HrAuditEvent] = []
        self._by_id: Dict[str, HrAuditEvent] = {}
        for event in events:
            self.append(event)

    def append(self, event: HrAuditEvent) -> None:
        if not isinstance(event, HrAuditEvent):
            raise TypeError("L'événement à journaliser est invalide.")
        if event.event_id in self._by_id:
            raise ValueError(f"L'événement RH '{event.event_id}' est déjà journalisé.")
        self._events.append(event)
        self._by_id[event.event_id] = event

    def all(self) -> Tuple[HrAuditEvent, ...]:
        return tuple(self._events)

    def for_target(
        self,
        *,
        target_kind: HrEventTargetKind,
        target_ref: str,
    ) -> Tuple[HrAuditEvent, ...]:
        if not isinstance(target_kind, HrEventTargetKind):
            raise TypeError("La nature de la cible d'audit est invalide.")
        normalized_ref = target_ref.strip()
        if not normalized_ref:
            raise ValueError("La référence de la cible d'audit est obligatoire.")
        return tuple(
            event
            for event in self._events
            if event.target_kind is target_kind and event.target_ref == normalized_ref
        )

    def for_kind(self, kind: HrEventKind) -> Tuple[HrAuditEvent, ...]:
        if not isinstance(kind, HrEventKind):
            raise TypeError("Le type d'événement RH est invalide.")
        return tuple(event for event in self._events if event.kind is kind)

    def __len__(self) -> int:
        return len(self._events)
