"""Persistance additive des avenants du Rail A.

Cette couche étend l'adaptateur Contrats existant : elle ne remplace ni la table
``contrats`` ni ``GestionDbContractWriteAdapter``. L'historique est append-only
et l'état courant continue d'être projeté dans ``contrats`` pour les lecteurs
legacy.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from application.services.contract_amendment import ContractAmendmentRecord
from infrastructure.persistence.contract_write_adapter import (
    GestionDbContractWriteAdapter,
)


AMENDMENT_TABLE = "tw_contract_amendment"


class GestionDbContractAmendmentAdapter(GestionDbContractWriteAdapter):
    """Ajoute verrouillage et journal d'avenants à l'adaptateur Contrats."""

    def lock_contract(self, contract_id: int):
        return self._read_contract(contract_id, for_update=True)

    @staticmethod
    def _as_record(row) -> ContractAmendmentRecord:
        effective = row[2]
        if isinstance(effective, datetime):
            effective = effective.date()
        elif type(effective) is not date:
            effective = date.fromisoformat(str(effective)[:10])
        changed_fields = tuple(
            item for item in str(row[6] or "").split(",") if item
        )
        created = row[11]
        if isinstance(created, datetime):
            created_at = created.isoformat(sep=" ")
        else:
            created_at = str(created or "")
        return ContractAmendmentRecord(
            amendment_id=int(row[0]),
            contract_id=int(row[1]),
            effective_date=effective,
            kind=str(row[3] or ""),
            idempotency_key=str(row[4] or ""),
            request_hash=str(row[5] or ""),
            changed_fields=changed_fields,
            before_hash=str(row[7] or ""),
            after_hash=str(row[8] or ""),
            before_payload=str(row[9] or ""),
            after_payload=str(row[10] or ""),
            created_at=created_at,
        )

    def _select_amendment(self, where_sql: str, params) -> ContractAmendmentRecord | None:
        self.db.cursor.execute(
            "SELECT amendment_id, contract_id, effective_date, kind, "
            "idempotency_key, request_hash, changed_fields, before_hash, "
            "after_hash, before_payload, after_payload, created_at "
            "FROM %s WHERE %s" % (AMENDMENT_TABLE, where_sql),
            params,
        )
        row = self.db.cursor.fetchone()
        return None if row is None else self._as_record(row)

    def find_amendment_by_key(self, idempotency_key: str):
        return self._select_amendment(
            "idempotency_key=%s" % self._placeholder,
            (idempotency_key,),
        )

    def latest_amendment(self, contract_id: int):
        return self._select_amendment(
            "contract_id=%s ORDER BY effective_date DESC, amendment_id DESC LIMIT 1"
            % self._placeholder,
            (contract_id,),
        )

    def read_amendment(self, amendment_id: int):
        return self._select_amendment(
            "amendment_id=%s" % self._placeholder,
            (amendment_id,),
        )

    def insert_amendment(
        self,
        *,
        contract_id: int,
        effective_date: date,
        kind: str,
        idempotency_key: str,
        request_hash: str,
        changed_fields: tuple[str, ...],
        before_hash: str,
        after_hash: str,
        before_payload: str,
        after_payload: str,
    ) -> int:
        created_at = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        inserted = self.db.ReqInsert(
            AMENDMENT_TABLE,
            [
                ("contract_id", contract_id),
                ("effective_date", effective_date.isoformat()),
                ("kind", kind),
                ("idempotency_key", idempotency_key),
                ("request_hash", request_hash),
                ("changed_fields", ",".join(changed_fields)),
                ("before_hash", before_hash),
                ("after_hash", after_hash),
                ("before_payload", before_payload),
                ("after_payload", after_payload),
                ("created_at", created_at.strftime("%Y-%m-%d %H:%M:%S")),
            ],
            commit=False,
        )
        if inserted is None:
            raise RuntimeError("L'historique de l'avenant n'a pas pu être créé.")
        return int(inserted)
