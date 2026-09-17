"""Adaptateur minimal d'écriture Contrats pour une connexion GestionDB existante.

L'adaptateur reçoit l'objet DB par injection et n'importe volontairement pas
teamworks.GestionDB : cela évite toute dépendance wx à l'import.
"""

from __future__ import annotations

from application.services.contract_write import ALLOWED_INDICATOR_FIELDS


class GestionDbContractWriteAdapter:
    def __init__(self, db):
        if db is None:
            raise RuntimeError("Connexion GestionDB absente.")
        if getattr(db, "echec", 0):
            raise RuntimeError("Connexion GestionDB indisponible.")
        if getattr(db, "cursor", None) is None or getattr(db, "connexion", None) is None:
            raise RuntimeError("Connexion GestionDB incomplète.")
        self.db = db

    @property
    def _placeholder(self) -> str:
        return "%s" if getattr(self.db, "isNetwork", False) else "?"

    def contract_exists(self, contract_id: int) -> bool:
        self.db.cursor.execute(
            "SELECT IDcontrat FROM contrats WHERE IDcontrat=%s" % self._placeholder,
            (contract_id,),
        )
        return self.db.cursor.fetchone() is not None

    def update_indicator(self, contract_id: int, field: str, value: str) -> int:
        if field not in ALLOWED_INDICATOR_FIELDS:
            raise ValueError("Indicateur contrat non autorisé : %s" % field)
        self.db.cursor.execute(
            "UPDATE contrats SET %s=%s WHERE IDcontrat=%s"
            % (field, self._placeholder, self._placeholder),
            (value, contract_id),
        )
        return int(self.db.cursor.rowcount)

    def commit(self) -> None:
        self.db.Commit()

    def rollback(self) -> None:
        self.db.connexion.rollback()

    def read_indicator(self, contract_id: int, field: str) -> str:
        if field not in ALLOWED_INDICATOR_FIELDS:
            raise ValueError("Indicateur contrat non autorisé : %s" % field)
        self.db.cursor.execute(
            "SELECT %s FROM contrats WHERE IDcontrat=%s" % (field, self._placeholder),
            (contract_id,),
        )
        row = self.db.cursor.fetchone()
        if row is None:
            raise LookupError("Contrat introuvable après commit.")
        return row[0] or ""
