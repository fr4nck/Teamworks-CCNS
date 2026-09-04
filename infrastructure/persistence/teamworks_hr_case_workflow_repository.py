from __future__ import annotations

from typing import Callable

from domain.hr_connections import (
    HrAuditEvent,
    HrCase,
    HrCaseStatus,
    HrEventKind,
    HrEventTargetKind,
)

from .teamworks_hr_cases_repository import (
    DuplicateTeamworksHrAuditEventError,
    TeamworksHrCasesRepository,
)
from .teamworks_hr_connections_repository import (
    _close,
    _commit,
    _execute,
    _fetchone,
    _required_text,
    _rollback,
)


class StaleTeamworksHrCaseTransitionError(RuntimeError):
    """Le dossier a changé depuis sa lecture et doit être rechargé."""


class TeamworksHrCaseWorkflowRepository:
    """Transaction de production pour une transition métier et son audit.

    Cet adaptateur ne crée aucune table supplémentaire. Il s'appuie sur le schéma
    CRH-22 et maintient dans une seule transaction la projection courante du dossier
    et l'événement append-only correspondant.
    """

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        ensure_schema: bool = True,
    ) -> None:
        self._db_factory = db_factory or self._default_db_factory
        self._cases = TeamworksHrCasesRepository(
            db_factory=self._db_factory,
            ensure_schema=ensure_schema,
        )

    @staticmethod
    def _default_db_factory():
        import GestionDB

        return GestionDB.DB()

    def get_case(self, *, structure_ref: str, case_id: str) -> HrCase | None:
        return self._cases.get_case(
            structure_ref=structure_ref,
            case_id=case_id,
        )

    def persist_case_transition(
        self,
        *,
        structure_ref: str,
        expected_status: HrCaseStatus,
        case: HrCase,
        event: HrAuditEvent,
    ) -> HrCase:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(expected_status, HrCaseStatus):
            raise TypeError("Le statut attendu du dossier RH est invalide.")
        if not isinstance(case, HrCase):
            raise TypeError("Le dossier RH à persister est invalide.")
        if not isinstance(event, HrAuditEvent):
            raise TypeError("L'événement RH à persister est invalide.")
        if case.status is expected_status:
            raise ValueError("Une transition RH doit modifier le statut métier du dossier.")
        if event.kind is not HrEventKind.CASE_STATUS_CHANGED:
            raise ValueError("L'événement d'audit doit décrire un changement de statut RH.")
        if event.target_kind is not HrEventTargetKind.CASE or event.target_ref != case.case_id:
            raise ValueError("L'événement d'audit ne cible pas le dossier RH modifié.")

        db = self._db_factory()
        try:
            duplicate = _fetchone(
                db,
                """
                SELECT 1 FROM tw_hr_audit_events
                WHERE structure_ref = ? AND event_id = ?
                """,
                (structure_ref, event.event_id),
            )
            if duplicate is not None:
                raise DuplicateTeamworksHrAuditEventError(
                    f"L'événement RH '{event.event_id}' est déjà persisté."
                )

            cursor = _execute(
                db,
                """
                UPDATE tw_hr_cases
                SET status = ?, result = ?, comment = ?
                WHERE structure_ref = ?
                  AND case_id = ?
                  AND status = ?
                  AND exchange_status = ?
                """,
                (
                    case.status.value,
                    case.result,
                    case.comment,
                    structure_ref,
                    case.case_id,
                    expected_status.value,
                    case.exchange_status.value,
                ),
            )
            if int(getattr(cursor, "rowcount", 0)) != 1:
                raise StaleTeamworksHrCaseTransitionError(
                    "Le dossier RH a changé depuis son ouverture ; rechargez-le avant de réessayer."
                )

            _execute(
                db,
                """
                INSERT INTO tw_hr_audit_events(
                    structure_ref,
                    event_id,
                    event_kind,
                    target_kind,
                    target_ref,
                    occurred_at,
                    actor_ref,
                    source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    structure_ref,
                    event.event_id,
                    event.kind.value,
                    event.target_kind.value,
                    event.target_ref,
                    event.occurred_at.isoformat(),
                    event.actor_ref,
                    event.source,
                ),
            )
            for position, field in enumerate(event.fields):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_audit_fields(
                        structure_ref,
                        event_id,
                        position,
                        field_key,
                        field_value
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        structure_ref,
                        event.event_id,
                        position,
                        field.key,
                        field.value,
                    ),
                )
            _commit(db)
        except Exception:
            _rollback(db)
            raise
        finally:
            _close(db)
        return case
