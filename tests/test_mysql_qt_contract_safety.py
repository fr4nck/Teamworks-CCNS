"""Recette MySQL synthétique du parcours Qt individu → contrat (gate CI Windows + MySQL).

Base créée pour le test sur le serveur MySQL éphémère de la CI, avec le schéma
historique ``DATA_Tables`` construit par ``GestionDB.CreationTables`` ; aucune
donnée réelle. Ne qualifie pas une copie représentative : ce gate reste distinct.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

if os.environ.get("TEAMWORKS_MYSQL_INTEGRATION") != "1":
    pytest.skip("Recette MySQL activée uniquement dans le gate Windows dédié.", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "teamworks"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import mysql.connector  # noqa: E402
import GestionDB  # noqa: E402
from Data import DATA_Tables as Tables  # noqa: E402

from application.services.contract_write import (  # noqa: E402
    ContractCreateCommand,
    ContractEditCommand,
    create_contract,
    update_contract,
)
from application.services.person_generalities_write import (  # noqa: E402
    PersonDetails,
    save_person_details,
)
from application.services.transactional_write import WriteCode  # noqa: E402
from infrastructure.persistence.ccns_data_reader import CcnsDataReader  # noqa: E402
from infrastructure.persistence.contract_schema_evolution import (  # noqa: E402
    add_contract_engine_columns,
)
from infrastructure.persistence.contract_write_adapter import (  # noqa: E402
    GestionDbContractWriteAdapter,
)
from infrastructure.persistence.person_generalities_write_adapter import (  # noqa: E402
    GestionDbPersonDetailsWriteAdapter,
)
from infrastructure.persistence.qt_schema_compatibility import (  # noqa: E402
    CONTRACT_ENGINE_COLUMNS,
    check_schema,
)

HOST = os.environ.get("TEAMWORKS_MYSQL_HOST", "127.0.0.1")
PORT = int(os.environ.get("TEAMWORKS_MYSQL_PORT", "3307"))
USER = os.environ.get("TEAMWORKS_MYSQL_USER", "root")
PASSWORD = os.environ.get("TEAMWORKS_MYSQL_PASSWORD", "")
DB_NAME = "teamworks_qt_contrat_ci"
UNTOUCHED = ("contrats_class", "contrats_types", "valeurs_point", "parametres")


_OPEN_SESSIONS = []


def _admin():
    connection = mysql.connector.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD,
        use_pure=True, ssl_disabled=True, connection_timeout=10,
    )
    cursor = connection.cursor()
    cursor.execute("SET SESSION lock_wait_timeout=10")
    cursor.close()
    return connection


def _session():
    db = GestionDB.DB(nomFichier=f"{PORT};{HOST};{USER};{PASSWORD}[RESEAU]{DB_NAME}", suffixe=None)
    assert db.echec == 0, getattr(db, "erreur", None)
    assert db.isNetwork is True
    # Une attente de verrou (ligne ou métadonnées) doit échouer vite, jamais bloquer la CI.
    db.cursor.execute("SET SESSION lock_wait_timeout=10")
    db.cursor.execute("SET SESSION innodb_lock_wait_timeout=10")
    _OPEN_SESSIONS.append(db)
    return db


def _close_all_sessions():
    """Une session laissée ouverte par un test en échec bloquerait le DROP DATABASE suivant."""
    while _OPEN_SESSIONS:
        db = _OPEN_SESSIONS.pop()
        try:
            db.connexion.rollback()
        except Exception:
            pass
        db.Close()


def _checksums(db, tables):
    db.cursor.execute("CHECKSUM TABLE " + ", ".join(tables))
    return {row[0].split(".")[-1]: row[1] for row in db.cursor.fetchall()}


@pytest.fixture()
def base():
    admin = _admin()
    cursor = admin.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8 COLLATE utf8_unicode_ci")
    cursor.close()
    admin.close()

    try:
        db = _session()
        db.CreationTables(Tables.DB_DATA)
        db.cursor.execute(
            "INSERT INTO parametres (categorie, nom, parametre) VALUES ('fichier', 'version', '2.1.2.0')"
        )
        db.cursor.execute("INSERT INTO personnes (IDpersonne, nom, prenom, ville_resid) VALUES (12, 'MARTIN', 'Ada', 'BREST')")
        db.cursor.execute("INSERT INTO contrats_types (IDtype, nom, nom_abrege, duree_indeterminee) VALUES (4, 'Contrat à Durée Indéterminée', 'CDI', 'oui')")
        db.Commit()
        yield db
    finally:
        _close_all_sessions()
        admin = _admin()
        cursor = admin.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cursor.close()
        admin.close()


def _edit(snapshot, **changes) -> ContractEditCommand:
    values = dict(
        contract_id=snapshot.contract_id, contract_type_code=snapshot.contract_type_code,
        convention_code=snapshot.convention_code, ccns_group=snapshot.ccns_group,
        cee_qualification=snapshot.cee_qualification, weekly_hours=snapshot.weekly_hours,
        gross_monthly_salary=snapshot.gross_monthly_salary,
        gross_annual_salary=snapshot.gross_annual_salary, start_date=snapshot.start_date,
        end_date=snapshot.end_date, break_date=snapshot.break_date,
        modern_fields_supported=snapshot.modern_fields_supported,
    )
    values.update(changes)
    return ContractEditCommand(**values)


def test_historic_mysql_schema_full_contract_journey_with_new_connection_readback(base):
    # Base wx antérieure aux colonnes CCNS : schéma historique sans les 10 colonnes additives.
    for name, _type in CONTRACT_ENGINE_COLUMNS:
        base.cursor.execute("ALTER TABLE contrats DROP COLUMN %s" % name)
    report = check_schema(base)
    assert report.missing_contract_columns
    assert report.compatible, report.blocking_text()

    # Qt ne peut pas sauvegarder une base réseau : l'ajout des colonnes est refusé, rien ne change.
    refused = add_contract_engine_columns(base)
    assert not refused.ok and "MySQL" in refused.message
    assert check_schema(base).missing_contract_columns == report.missing_contract_columns
    types = dict(CONTRACT_ENGINE_COLUMNS)
    for name in report.missing_contract_columns:  # geste de l'administrateur
        base.AjoutChamp(nomTable="contrats", nomChamp=name, typeChamp=types[name])
    assert check_schema(base).contract_writes_ready
    before = _checksums(base, UNTOUCHED)

    port = GestionDbContractWriteAdapter(base)
    created = create_contract(port, command=ContractCreateCommand(
        person_id=12, contract_type_code="CDI", convention_code="CCNS", ccns_group="G4",
        cee_qualification=None, weekly_hours=Decimal("28.00"),
        gross_monthly_salary=Decimal("3000.00"), gross_annual_salary=None,
        start_date=date(2026, 11, 2), end_date=None,
        trial_period_value=2, trial_period_unit="MONTH",
    ))
    assert created.ok and created.committed, created.message
    contract_id = created.target_id

    opened = port.read_contract(contract_id)
    edited = update_contract(port, command=_edit(opened, gross_monthly_salary=Decimal("3100.00")), expected=opened)
    assert edited.ok and edited.committed, edited.message

    person = GestionDbPersonDetailsWriteAdapter(_session())
    snapshot = person.load(12)
    saved = save_person_details(person, snapshot, PersonDetails(
        last_name="MARTIN-RECETTE", first_name="Ada", address=None, postcode=None,
        city="QUIMPER", memo="Recette MySQL synthétique"))
    assert saved.committed and saved.verified, saved.message
    person.close()

    fresh = _session()
    try:
        reread = GestionDbContractWriteAdapter(fresh).read_contract(contract_id)
        assert reread.gross_monthly_salary == Decimal("3100.00")
        assert reread.weekly_hours == Decimal("28.00") and reread.ccns_group == "G4"
        assert reread.start_date == date(2026, 11, 2) and reread.end_date is None
        listed = CcnsDataReader(db_factory=lambda: fresh).lire_contrats_personne(12)
        assert [record.IDcontrat for record in listed] == [contract_id]
        fresh.cursor.execute("SELECT nom, ville_resid, memo FROM personnes WHERE IDpersonne=12")
        assert fresh.cursor.fetchone() == ("MARTIN-RECETTE", "QUIMPER", "Recette MySQL synthétique")
        assert _checksums(fresh, UNTOUCHED) == before
    finally:
        fresh.Close()


def _ready_contract(base):
    types = dict(CONTRACT_ENGINE_COLUMNS)
    for name in check_schema(base).missing_contract_columns:
        base.AjoutChamp(nomTable="contrats", nomChamp=name, typeChamp=types[name])
    port = GestionDbContractWriteAdapter(base)
    created = create_contract(port, command=ContractCreateCommand(
        person_id=12, contract_type_code="CDI", convention_code="CCNS", ccns_group="G4",
        cee_qualification=None, weekly_hours=Decimal("28.00"),
        gross_monthly_salary=Decimal("3000.00"), gross_annual_salary=None,
        start_date=date(2026, 11, 2), end_date=None, trial_period_value=2, trial_period_unit="MONTH",
    ))
    assert created.ok, created.message
    return port, created.target_id


def _salary(contract_id):
    db = _session()
    try:
        db.cursor.execute("SELECT gross_monthly_salary, weekly_hours FROM contrats WHERE IDcontrat=%s", (contract_id,))
        return tuple(float(value) for value in db.cursor.fetchone())
    finally:
        db.Close()


def test_mysql_change_by_another_session_is_refused_not_overwritten(base):
    port, contract_id = _ready_contract(base)
    opened = port.read_contract(contract_id)
    base.Commit()  # fin de la transaction de lecture (instantané REPEATABLE READ)

    other = _session()
    other.cursor.execute("UPDATE contrats SET weekly_hours=30 WHERE IDcontrat=%s", (contract_id,))
    other.Commit()
    other.Close()

    result = update_contract(port, command=_edit(opened, gross_monthly_salary=Decimal("3200.00")), expected=opened)
    assert result.code == WriteCode.CONFLICT and not result.committed, result.message
    assert _salary(contract_id) == (3000.0, 30.0)


def test_mysql_row_locked_by_another_session_fails_cleanly_then_retry_succeeds(base):
    port, contract_id = _ready_contract(base)
    opened = port.read_contract(contract_id)
    base.Commit()
    base.cursor.execute("SET SESSION innodb_lock_wait_timeout=2")

    holder = _session()
    holder.cursor.execute("SELECT IDcontrat FROM contrats WHERE IDcontrat=%s FOR UPDATE", (contract_id,))
    holder.cursor.fetchall()
    try:
        result = update_contract(port, command=_edit(opened, gross_monthly_salary=Decimal("3300.00")), expected=opened)
        assert result.code == WriteCode.DATABASE_ERROR and not result.committed, result.message
    finally:
        holder.connexion.rollback()
        holder.Close()
    assert _salary(contract_id) == (3000.0, 28.0)

    retry = update_contract(port, command=_edit(opened, gross_monthly_salary=Decimal("3300.00")), expected=opened)
    assert retry.ok and retry.committed, retry.message
    assert _salary(contract_id) == (3300.0, 28.0)


def _diagnose(password):
    from infrastructure.persistence.mysql_connection_diagnostic import run_mysql_diagnostic

    def schema():
        db = _session()
        try:
            return check_schema(db)
        finally:
            _OPEN_SESSIONS.remove(db)
            db.Close()

    return run_mysql_diagnostic(
        f"{PORT};{HOST};{USER};{GestionDB.EncodeMdpReseau(password)}[RESEAU]{DB_NAME}",
        suffix="",
        connector=mysql.connector,
        open_connection=GestionDB.GetConnexionReseau,
        check_schema=schema,
        decode_password=GestionDB.DecodeMdpReseau,
        tls_label="désactivé",
    )


def test_mysql_diagnostic_passes_the_five_steps_on_this_server(base):
    before = _checksums(base, UNTOUCHED)
    report = _diagnose(PASSWORD)
    text = report.text()
    print(text)
    assert report.ok, text
    assert "Modules dynamiques du pilote : tous présents" in text
    expected = os.environ.get("TEAMWORKS_MYSQL_EXPECTED_VERSION")
    if expected:
        assert f"serveur MySQL {expected}" in report.steps[1].detail, text
    assert PASSWORD == "" or PASSWORD not in text
    assert _checksums(base, UNTOUCHED) == before


def test_mysql_diagnostic_reports_a_rejected_password_as_authentication(base):
    wrong = "mauvais-mdp-fictif"
    report = _diagnose(wrong)
    text = report.text()
    print(text)
    assert [step.status for step in report.steps[:4]] == ["OK", "OK", "ÉCHEC", "NON TESTÉ"], text
    assert "1045" in report.steps[2].detail and "identifiant ou mot de passe refusé" in report.steps[2].detail
    assert "ImportError" not in text and wrong not in text
    assert GestionDB.EncodeMdpReseau(wrong) not in text


def test_mysql_non_transactional_tables_are_refused_by_the_precheck(base):
    base.cursor.execute("ALTER TABLE contrats ENGINE=MyISAM")
    report = check_schema(base)
    assert not report.compatible
    assert "contrats" in report.blocking_text() and "InnoDB" in report.blocking_text()
