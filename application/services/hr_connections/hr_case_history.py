from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Tuple

from domain.hr_connections import (
    HrAuditEvent,
    HrEventKind,
    HrEventTargetKind,
)


class HrCaseHistoryRepository(Protocol):
    """Port de lecture du journal append-only pour une démarche RH."""

    def list_events(
        self,
        *,
        structure_ref: str,
        target_kind: HrEventTargetKind | None = None,
        target_ref: str | None = None,
    ) -> tuple[HrAuditEvent, ...]:
        ...


@dataclass(frozen=True)
class HrCaseHistoryField:
    key: str
    value: str


@dataclass(frozen=True)
class HrCaseHistoryRow:
    event_id: str
    kind: HrEventKind
    occurred_at: datetime
    actor_ref: str | None
    source: str | None
    fields: Tuple[HrCaseHistoryField, ...]


@dataclass(frozen=True)
class HrCaseHistory:
    case_id: str
    rows: Tuple[HrCaseHistoryRow, ...]
    total_count: int
    status_change_count: int
    latest_at: datetime | None

    @property
    def is_empty(self) -> bool:
        return self.total_count == 0


class HrCaseHistoryService:
    """Construit l'historique descriptif d'une démarche depuis le journal d'audit."""

    def __init__(self, *, repository: HrCaseHistoryRepository) -> None:
        self._repository = repository

    def build(self, *, structure_ref: str, case_id: str) -> HrCaseHistory:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        case_id = _required_text(
            case_id,
            "L'identifiant du dossier RH est obligatoire.",
        )
        events = self._repository.list_events(
            structure_ref=structure_ref,
            target_kind=HrEventTargetKind.CASE,
            target_ref=case_id,
        )
        if any(not isinstance(event, HrAuditEvent) for event in events):
            raise TypeError("Le repository a retourné un événement d'audit RH invalide.")
        if any(
            event.target_kind is not HrEventTargetKind.CASE
            or event.target_ref != case_id
            for event in events
        ):
            raise ValueError("Le repository a retourné un événement étranger au dossier RH.")

        rows = tuple(
            sorted(
                (
                    HrCaseHistoryRow(
                        event_id=event.event_id,
                        kind=event.kind,
                        occurred_at=event.occurred_at,
                        actor_ref=event.actor_ref,
                        source=event.source,
                        fields=tuple(
                            HrCaseHistoryField(key=field.key, value=field.value)
                            for field in event.fields
                        ),
                    )
                    for event in events
                ),
                key=lambda row: (row.occurred_at, row.event_id),
                reverse=True,
            )
        )
        return HrCaseHistory(
            case_id=case_id,
            rows=rows,
            total_count=len(rows),
            status_change_count=sum(
                1 for row in rows if row.kind is HrEventKind.CASE_STATUS_CHANGED
            ),
            latest_at=rows[0].occurred_at if rows else None,
        )


def _required_text(value: str, message: str) -> str:
    if not isinstance(value, str):
        raise TypeError(message)
    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized
