"""Adaptateur minimal d'écriture Contrats pour une connexion GestionDB existante.

L'adaptateur reçoit l'objet DB par injection et n'importe volontairement pas
teamworks.GestionDB : cela évite toute dépendance wx à l'import.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from application.services.contract_write import (
    ALLOWED_INDICATOR_FIELDS,
    ContractEditCommand,
    ContractEditSnapshot,
)


class GestionDbContractWriteAdapter:
    def __init__(self, db):
        if db is None:
            raise RuntimeError("Connexion GestionDB absente.")
        if getattr(db, "echec", 0):
            raise RuntimeError("Connexion GestionDB indisponible.")
        if getattr(db, "cursor", None) is None or getattr(db, "connexion", None) is None:
            raise RuntimeError("Connexion GestionDB incomplète.")
        self.db = db
        self._contract_columns_cache = None

    @property
    def _placeholder(self) -> str:
        return "%s" if getattr(self.db, "isNetwork", False) else "?"


    def _contract_columns(self) -> set[str]:
        if self._contract_columns_cache is None:
            columns = self.db.GetListeChamps2("contrats") or ()
            self._contract_columns_cache = {str(item[0]) for item in columns if item}
        return self._contract_columns_cache

    def _optional_expr(self, name: str) -> str:
        return name if name in self._contract_columns() else "NULL"

    @staticmethod
    def _as_date(value):
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.date()
        if type(value) is date:
            return value
        text = str(value).strip()
        if not text:
            return None
        return date.fromisoformat(text[:10])

    @staticmethod
    def _as_decimal(value):
        if value in (None, ""):
            return None
        return Decimal(str(value))

    def read_contract(self, contract_id: int) -> ContractEditSnapshot | None:
        modern_names = (
            "convention_code",
            "ccns_group",
            "cee_qualification",
            "weekly_hours",
            "gross_monthly_salary",
            "gross_annual_salary",
        )
        modern_supported = all(name in self._contract_columns() for name in modern_names)
        exprs = [self._optional_expr(name) for name in modern_names]
        req = (
            "SELECT c.IDpersonne, c.IDtype, COALESCE(t.nom_abrege, t.nom, ''), "
            "COALESCE(t.nom, t.nom_abrege, ''), "
            "c.date_debut, c.date_fin, c.date_rupture, "
            + ", ".join("c.%s" % expr if expr != "NULL" else "NULL" for expr in exprs)
            + " FROM contrats c "
            "LEFT JOIN contrats_types t ON t.IDtype=c.IDtype "
            "WHERE c.IDcontrat=%s" % self._placeholder
        )
        self.db.cursor.execute(req, (contract_id,))
        row = self.db.cursor.fetchone()
        if row is None:
            return None

        end_date = self._as_date(row[5])
        if end_date == date(2999, 1, 1):
            end_date = None
        return ContractEditSnapshot(
            contract_id=contract_id,
            person_id=int(row[0]),
            contract_type_code=str(row[2] or "").strip().upper(),
            contract_type_label=str(row[3] or row[2] or "").strip(),
            start_date=self._as_date(row[4]),
            end_date=end_date,
            break_date=self._as_date(row[6]),
            convention_code=row[7],
            ccns_group=row[8],
            cee_qualification=row[9],
            weekly_hours=self._as_decimal(row[10]),
            gross_monthly_salary=self._as_decimal(row[11]),
            gross_annual_salary=self._as_decimal(row[12]),
            modern_fields_supported=modern_supported,
        )

    def update_contract(self, command: ContractEditCommand) -> int:
        fields = [
            ("date_debut", command.start_date.isoformat()),
            ("date_fin", command.end_date.isoformat() if command.end_date else "2999-01-01"),
            ("date_rupture", command.break_date.isoformat() if command.break_date else None),
        ]
        if command.modern_fields_supported:
            if not all(
                name in self._contract_columns()
                for name in (
                    "convention_code",
                    "ccns_group",
                    "cee_qualification",
                    "weekly_hours",
                    "gross_monthly_salary",
                    "gross_annual_salary",
                )
            ):
                raise RuntimeError("Le schéma moderne du contrat n'est plus disponible.")
            fields.extend(
                (
                    ("convention_code", command.convention_code),
                    ("ccns_group", command.ccns_group),
                    ("cee_qualification", command.cee_qualification),
                    (
                        "weekly_hours",
                        float(command.weekly_hours) if command.weekly_hours is not None else None,
                    ),
                    (
                        "gross_monthly_salary",
                        float(command.gross_monthly_salary)
                        if command.gross_monthly_salary is not None
                        else None,
                    ),
                    (
                        "gross_annual_salary",
                        float(command.gross_annual_salary)
                        if command.gross_annual_salary is not None
                        else None,
                    ),
                )
            )

        assignments = ", ".join(
            "%s=%s" % (name, self._placeholder) for name, _value in fields
        )
        values = [value for _name, value in fields]
        values.append(command.contract_id)
        self.db.cursor.execute(
            "UPDATE contrats SET %s WHERE IDcontrat=%s" % (assignments, self._placeholder),
            tuple(values),
        )
        return int(self.db.cursor.rowcount)

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
