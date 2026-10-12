from __future__ import annotations

from datetime import date
from typing import Callable

from domain.hr_connections import HrCaseDocumentReceipt, HrCaseDocumentState

from .teamworks_hr_case_document_repository import TeamworksHrCaseDocumentRepository
from .teamworks_hr_connections_repository import _close, _fetchall, _required_text


_COLUMNS = (
    "structure_ref",
    "receipt_key",
    "case_id",
    "document_code",
    "state",
    "received_on",
    "withdrawn_on",
    "artifact_ref",
    "source",
)


class TeamworksHrCaseDashboardDocumentRepository:
    """Projection de lecture groupée des pièces pour le cockpit CRH-33.

    Cet adaptateur lit toutes les réceptions d'une structure en une requête afin
    d'éviter un accès par démarche. Il ne possède aucune opération d'écriture et
    réutilise le schéma additif CRH-31.
    """

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        ensure_schema: bool = True,
    ) -> None:
        self._db_factory = db_factory or self._default_db_factory
        if ensure_schema:
            TeamworksHrCaseDocumentRepository(db_factory=self._db_factory)

    @staticmethod
    def _default_db_factory():
        import GestionDB

        return GestionDB.DB()

    def list_receipts_for_structure(
        self,
        *,
        structure_ref: str,
    ) -> tuple[HrCaseDocumentReceipt, ...]:
        structure_ref = _required_text(
            structure_ref,
            "La référence de structure est obligatoire.",
        )
        db = self._db_factory()
        try:
            rows = _fetchall(
                db,
                "SELECT "
                + ", ".join(_COLUMNS)
                + " FROM tw_hr_case_document_receipts "
                "WHERE structure_ref = ? ORDER BY case_id, document_code",
                (structure_ref,),
            )
        finally:
            _close(db)
        return tuple(_receipt_from_row(row) for row in rows)


def _receipt_from_row(row) -> HrCaseDocumentReceipt:
    return HrCaseDocumentReceipt(
        case_id=row[2],
        document_code=row[3],
        state=HrCaseDocumentState(row[4]),
        received_on=date.fromisoformat(row[5]),
        withdrawn_on=date.fromisoformat(row[6]) if row[6] else None,
        artifact_ref=row[7],
        source=row[8],
    )
