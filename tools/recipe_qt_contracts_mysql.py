#!/usr/bin/env python3
"""Recette réelle du Rail A sur Windows + MySQL.

Ce script n'accepte volontairement ni SQLite ni les bases Exemple. Il utilise le
dossier Teamworks configuré sur le poste, crée un CDD CCNS temporaire via le
service Contrats et l'adaptateur de production, le relit, le modifie, le relit
à nouveau, puis le supprime et vérifie son absence.

La recette écrit donc brièvement une ligne dans la base réelle. Le nettoyage est
tenté dans un finally même si une étape intermédiaire échoue.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import os
from pathlib import Path
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
POC = ROOT / "poc" / "qt-theme"
for path in (ROOT, TEAMWORKS, POC):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from application.control.ccns_contract_compliance import (  # noqa: E402
    CCNSContractCompliancePresenter,
)
from application.services.contract_write import (  # noqa: E402
    ContractCreateCommand,
    ContractDeleteCommand,
    ContractEditCommand,
    create_contract,
    delete_contract,
    load_contract_creation_types,
    update_contract,
)
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity  # noqa: E402
from infrastructure.persistence.contract_write_adapter import (  # noqa: E402
    GestionDbContractWriteAdapter,
)
import GestionDB  # noqa: E402


READY = "TEAMWORKS_RAIL_A_MYSQL_READY"
FAILURE = "TEAMWORKS_RAIL_A_MYSQL_FAILED"


def _require_real_mysql(db) -> None:
    if os.name != "nt":
        raise RuntimeError("Cette recette doit être exécutée sur Windows.")
    if getattr(db, "echec", 1):
        raise RuntimeError("La connexion GestionDB a échoué.")
    if getattr(db, "isNetwork", False) is not True:
        raise RuntimeError(
            "Stop-gate refusé : le dossier actif n'est pas un backend MySQL réseau."
        )


def _safe_person_id(db, start: date, end: date) -> int:
    """Choisit une personne sans contrat chevauchant la fenêtre de recette."""
    db.cursor.execute(
        """
        SELECT p.IDpersonne
        FROM personnes p
        WHERE NOT EXISTS (
            SELECT 1
            FROM contrats c
            WHERE c.IDpersonne=p.IDpersonne
              AND COALESCE(c.date_debut, '')<>''
              AND c.date_debut<=%s
              AND (
                    c.date_fin IS NULL
                 OR c.date_fin=''
                 OR c.date_fin='2999-01-01'
                 OR c.date_fin>=%s
              )
        )
        ORDER BY p.IDpersonne
        LIMIT 1
        """,
        (end.isoformat(), start.isoformat()),
    )
    row = db.cursor.fetchone()
    if row is None:
        raise RuntimeError(
            "Aucune personne sans contrat chevauchant la fenêtre de recette ; "
            "aucune écriture n'a été tentée."
        )
    return int(row[0])


def _monthly_group(reference_date: date) -> str:
    choices = CCNSContractCompliancePresenter().group_choices(reference_date)
    for choice in choices:
        if choice.periodicity is SalaryMinimumPeriodicity.MONTHLY:
            return choice.code
    raise RuntimeError("Aucun groupe CCNS à minimum mensuel disponible pour la recette.")


def _cleanup(port: GestionDbContractWriteAdapter, contract_id: int | None) -> None:
    if not contract_id:
        return
    try:
        if port.contract_exists(contract_id):
            affected = port.delete_contract(contract_id)
            if affected != 1:
                raise RuntimeError(
                    "Nettoyage incomplet du contrat de recette : rowcount=%s" % affected
                )
            port.commit()
    except Exception:
        try:
            port.rollback()
        finally:
            raise


def run() -> int:
    db = None
    port = None
    created_id = None

    try:
        db = GestionDB.DB()
        _require_real_mysql(db)
        port = GestionDbContractWriteAdapter(db)

        try:
            version = db.GetVersionServeur()
        except Exception:
            version = None
        print("TEAMWORKS_RAIL_A_BACKEND:MYSQL", flush=True)
        print("TEAMWORKS_RAIL_A_MYSQL_VERSION:%s" % (version or "inconnue"), flush=True)

        start = date.today() + timedelta(days=14)
        end = start + timedelta(days=6)
        person_id = _safe_person_id(db, start, end)

        available = load_contract_creation_types(port)
        if not available.ok or not available.value:
            raise RuntimeError("Types de contrat indisponibles : %s" % available.message)
        if "CDD" not in available.value:
            raise RuntimeError("Le type CDD n'est pas configuré dans cette base.")

        group = _monthly_group(start)

        create_command = ContractCreateCommand(
            person_id=person_id,
            contract_type_code="CDD",
            convention_code="CCNS",
            ccns_group=group,
            cee_qualification=None,
            weekly_hours=Decimal("35.00"),
            gross_monthly_salary=Decimal("9999.00"),
            gross_annual_salary=None,
            start_date=start,
            end_date=end,
            trial_period_value=0,
            trial_period_unit="DAY",
            confirm_no_trial=True,
        )

        created = create_contract(port, command=create_command)
        if not created.ok or not created.committed or created.value is None:
            raise RuntimeError(
                "Création MySQL refusée : %s · %s" % (created.code, created.message)
            )
        created_id = created.target_id
        if not created_id:
            raise RuntimeError("Création commitée sans identifiant de contrat.")
        if created.value.contract_id != created_id:
            raise RuntimeError("Le readback de création ne restitue pas l'identité créée.")
        print("TEAMWORKS_RAIL_A_STAGE:create-readback", flush=True)

        updated_command = ContractEditCommand(
            contract_id=created_id,
            contract_type_code=created.value.contract_type_code,
            convention_code=created.value.convention_code,
            ccns_group=created.value.ccns_group,
            cee_qualification=created.value.cee_qualification,
            weekly_hours=created.value.weekly_hours,
            gross_monthly_salary=Decimal("9999.01"),
            gross_annual_salary=created.value.gross_annual_salary,
            start_date=created.value.start_date,
            end_date=created.value.end_date + timedelta(days=1),
            break_date=created.value.break_date,
            modern_fields_supported=created.value.modern_fields_supported,
        )

        updated = update_contract(port, command=updated_command)
        if not updated.ok or not updated.committed or updated.value is None:
            raise RuntimeError(
                "Modification MySQL refusée : %s · %s" % (updated.code, updated.message)
            )
        if updated.value.gross_monthly_salary != Decimal("9999.01"):
            raise RuntimeError("Le readback ne restitue pas le salaire modifié.")
        if updated.value.end_date != end + timedelta(days=1):
            raise RuntimeError("Le readback ne restitue pas la date de fin modifiée.")
        print("TEAMWORKS_RAIL_A_STAGE:update-readback", flush=True)

        deleted = delete_contract(
            port,
            command=ContractDeleteCommand(contract_id=created_id, confirmed=True),
        )
        if not deleted.ok or not deleted.committed:
            raise RuntimeError(
                "Suppression MySQL refusée : %s · %s" % (deleted.code, deleted.message)
            )
        if port.contract_exists(created_id):
            raise RuntimeError("Le contrat de recette existe encore après suppression.")
        print("TEAMWORKS_RAIL_A_STAGE:delete-readback", flush=True)

        created_id = None
        print(READY, flush=True)
        return 0

    except Exception:
        traceback.print_exc()
        print(FAILURE, flush=True)
        return 1

    finally:
        if port is not None and created_id is not None:
            try:
                _cleanup(port, created_id)
                print("TEAMWORKS_RAIL_A_CLEANUP:OK", flush=True)
            except Exception:
                traceback.print_exc()
                print("TEAMWORKS_RAIL_A_CLEANUP:FAILED", flush=True)
        if db is not None:
            try:
                db.Close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(run())
