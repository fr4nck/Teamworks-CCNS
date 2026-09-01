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
    _CASE_COLUMNS,
    _case_values,
    _event_values,
)
from .teamworks_hr_connections_repository import (
    _close,
    _commit,
    _execute,
    _fetchone,
    _required_text,
    _rollback,
)


class DuplicateTeamworksHrCaseError(ValueError):
    """Un dossier existe déjà sous le même identifiant logique."""


class TeamworksHrCaseCreationRepository:
    """Transaction de production pour l'ouverture d'une démarche et son audit.

    Le schéma reste la propriété de ``TeamworksHrCasesRepository`` (CRH-22).
    Cet adaptateur n'ajoute aucune table et réutilise ses sérialisations afin que
    la création initiale et les lectures ultérieures restent strictement cohérentes.
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

    def create_case_with_event(
        self,
        *,
        structure_ref: str,
        case: HrCase,
        event: HrAuditEvent,
    ) -> HrCase:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        if not isinstance(case, HrCase):
            raise TypeError("Le dossier RH à créer est invalide.")
        if not isinstance(event, HrAuditEvent):
            raise TypeError("L'événement de création RH est invalide.")
        if case.status is not HrCaseStatus.TODO:
            raise ValueError("Une nouvelle démarche RH doit être créée au statut « À faire ».")
        if event.kind is not HrEventKind.CASE_CREATED:
            raise ValueError("L'événement d'audit doit décrire la création du dossier RH.")
        if event.target_kind is not HrEventTargetKind.CASE or event.target_ref != case.case_id:
            raise ValueError("L'événement de création ne cible pas le dossier RH créé.")

        db = self._db_factory()
        try:
            if _fetchone(
                db,
                """
                SELECT 1 FROM tw_hr_cases
                WHERE structure_ref = ? AND case_id = ?
                """,
                (structure_ref, case.case_id),
            ) is not None:
                raise DuplicateTeamworksHrCaseError(
                    f"La démarche RH '{case.case_id}' existe déjà."
                )

            if _fetchone(
                db,
                """
                SELECT 1 FROM tw_hr_audit_events
                WHERE structure_ref = ? AND event_id = ?
                """,
                (structure_ref, event.event_id),
            ) is not None:
                raise DuplicateTeamworksHrAuditEventError(
                    f"L'événement RH '{event.event_id}' est déjà persisté."
                )

            placeholders = ", ".join("?" for _ in _CASE_COLUMNS)
            _execute(
                db,
                "INSERT INTO tw_hr_cases("
                + ", ".join(_CASE_COLUMNS)
                + f") VALUES ({placeholders})",
                _case_values(structure_ref, case),
            )

            for document in sorted(case.expected_documents, key=lambda item: item.code):
                _execute(
                    db,
                    """
                    INSERT INTO tw_hr_case_expected_documents(
                        structure_ref,
                        case_id,
                        document_code,
                        document_label,
                        required
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        structure_ref,
                        case.case_id,
                        document.code,
                        document.label,
                        1 if document.required else 0,
                    ),
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
                _event_values(structure_ref, event),
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
