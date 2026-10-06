#!/usr/bin/env python3
"""Recette reelle du Rail A Contrats sur Windows + MySQL/MariaDB.

La recette refuse SQLite et les bases non reseau. Elle conserve le CRUD Contrats
historique puis qualifie les avenants historises sur un vrai moteur transactionnel:
schema, commit/readback, idempotence, rollback, readback post-commit, concurrence
et preservation de la genealogie CDD. Toutes les donnees de recette sont nettoyees
et le marqueur READY n'est emis qu'apres verification independante du nettoyage.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
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
from application.services.contract_amendment import (  # noqa: E402
    CONCURRENT_MODIFICATION,
    IDEMPOTENT_REPLAY,
    ContractAmendmentCommand,
    apply_contract_amendment,
    contract_state_hash,
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
from application.services.transactional_write import WriteCode  # noqa: E402
from domain.contracts.contract_operation import ContractOperation  # noqa: E402
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity  # noqa: E402
from infrastructure.persistence.contract_amendment_adapter import (  # noqa: E402
    GestionDbContractAmendmentAdapter,
)
from infrastructure.persistence.contract_write_adapter import (  # noqa: E402
    GestionDbContractWriteAdapter,
)
import GestionDB  # noqa: E402


READY = "TEAMWORKS_RAIL_A_MYSQL_READY"
FAILURE = "TEAMWORKS_RAIL_A_MYSQL_FAILED"
REPORT_DIR = ROOT / "artifacts" / "rail-a-mysql"
REPORT_PATH = REPORT_DIR / "report.json"
DDL_PATH = ROOT / "infrastructure" / "persistence" / "sql" / "contract_amendment_v1.sql"
AMENDMENT_TABLE = "tw_contract_amendment"
EXPECTED_BRANCH = "qt/contracts-amendment-foundation"


class RecipeFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RecipeFailure(message)


def _require_real_mysql(db) -> None:
    if os.name != "nt":
        raise RecipeFailure("Cette recette doit etre executee sur Windows.")
    if getattr(db, "echec", 1):
        raise RecipeFailure("La connexion GestionDB a echoue.")
    if getattr(db, "isNetwork", False) is not True:
        raise RecipeFailure(
            "Stop-gate refuse : le dossier actif n'est pas un backend MySQL reseau."
        )


def _git_value(*args: str) -> str:
    try:
        completed = subprocess.run(
            ("git",) + args,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except Exception:
        return ""


def _git_context() -> tuple[str, str]:
    sha = _git_value("rev-parse", "HEAD") or os.environ.get("GITHUB_SHA", "inconnu")
    branch = (
        _git_value("branch", "--show-current")
        or os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
        or "inconnue"
    )
    return sha, branch


def _git_source_preflight() -> tuple[str, str]:
    """Garantit que le SHA rapporte correspond exactement au code suivi execute."""
    sha, branch = _git_context()
    valid_sha = len(sha) == 40 and all(
        character in "0123456789abcdefABCDEF" for character in sha
    )
    _require(valid_sha, "SHA Git du code teste introuvable ou invalide.")
    _require(
        branch == EXPECTED_BRANCH,
        "Branche Git inattendue pour le stop-gate : %s." % branch,
    )
    try:
        completed = subprocess.run(
            ("git", "status", "--porcelain", "--untracked-files=no"),
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        raise RecipeFailure("Etat Git impossible a verifier : %s" % exc) from exc
    _require(
        not completed.stdout.strip(),
        "Worktree Git suivi modifie : le SHA reporte ne correspondrait pas exactement au code execute.",
    )
    return sha, branch


def _new_report(run_id: str) -> dict[str, object]:
    sha, branch = _git_context()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "tested_sha": sha,
        "branch": branch,
        "python_version": platform.python_version(),
        "mysql": {},
        "scenarios": {},
        "technical_ids": {"contracts": [], "amendments": []},
        "cleanup": {"status": "PENDING"},
        "overall": "PENDING",
    }


def _scenario(report: dict[str, object], name: str, stage: str | None, callback):
    scenarios = report["scenarios"]
    try:
        details = callback() or {}
    except Exception as exc:
        scenarios[name] = {
            "status": "FAILURE",
            "error_type": type(exc).__name__,
        }
        raise
    scenarios[name] = {"status": "SUCCESS", **details}
    if stage:
        print(stage, flush=True)
    return details


def _record_contract_id(report: dict[str, object], contract_ids: list[int], value) -> None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        if value not in contract_ids:
            contract_ids.append(value)
        ids = report["technical_ids"]["contracts"]
        if value not in ids:
            ids.append(value)


def _record_amendment_id(report: dict[str, object], value) -> None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        ids = report["technical_ids"]["amendments"]
        if value not in ids:
            ids.append(value)


def _write_report(report: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _query_one(db, query: str, params=()):
    db.cursor.execute(query, params)
    return db.cursor.fetchone()


def _server_preflight(db, port: GestionDbContractWriteAdapter) -> dict[str, object]:
    _require_real_mysql(db)
    tested_sha, branch = _git_source_preflight()

    row = _query_one(db, "SELECT VERSION(), DATABASE(), @@autocommit")
    _require(row is not None and len(row) >= 3, "Preflight serveur MySQL incomplet.")
    version = str(row[0] or "")
    database_name = str(row[1] or "")
    autocommit = int(row[2])

    isolation = None
    isolation_source = None
    for variable in ("@@session.transaction_isolation", "@@session.tx_isolation"):
        try:
            iso_row = _query_one(db, "SELECT %s" % variable)
            if iso_row is not None and iso_row[0] is not None:
                isolation = str(iso_row[0])
                isolation_source = variable
                break
        except Exception:
            try:
                db.connexion.rollback()
            except Exception:
                pass
    _require(bool(isolation), "Niveau d'isolation MySQL/MariaDB introuvable.")

    _query_one(db, "SELECT 1")
    db.connexion.rollback()
    _query_one(db, "SELECT 1")
    db.Commit()

    available = load_contract_creation_types(port)
    _require(available.ok and available.value, "Types de contrat indisponibles.")
    _require("CDI" in available.value, "Le type CDI n'est pas configure dans cette base.")
    _require("CDD" in available.value, "Le type CDD n'est pas configure dans cette base.")
    group = _monthly_group(date.today())

    print("TEAMWORKS_RAIL_A_BACKEND:MYSQL", flush=True)
    print("TEAMWORKS_RAIL_A_SOURCE:SHA=%s" % tested_sha, flush=True)
    print("TEAMWORKS_RAIL_A_SOURCE:BRANCH=%s" % branch, flush=True)
    print("TEAMWORKS_RAIL_A_SOURCE:TRACKED_WORKTREE=CLEAN", flush=True)
    print("TEAMWORKS_RAIL_A_PREFLIGHT:VERSION=%s" % version, flush=True)
    print("TEAMWORKS_RAIL_A_PREFLIGHT:DATABASE=%s" % (database_name or "inconnue"), flush=True)
    print("TEAMWORKS_RAIL_A_PREFLIGHT:AUTOCOMMIT=%s" % autocommit, flush=True)
    print("TEAMWORKS_RAIL_A_PREFLIGHT:ISOLATION=%s" % isolation, flush=True)

    return {
        "tested_sha": tested_sha,
        "branch": branch,
        "tracked_worktree_clean": True,
        "version": version,
        "database": database_name or None,
        "autocommit": autocommit,
        "isolation": isolation,
        "isolation_source": isolation_source,
        "available_contract_types": sorted(available.value),
        "monthly_ccns_group": group,
    }


def _monthly_group(reference_date: date) -> str:
    choices = CCNSContractCompliancePresenter().group_choices(reference_date)
    for choice in choices:
        if choice.periodicity is SalaryMinimumPeriodicity.MONTHLY:
            return choice.code
    raise RecipeFailure("Aucun groupe CCNS a minimum mensuel disponible pour la recette.")


def _safe_person_id(
    db,
    start: date,
    end: date,
    *,
    excluded_person_ids: tuple[int, ...] = (),
) -> int:
    """Choisit une personne sans contrat chevauchant la fenetre de recette."""
    exclusion_sql = ""
    params: list[object] = [end.isoformat(), start.isoformat()]
    if excluded_person_ids:
        placeholders = ", ".join("%s" for _ in excluded_person_ids)
        exclusion_sql = " AND p.IDpersonne NOT IN (%s)" % placeholders
        params.extend(excluded_person_ids)
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
        %s
        ORDER BY p.IDpersonne
        LIMIT 1
        """ % ("%s", "%s", exclusion_sql),
        tuple(params),
    )
    row = db.cursor.fetchone()
    if row is None:
        raise RecipeFailure(
            "Aucune personne sans contrat chevauchant la fenetre de recette ; "
            "aucune ecriture n'a ete tentee."
        )
    return int(row[0])


def _strip_sql_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def _apply_amendment_schema(db) -> dict[str, object]:
    sql = _strip_sql_comments(DDL_PATH.read_text(encoding="utf-8"))
    statements = [item.strip() for item in sql.split(";") if item.strip()]
    _require(bool(statements), "DDL avenants vide.")
    for statement in statements:
        db.cursor.execute(statement)
    db.Commit()

    table_row = _query_one(
        db,
        "SELECT ENGINE FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s",
        (AMENDMENT_TABLE,),
    )
    _require(table_row is not None, "Table tw_contract_amendment absente apres DDL.")
    engine = str(table_row[0] or "")
    _require(engine.upper() == "INNODB", "tw_contract_amendment n'utilise pas InnoDB.")

    db.cursor.execute(
        "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
        (AMENDMENT_TABLE,),
    )
    columns = db.cursor.fetchall() or ()
    expected_columns = (
        "amendment_id",
        "contract_id",
        "effective_date",
        "kind",
        "idempotency_key",
        "request_hash",
        "changed_fields",
        "before_hash",
        "after_hash",
        "before_payload",
        "after_payload",
        "created_at",
    )
    names = tuple(str(row[0]) for row in columns)
    _require(names == expected_columns, "Colonnes tw_contract_amendment inattendues.")
    idempotency = next(row for row in columns if str(row[0]) == "idempotency_key")
    _require(str(idempotency[1]).lower() == "varchar", "idempotency_key n'est pas VARCHAR.")
    _require(int(idempotency[2]) == 64, "idempotency_key n'est pas VARCHAR(64).")

    db.cursor.execute(
        "SELECT INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME "
        "FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s "
        "ORDER BY INDEX_NAME, SEQ_IN_INDEX",
        (AMENDMENT_TABLE,),
    )
    index_rows = db.cursor.fetchall() or ()
    indexes: dict[str, list[tuple[int, str]]] = {}
    uniqueness: dict[str, int] = {}
    for index_name, non_unique, seq, column_name in index_rows:
        name = str(index_name)
        indexes.setdefault(name, []).append((int(seq), str(column_name)))
        uniqueness[name] = int(non_unique)

    unique_name = "uq_tw_contract_amendment_idempotency"
    ix_name = "ix_tw_contract_amendment_contract_effective"
    _require(unique_name in indexes, "Index UNIQUE d'idempotence absent.")
    _require(uniqueness[unique_name] == 0, "Index d'idempotence non UNIQUE.")
    _require(
        tuple(column for _seq, column in indexes[unique_name]) == ("idempotency_key",),
        "Index UNIQUE d'idempotence mal defini.",
    )
    _require(ix_name in indexes, "Index contrat/date d'effet absent.")
    _require(
        tuple(column for _seq, column in indexes[ix_name])
        == ("contract_id", "effective_date", "amendment_id"),
        "Ordre de l'index contrat/date d'effet incorrect.",
    )
    return {
        "engine": engine,
        "columns": list(names),
        "idempotency_key": "VARCHAR(64)",
        "unique_index": unique_name,
        "contract_effective_index": [
            "contract_id",
            "effective_date",
            "amendment_id",
        ],
    }


def _edit(snapshot, **changes) -> ContractEditCommand:
    return ContractEditCommand(
        contract_id=snapshot.contract_id,
        contract_type_code=snapshot.contract_type_code,
        convention_code=snapshot.convention_code,
        ccns_group=changes.get("ccns_group", snapshot.ccns_group),
        cee_qualification=changes.get("cee_qualification", snapshot.cee_qualification),
        weekly_hours=changes.get("weekly_hours", snapshot.weekly_hours),
        gross_monthly_salary=changes.get(
            "gross_monthly_salary", snapshot.gross_monthly_salary
        ),
        gross_annual_salary=changes.get(
            "gross_annual_salary", snapshot.gross_annual_salary
        ),
        start_date=snapshot.start_date,
        end_date=snapshot.end_date,
        break_date=snapshot.break_date,
        modern_fields_supported=snapshot.modern_fields_supported,
    )


def _create_checked(
    port: GestionDbContractWriteAdapter,
    command: ContractCreateCommand,
    report: dict[str, object],
    contract_ids: list[int],
):
    result = create_contract(port, command=command)
    _record_contract_id(report, contract_ids, result.target_id)
    _require(
        result.ok and result.committed and result.value is not None and result.target_id,
        "Creation MySQL refusee : %s - %s" % (result.code, result.message),
    )
    _require(
        result.value.contract_id == result.target_id,
        "Le readback de creation ne restitue pas l'identite creee.",
    )
    return result


def _direct_contract_projection(db, contract_id: int) -> dict[str, object] | None:
    row = _query_one(
        db,
        "SELECT c.IDcontrat, c.IDpersonne, COALESCE(t.nom_abrege, t.nom, ''), "
        "c.gross_monthly_salary, c.weekly_hours, c.operation_type, c.previous_contract_id "
        "FROM contrats c LEFT JOIN contrats_types t ON t.IDtype=c.IDtype "
        "WHERE c.IDcontrat=%s",
        (contract_id,),
    )
    if row is None:
        return None
    return {
        "contract_id": int(row[0]),
        "person_id": int(row[1]),
        "contract_type": str(row[2] or "").strip().upper(),
        "gross_monthly_salary": Decimal(str(row[3])) if row[3] is not None else None,
        "weekly_hours": Decimal(str(row[4])) if row[4] is not None else None,
        "operation_type": row[5],
        "previous_contract_id": int(row[6]) if row[6] is not None else None,
    }


def _direct_amendment(db, key: str) -> dict[str, object] | None:
    row = _query_one(
        db,
        "SELECT amendment_id, contract_id, effective_date, kind, idempotency_key, "
        "request_hash, changed_fields, before_hash, after_hash, before_payload, "
        "after_payload, created_at FROM tw_contract_amendment WHERE idempotency_key=%s",
        (key,),
    )
    if row is None:
        return None
    return {
        "amendment_id": int(row[0]),
        "contract_id": int(row[1]),
        "effective_date": str(row[2])[:10],
        "kind": str(row[3]),
        "idempotency_key": str(row[4]),
        "request_hash": str(row[5]),
        "changed_fields": str(row[6]),
        "before_hash": str(row[7]),
        "after_hash": str(row[8]),
        "before_payload": str(row[9]),
        "after_payload": str(row[10]),
        "created_at": str(row[11]),
    }


def _amendment_count(db, key: str) -> int:
    row = _query_one(
        db,
        "SELECT COUNT(*) FROM tw_contract_amendment WHERE idempotency_key=%s",
        (key,),
    )
    return int(row[0]) if row else 0


def _new_connection():
    db = GestionDB.DB()
    _require_real_mysql(db)
    return db


def _healthy_snapshot(contract_id: int):
    db = _new_connection()
    try:
        port = GestionDbContractAmendmentAdapter(db)
        snapshot = port.read_contract(contract_id)
        _require(snapshot is not None, "Contrat introuvable sur la connexion de controle.")
        return snapshot
    finally:
        try:
            db.Close()
        except Exception:
            pass


class _RollbackFailureAdapter(GestionDbContractAmendmentAdapter):
    """Laisse l'historique pending puis force une vraie erreur SQL a l'UPDATE."""

    def update_contract(self, command):
        self.db.cursor.execute(
            "UPDATE contrats SET __rail_a_missing_column__=1 WHERE IDcontrat=%s"
            % self._placeholder,
            (command.contract_id,),
        )
        return int(self.db.cursor.rowcount)


class _ReadbackFailureAfterCommitAdapter(GestionDbContractAmendmentAdapter):
    """Autorise le commit reel puis rend uniquement la relecture post-commit impossible."""

    def __init__(self, db):
        super().__init__(db)
        self._rail_a_committed = False

    def commit(self) -> None:
        super().commit()
        self._rail_a_committed = True

    def read_contract(self, contract_id: int):
        if self._rail_a_committed:
            raise RuntimeError("rail-a forced post-commit readback failure")
        return super().read_contract(contract_id)


def _cleanup_verified(
    run_id: str,
    contract_ids: list[int],
) -> tuple[bool, dict[str, object]]:
    errors: list[str] = []
    cleanup_db = None
    try:
        cleanup_db = _new_connection()
        cleanup_port = GestionDbContractWriteAdapter(cleanup_db)

        try:
            cleanup_db.cursor.execute(
                "DELETE FROM tw_contract_amendment "
                "WHERE idempotency_key LIKE %s",
                (run_id + "-%",),
            )
            removed_history = int(cleanup_db.cursor.rowcount)
            cleanup_db.Commit()
        except Exception as exc:
            try:
                cleanup_db.connexion.rollback()
            except Exception:
                pass
            removed_history = None
            errors.append("history:%s" % type(exc).__name__)

        for contract_id in reversed(contract_ids):
            try:
                if cleanup_port.contract_exists(contract_id):
                    result = delete_contract(
                        cleanup_port,
                        command=ContractDeleteCommand(
                            contract_id=contract_id,
                            confirmed=True,
                        ),
                    )
                    if not result.ok or not result.committed:
                        errors.append("contract-%s:%s" % (contract_id, result.code))
            except Exception as exc:
                try:
                    cleanup_port.rollback()
                except Exception:
                    pass
                errors.append("contract-%s:%s" % (contract_id, type(exc).__name__))
    except Exception as exc:
        removed_history = None
        errors.append("cleanup-connection:%s" % type(exc).__name__)
    finally:
        if cleanup_db is not None:
            try:
                cleanup_db.Close()
            except Exception:
                pass

    verifier = None
    remaining_contracts: list[int] = []
    remaining_history = None
    table_present = False
    try:
        verifier = _new_connection()
        verify_port = GestionDbContractWriteAdapter(verifier)
        remaining_contracts = [
            contract_id
            for contract_id in contract_ids
            if verify_port.contract_exists(contract_id)
        ]
        row = _query_one(
            verifier,
            "SELECT COUNT(*) FROM tw_contract_amendment WHERE idempotency_key LIKE %s",
            (run_id + "-%",),
        )
        remaining_history = int(row[0]) if row else -1
        table_row = _query_one(
            verifier,
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s",
            (AMENDMENT_TABLE,),
        )
        table_present = bool(table_row and int(table_row[0]) == 1)
    except Exception as exc:
        errors.append("cleanup-readback:%s" % type(exc).__name__)
    finally:
        if verifier is not None:
            try:
                verifier.Close()
            except Exception:
                pass

    ok = (
        not errors
        and not remaining_contracts
        and remaining_history == 0
        and table_present
    )
    return ok, {
        "status": "SUCCESS" if ok else "FAILURE",
        "removed_history_rows": removed_history,
        "remaining_contract_ids": remaining_contracts,
        "remaining_amendment_rows": remaining_history,
        "amendment_table_present": table_present,
        "errors": errors,
    }


def run() -> int:
    run_id = "rail-a-%s-%s" % (
        datetime.now().strftime("%Y%m%d-%H%M%S"),
        os.getpid(),
    )
    report = _new_report(run_id)
    print("TEAMWORKS_RAIL_A_RUN:%s" % run_id, flush=True)
    contract_ids: list[int] = []
    db = None
    port = None
    scenarios_ok = False
    cleanup_ok = False

    try:
        db = _new_connection()
        port = GestionDbContractAmendmentAdapter(db)

        preflight = _scenario(
            report,
            "preflight",
            None,
            lambda: _server_preflight(db, port),
        )
        report["tested_sha"] = preflight["tested_sha"]
        report["branch"] = preflight["branch"]
        report["source"] = {
            "tracked_worktree_clean": preflight["tracked_worktree_clean"],
        }
        report["mysql"] = {
            "version": preflight["version"],
            "database": preflight["database"],
            "autocommit": preflight["autocommit"],
            "isolation": preflight["isolation"],
        }

        _scenario(
            report,
            "amendment-schema",
            "TEAMWORKS_RAIL_A_STAGE:amendment-schema",
            lambda: _apply_amendment_schema(db),
        )

        def historical_crud():
            start = date.today() + timedelta(days=14)
            end = start + timedelta(days=6)
            person_id = _safe_person_id(
                db,
                start,
                end + timedelta(days=1),
            )
            group = _monthly_group(start)
            created = _create_checked(
                port,
                ContractCreateCommand(
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
                ),
                report,
                contract_ids,
            )
            created_id = int(created.target_id)
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
            _require(
                updated.ok and updated.committed and updated.value is not None,
                "Modification MySQL refusee : %s - %s" % (updated.code, updated.message),
            )
            _require(
                updated.value.gross_monthly_salary == Decimal("9999.01"),
                "Le readback ne restitue pas le salaire modifie.",
            )
            _require(
                updated.value.end_date == end + timedelta(days=1),
                "Le readback ne restitue pas la date de fin modifiee.",
            )
            print("TEAMWORKS_RAIL_A_STAGE:update-readback", flush=True)
            deleted = delete_contract(
                port,
                command=ContractDeleteCommand(contract_id=created_id, confirmed=True),
            )
            _require(
                deleted.ok and deleted.committed,
                "Suppression MySQL refusee : %s - %s" % (deleted.code, deleted.message),
            )
            _require(not port.contract_exists(created_id), "Le CDD CRUD existe encore.")
            print("TEAMWORKS_RAIL_A_STAGE:delete-readback", flush=True)
            return {
                "codes": [created.code, updated.code, deleted.code],
                "contract_id": created_id,
            }

        _scenario(report, "historical-contract-crud", None, historical_crud)

        cdi_start = date.today() - timedelta(days=30)
        cdi_person = _safe_person_id(
            db,
            cdi_start,
            date(2999, 1, 1),
        )
        cdi_group = _monthly_group(cdi_start)
        cdi_create = _create_checked(
            port,
            ContractCreateCommand(
                person_id=cdi_person,
                contract_type_code="CDI",
                convention_code="CCNS",
                ccns_group=cdi_group,
                cee_qualification=None,
                weekly_hours=Decimal("35.00"),
                gross_monthly_salary=Decimal("9999.00"),
                gross_annual_salary=None,
                start_date=cdi_start,
                end_date=None,
                trial_period_value=0,
                trial_period_unit="DAY",
                confirm_no_trial=True,
            ),
            report,
            contract_ids,
        )
        cdi_id = int(cdi_create.target_id)

        cdi_key = run_id + "-cdi-remuneration"
        cdi_command_holder = {}

        def cdi_nominal():
            snapshot = port.read_contract(cdi_id)
            _require(snapshot is not None, "CDI de recette introuvable avant avenant.")
            expected_before_hash = contract_state_hash(snapshot)
            command = ContractAmendmentCommand(
                edit=_edit(snapshot, gross_monthly_salary=Decimal("9999.10")),
                effective_date=date.today(),
                idempotency_key=cdi_key,
                expected_before_hash=expected_before_hash,
                expected_person_id=snapshot.person_id,
            )
            cdi_command_holder["command"] = command
            result = apply_contract_amendment(port, command=command)
            _require(result.ok is True, "Avenant CDI nominal en echec.")
            _require(result.committed is True, "Avenant CDI nominal non commite.")
            _require(result.code == WriteCode.OK, "Code CDI nominal inattendu: %s" % result.code)
            _require(result.value is not None, "Avenant CDI nominal sans record.")

            projection = _direct_contract_projection(db, cdi_id)
            _require(projection is not None, "Projection CDI absente apres commit.")
            _require(projection["contract_id"] == cdi_id, "ID CDI modifie.")
            _require(projection["person_id"] == snapshot.person_id, "Salarie CDI modifie.")
            _require(projection["contract_type"] == "CDI", "Type CDI detruit.")
            _require(
                projection["gross_monthly_salary"] == Decimal("9999.10"),
                "Salaire CDI direct SQL incorrect.",
            )
            reread = port.read_contract(cdi_id)
            _require(reread is not None, "Readback CDI absent.")
            expected_after_hash = contract_state_hash(reread)
            history = _direct_amendment(db, cdi_key)
            _require(history is not None, "Historique CDI absent.")
            _require(_amendment_count(db, cdi_key) == 1, "Historique CDI duplique.")
            _require(history["contract_id"] == cdi_id, "Historique sur mauvais CDI.")
            _require(history["kind"] == "REMUNERATION", "Kind CDI incorrect.")
            _require(
                history["changed_fields"] == "gross_monthly_salary",
                "changed_fields CDI incorrect.",
            )
            _require(history["before_hash"] == expected_before_hash, "before_hash CDI incorrect.")
            _require(history["after_hash"] == expected_after_hash, "after_hash CDI incorrect.")
            _require(
                '"gross_monthly_salary":"9999.00"' in history["before_payload"],
                "Payload avant CDI incorrect.",
            )
            _require(
                '"gross_monthly_salary":"9999.10"' in history["after_payload"],
                "Payload apres CDI incorrect.",
            )
            _record_amendment_id(report, history["amendment_id"])
            return {
                "codes": [result.code],
                "contract_id": cdi_id,
                "amendment_id": history["amendment_id"],
                "before_hash": expected_before_hash,
                "after_hash": expected_after_hash,
            }

        _scenario(
            report,
            "amendment-cdi-commit-readback",
            "TEAMWORKS_RAIL_A_STAGE:amendment-cdi-commit-readback",
            cdi_nominal,
        )

        def idempotent_replay():
            command = cdi_command_holder["command"]
            before_projection = _direct_contract_projection(db, cdi_id)
            before_history = _direct_amendment(db, cdi_key)
            result = apply_contract_amendment(port, command=command)
            after_projection = _direct_contract_projection(db, cdi_id)
            after_history = _direct_amendment(db, cdi_key)
            _require(result.ok is True, "Replay idempotent en echec.")
            _require(result.code == IDEMPOTENT_REPLAY, "Code replay inattendu: %s" % result.code)
            _require(result.committed is True, "Replay idempotent non classe committed.")
            _require(_amendment_count(db, cdi_key) == 1, "Replay a duplique l'historique.")
            _require(before_history is not None and after_history is not None, "Historique replay absent.")
            _require(
                before_history["amendment_id"] == after_history["amendment_id"],
                "Replay a change l'amendment_id.",
            )
            _require(before_projection == after_projection, "Replay a remute contrats.")
            _require(
                after_projection["gross_monthly_salary"] == Decimal("9999.10"),
                "Replay a change le salaire.",
            )
            return {
                "codes": [result.code],
                "amendment_id": after_history["amendment_id"],
            }

        _scenario(
            report,
            "amendment-idempotent-replay",
            "TEAMWORKS_RAIL_A_STAGE:amendment-idempotent-replay",
            idempotent_replay,
        )

        def idempotency_conflict():
            snapshot = port.read_contract(cdi_id)
            _require(snapshot is not None, "CDI absent avant collision idempotence.")
            command = ContractAmendmentCommand(
                edit=_edit(snapshot, gross_monthly_salary=Decimal("9999.20")),
                effective_date=date.today(),
                idempotency_key=cdi_key,
                expected_before_hash=contract_state_hash(snapshot),
                expected_person_id=snapshot.person_id,
            )
            result = apply_contract_amendment(port, command=command)
            _require(result.ok is False, "Collision idempotence acceptee.")
            _require(result.code == WriteCode.VALIDATION_ERROR, "Collision mal classee.")
            _require(_amendment_count(db, cdi_key) == 1, "Collision a ajoute un historique.")
            projection = _direct_contract_projection(db, cdi_id)
            _require(
                projection is not None
                and projection["gross_monthly_salary"] == Decimal("9999.10"),
                "Collision a mute le salaire.",
            )
            return {"codes": [result.code]}

        _scenario(
            report,
            "amendment-idempotency-conflict",
            "TEAMWORKS_RAIL_A_STAGE:amendment-idempotency-conflict",
            idempotency_conflict,
        )

        rollback_key = run_id + "-rollback"

        def real_rollback():
            baseline = port.read_contract(cdi_id)
            _require(baseline is not None, "CDI absent avant rollback reel.")
            baseline_hash = contract_state_hash(baseline)
            failing_port = _RollbackFailureAdapter(db)
            command = ContractAmendmentCommand(
                edit=_edit(baseline, gross_monthly_salary=Decimal("9999.20")),
                effective_date=date.today(),
                idempotency_key=rollback_key,
                expected_before_hash=baseline_hash,
                expected_person_id=baseline.person_id,
            )
            result = apply_contract_amendment(failing_port, command=command)
            _require(result.ok is False, "Le rollback force a retourne un succes.")
            _require(result.committed is False, "Le rollback force est marque committed.")

            verify_db = _new_connection()
            try:
                verify_port = GestionDbContractAmendmentAdapter(verify_db)
                after = verify_port.read_contract(cdi_id)
                _require(after is not None, "CDI absent apres rollback.")
                _require(
                    contract_state_hash(after) == baseline_hash,
                    "Projection contrats modifiee malgre rollback.",
                )
                _require(
                    _amendment_count(verify_db, rollback_key) == 0,
                    "Historique avenant persiste malgre rollback.",
                )
            finally:
                try:
                    verify_db.Close()
                except Exception:
                    pass
            return {
                "codes": [result.code],
                "before_hash": baseline_hash,
                "after_hash": baseline_hash,
            }

        _scenario(
            report,
            "amendment-real-rollback",
            "TEAMWORKS_RAIL_A_STAGE:amendment-real-rollback",
            real_rollback,
        )

        readback_key = run_id + "-readback"

        def readback_after_commit():
            baseline = port.read_contract(cdi_id)
            _require(baseline is not None, "CDI absent avant readback post-commit.")
            before_hash = contract_state_hash(baseline)
            failing_port = _ReadbackFailureAfterCommitAdapter(db)
            command = ContractAmendmentCommand(
                edit=_edit(baseline, gross_monthly_salary=Decimal("9999.30")),
                effective_date=date.today(),
                idempotency_key=readback_key,
                expected_before_hash=before_hash,
                expected_person_id=baseline.person_id,
            )
            result = apply_contract_amendment(failing_port, command=command)
            _require(result.ok is False, "Readback force a retourne un succes.")
            _require(result.code == WriteCode.READBACK_ERROR, "Readback force mal classe.")
            _require(result.committed is True, "Commit reel perdu dans le resultat readback.")

            verify_db = _new_connection()
            try:
                verify_port = GestionDbContractAmendmentAdapter(verify_db)
                actual = verify_port.read_contract(cdi_id)
                _require(actual is not None, "CDI absent apres commit/readback perdu.")
                after_hash = contract_state_hash(actual)
                _require(
                    actual.gross_monthly_salary == Decimal("9999.30"),
                    "Projection non persistee apres commit/readback perdu.",
                )
                history = _direct_amendment(verify_db, readback_key)
                _require(history is not None, "Historique absent apres commit/readback perdu.")
                _require(history["after_hash"] == after_hash, "after_hash readback incoherent.")
                _record_amendment_id(report, history["amendment_id"])
            finally:
                try:
                    verify_db.Close()
                except Exception:
                    pass
            return {
                "codes": [result.code],
                "before_hash": before_hash,
                "after_hash": after_hash,
                "amendment_id": history["amendment_id"],
            }

        _scenario(
            report,
            "amendment-readback-after-commit",
            "TEAMWORKS_RAIL_A_STAGE:amendment-readback-after-commit",
            readback_after_commit,
        )

        concurrent_a_key = run_id + "-concurrent-a"
        concurrent_b_key = run_id + "-concurrent-b"

        def concurrency():
            expected = _healthy_snapshot(cdi_id)
            expected_hash = contract_state_hash(expected)
            barrier = threading.Barrier(2, timeout=15)
            results: dict[str, dict[str, object]] = {}
            errors: dict[str, str] = {}
            guard = threading.Lock()

            targets = {
                "a": (Decimal("9999.40"), concurrent_a_key),
                "b": (Decimal("9999.50"), concurrent_b_key),
            }

            def worker(label: str) -> None:
                worker_db = None
                try:
                    worker_db = _new_connection()
                    worker_db.cursor.execute("SET SESSION innodb_lock_wait_timeout=10")
                    worker_port = GestionDbContractAmendmentAdapter(worker_db)
                    initial = worker_port.read_contract(cdi_id)
                    _require(initial is not None, "CDI absent dans worker concurrence.")
                    initial_hash = contract_state_hash(initial)
                    _require(
                        initial_hash == expected_hash,
                        "Les operateurs n'ont pas lu le meme etat initial.",
                    )
                    barrier.wait()
                    salary, key = targets[label]
                    command = ContractAmendmentCommand(
                        edit=_edit(initial, gross_monthly_salary=salary),
                        effective_date=date.today(),
                        idempotency_key=key,
                        expected_before_hash=initial_hash,
                        expected_person_id=initial.person_id,
                    )
                    result = apply_contract_amendment(worker_port, command=command)
                    functional = False
                    try:
                        worker_db.cursor.execute("SELECT 1")
                        functional = worker_db.cursor.fetchone() == (1,)
                    except Exception:
                        functional = False
                    with guard:
                        results[label] = {
                            "code": result.code,
                            "ok": result.ok,
                            "committed": result.committed,
                            "functional_after": functional,
                        }
                except Exception as exc:
                    try:
                        barrier.abort()
                    except Exception:
                        pass
                    with guard:
                        errors[label] = type(exc).__name__
                finally:
                    if worker_db is not None:
                        try:
                            worker_db.Close()
                        except Exception:
                            pass

            thread_a = threading.Thread(target=worker, args=("a",), daemon=True)
            thread_b = threading.Thread(target=worker, args=("b",), daemon=True)
            thread_a.start()
            thread_b.start()
            thread_a.join(timeout=25)
            thread_b.join(timeout=25)
            _require(not thread_a.is_alive() and not thread_b.is_alive(), "Timeout concurrence Rail A.")
            _require(not errors, "Erreur worker concurrence: %s" % sorted(errors))
            _require(set(results) == {"a", "b"}, "Resultats concurrence incomplets.")

            winners = [label for label, item in results.items() if item["code"] == WriteCode.OK]
            losers = [
                label
                for label, item in results.items()
                if item["code"] == CONCURRENT_MODIFICATION
            ]
            _require(len(winners) == 1, "La concurrence n'a pas exactement un succes.")
            _require(len(losers) == 1, "La concurrence n'a pas exactement un conflit.")
            winner = winners[0]
            loser = losers[0]
            _require(results[winner]["ok"] is True, "Le gagnant n'est pas ok.")
            _require(results[winner]["committed"] is True, "Le gagnant n'est pas committed.")
            _require(results[loser]["ok"] is False, "Le perdant est ok.")
            _require(results[loser]["committed"] is False, "Le perdant est committed.")
            _require(results[loser]["functional_after"] is True, "Connexion perdante inutilisable.")

            verify_db = _new_connection()
            try:
                final_projection = _direct_contract_projection(verify_db, cdi_id)
                _require(final_projection is not None, "CDI absent apres concurrence.")
                winner_salary, winner_key = targets[winner]
                _require(
                    final_projection["gross_monthly_salary"] == winner_salary,
                    "Salaire final ne correspond pas au gagnant.",
                )
                history_a = _direct_amendment(verify_db, concurrent_a_key)
                history_b = _direct_amendment(verify_db, concurrent_b_key)
                histories = {"a": history_a, "b": history_b}
                _require(histories[winner] is not None, "Historique gagnant absent.")
                _require(histories[loser] is None, "Historique perdant persiste.")
                _record_amendment_id(report, histories[winner]["amendment_id"])
                final_snapshot = GestionDbContractAmendmentAdapter(verify_db).read_contract(cdi_id)
                _require(final_snapshot is not None, "Snapshot final concurrence absent.")
                final_hash = contract_state_hash(final_snapshot)
            finally:
                try:
                    verify_db.Close()
                except Exception:
                    pass
            return {
                "codes": [results["a"]["code"], results["b"]["code"]],
                "winner": winner,
                "before_hash": expected_hash,
                "after_hash": final_hash,
                "amendment_id": histories[winner]["amendment_id"],
            }

        _scenario(
            report,
            "amendment-concurrency",
            "TEAMWORKS_RAIL_A_STAGE:amendment-concurrency",
            concurrency,
        )

        cdd_key = run_id + "-cdd-renewal"

        def cdd_renewal():
            previous_start = date.today() - timedelta(days=44)
            previous_end = date.today() - timedelta(days=15)
            renewal_start = date.today() - timedelta(days=14)
            renewal_end = date.today() + timedelta(days=14)
            person_id = _safe_person_id(
                db,
                previous_start,
                renewal_end,
            )
            previous_group = _monthly_group(previous_start)
            previous = _create_checked(
                port,
                ContractCreateCommand(
                    person_id=person_id,
                    contract_type_code="CDD",
                    convention_code="CCNS",
                    ccns_group=previous_group,
                    cee_qualification=None,
                    weekly_hours=Decimal("35.00"),
                    gross_monthly_salary=Decimal("9999.00"),
                    gross_annual_salary=None,
                    start_date=previous_start,
                    end_date=previous_end,
                    trial_period_value=0,
                    trial_period_unit="DAY",
                    confirm_no_trial=True,
                ),
                report,
                contract_ids,
            )
            previous_id = int(previous.target_id)
            renewal_group = _monthly_group(renewal_start)
            renewal = _create_checked(
                port,
                ContractCreateCommand(
                    person_id=person_id,
                    contract_type_code="CDD",
                    convention_code="CCNS",
                    ccns_group=renewal_group,
                    cee_qualification=None,
                    weekly_hours=Decimal("35.00"),
                    gross_monthly_salary=Decimal("9999.00"),
                    gross_annual_salary=None,
                    start_date=renewal_start,
                    end_date=renewal_end,
                    trial_period_value=0,
                    trial_period_unit="DAY",
                    confirm_no_trial=True,
                    operation_type=ContractOperation.CDD_RENEWAL.value,
                    previous_contract_id=previous_id,
                ),
                report,
                contract_ids,
            )
            renewal_id = int(renewal.target_id)
            before = port.read_contract(renewal_id)
            _require(before is not None, "CDD renouvele absent avant avenant.")
            _require(
                before.operation_type == ContractOperation.CDD_RENEWAL.value,
                "operation_type CDD_RENEWAL absent avant avenant.",
            )
            _require(before.previous_contract_id == previous_id, "Genealogie CDD absente avant avenant.")
            _require(before.weekly_hours == Decimal("35.00"), "Duree CDD initiale incorrecte.")
            before_hash = contract_state_hash(before)
            command = ContractAmendmentCommand(
                edit=_edit(before, weekly_hours=Decimal("32.00")),
                effective_date=date.today(),
                idempotency_key=cdd_key,
                expected_before_hash=before_hash,
                expected_person_id=before.person_id,
            )
            result = apply_contract_amendment(port, command=command)
            _require(result.ok and result.committed and result.code == WriteCode.OK, "Avenant CDD refuse.")
            after = port.read_contract(renewal_id)
            _require(after is not None, "CDD renouvele absent apres avenant.")
            _require(after.contract_id == renewal_id, "Avenant CDD a change l'ID.")
            _require(after.weekly_hours == Decimal("32.00"), "Duree CDD non modifiee.")
            _require(
                after.operation_type == ContractOperation.CDD_RENEWAL.value,
                "Avenant a detruit operation_type CDD_RENEWAL.",
            )
            _require(
                after.previous_contract_id == previous_id,
                "Avenant a detruit previous_contract_id.",
            )
            history = _direct_amendment(db, cdd_key)
            _require(history is not None, "Historique avenant CDD absent.")
            _require(history["changed_fields"] == "weekly_hours", "changed_fields CDD incorrect.")
            _require(history["kind"] == "WORKING_TIME", "Kind CDD incorrect.")
            after_hash = contract_state_hash(after)
            _require(history["after_hash"] == after_hash, "after_hash CDD incorrect.")
            _record_amendment_id(report, history["amendment_id"])
            return {
                "codes": [previous.code, renewal.code, result.code],
                "previous_contract_id": previous_id,
                "renewal_contract_id": renewal_id,
                "amendment_id": history["amendment_id"],
                "before_hash": before_hash,
                "after_hash": after_hash,
            }

        _scenario(
            report,
            "amendment-cdd-renewal",
            "TEAMWORKS_RAIL_A_STAGE:amendment-cdd-renewal",
            cdd_renewal,
        )

        scenarios_ok = True

    except Exception:
        traceback.print_exc()
        scenarios_ok = False

    finally:
        if port is not None:
            try:
                port.rollback()
            except Exception:
                pass
        if db is not None:
            try:
                db.Close()
            except Exception:
                pass

        try:
            cleanup_ok, cleanup_details = _cleanup_verified(run_id, contract_ids)
            report["cleanup"] = cleanup_details
            print(
                "TEAMWORKS_RAIL_A_CLEANUP:OK"
                if cleanup_ok
                else "TEAMWORKS_RAIL_A_CLEANUP:FAILED",
                flush=True,
            )
        except Exception:
            traceback.print_exc()
            cleanup_ok = False
            report["cleanup"] = {"status": "FAILURE", "error_type": "unexpected"}
            print("TEAMWORKS_RAIL_A_CLEANUP:FAILED", flush=True)

    report["overall"] = "SUCCESS" if scenarios_ok and cleanup_ok else "FAILURE"
    report_ok = True
    try:
        _write_report(report)
    except Exception:
        traceback.print_exc()
        report_ok = False

    if scenarios_ok and cleanup_ok and report_ok:
        print(READY, flush=True)
        return 0

    print(FAILURE, flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
