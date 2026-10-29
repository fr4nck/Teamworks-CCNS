"""Écriture de contrat face à une autre session, une base verrouillée ou perdue.

Deux connexions SQLite réelles sur le même fichier : « Qt » (adaptateur de
production) et « autre poste » (connexion brute, comme Teamworks wx).
"""
from __future__ import annotations

import sqlite3
from dataclasses import replace
from decimal import Decimal

import pytest

from application.services.contract_write import ContractEditCommand, update_contract
from application.services.transactional_write import WriteCode
from infrastructure.persistence.contract_write_adapter import GestionDbContractWriteAdapter

SCHEMA = """
CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, prenom TEXT, nom TEXT);
CREATE TABLE contrats_types (IDtype INTEGER PRIMARY KEY, nom TEXT, nom_abrege TEXT);
CREATE TABLE contrats_valchamps (IDval_champ INTEGER PRIMARY KEY, IDcontrat INTEGER);
CREATE TABLE contrats (
    IDcontrat INTEGER PRIMARY KEY, IDpersonne INTEGER, IDclassification INTEGER,
    IDtype INTEGER, valeur_point INTEGER, date_debut TEXT, date_fin TEXT,
    date_rupture TEXT, essai INTEGER, signature TEXT, due TEXT,
    convention_code TEXT, ccns_group TEXT, cee_qualification TEXT,
    weekly_hours REAL, gross_monthly_salary REAL, gross_annual_salary REAL
);
INSERT INTO personnes VALUES (12, 'Ada', 'Lovelace');
INSERT INTO contrats_types VALUES (4, 'CDI', 'CDI');
INSERT INTO contrats VALUES (417, 12, NULL, 4, NULL, '2026-09-01', '2999-01-01', NULL, 0,
    '', '', 'CCNS', 'G3', NULL, 35.0, 3000.0, NULL);
"""


class FileGestionDb:
    """Sous-ensemble GestionDB utilisé par l'adaptateur, sur un vrai fichier."""

    def __init__(self, path, timeout=0.2):
        self.nomFichier = str(path)
        self.connexion = sqlite3.connect(str(path), timeout=timeout)
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False

    def GetListeChamps2(self, table):
        return [(r[1], r[2]) for r in self.connexion.execute("PRAGMA table_info(%s)" % table)]

    def Commit(self):
        self.connexion.commit()


@pytest.fixture
def base(tmp_path):
    path = tmp_path / "Recette_TDATA.dat"
    with sqlite3.connect(path) as c:
        c.executescript(SCHEMA)
    return path


def _command(snapshot, **changes) -> ContractEditCommand:
    command = ContractEditCommand(
        contract_id=snapshot.contract_id,
        contract_type_code=snapshot.contract_type_code,
        convention_code=snapshot.convention_code,
        ccns_group=snapshot.ccns_group,
        cee_qualification=snapshot.cee_qualification,
        weekly_hours=snapshot.weekly_hours,
        gross_monthly_salary=snapshot.gross_monthly_salary,
        gross_annual_salary=snapshot.gross_annual_salary,
        start_date=snapshot.start_date,
        end_date=snapshot.end_date,
        break_date=snapshot.break_date,
        modern_fields_supported=snapshot.modern_fields_supported,
    )
    return replace(command, **changes)


def _row(path):
    with sqlite3.connect(path) as c:
        return c.execute(
            "SELECT weekly_hours, gross_monthly_salary FROM contrats WHERE IDcontrat=417"
        ).fetchone()


def test_change_by_another_session_after_opening_is_refused_not_overwritten(base):
    db = FileGestionDb(base)
    port = GestionDbContractWriteAdapter(db)
    opened = port.read_contract(417)

    with sqlite3.connect(base) as other:
        other.execute("UPDATE contrats SET weekly_hours=30.0 WHERE IDcontrat=417")

    result = update_contract(
        port, command=_command(opened, gross_monthly_salary=Decimal("3100.00")), expected=opened
    )
    assert result.code == WriteCode.CONFLICT and not result.committed
    assert "autre session" in result.message
    assert _row(base) == (30.0, 3000.0)
    assert not db.connexion.in_transaction
    db.connexion.close()


def test_unchanged_contract_is_saved_and_every_value_read_back(base):
    db = FileGestionDb(base)
    port = GestionDbContractWriteAdapter(db)
    opened = port.read_contract(417)
    result = update_contract(
        port,
        command=_command(opened, weekly_hours=Decimal("28.00"), gross_monthly_salary=Decimal("2550.55")),
        expected=opened,
    )
    assert result.ok and result.committed, result.message
    assert result.value.weekly_hours == Decimal("28.00")
    assert _row(base) == (28.0, 2550.55)
    db.connexion.close()


def test_base_locked_by_another_writer_is_reported_and_nothing_written(base):
    db = FileGestionDb(base)
    port = GestionDbContractWriteAdapter(db)
    opened = port.read_contract(417)
    other = sqlite3.connect(base)
    other.execute("BEGIN IMMEDIATE")
    other.execute("UPDATE contrats SET due='Oui' WHERE IDcontrat=417")
    try:
        result = update_contract(
            port, command=_command(opened, weekly_hours=Decimal("20.00")), expected=opened
        )
        assert result.code == WriteCode.DATABASE_ERROR and not result.committed
        assert "occupée" in result.message
        assert not db.connexion.in_transaction
    finally:
        other.rollback()
        other.close()
    assert _row(base) == (35.0, 3000.0)

    retry = update_contract(
        port, command=_command(opened, weekly_hours=Decimal("20.00")), expected=opened
    )
    assert retry.ok and retry.committed, retry.message
    assert _row(base) == (20.0, 3000.0)
    db.connexion.close()


def test_value_altered_after_commit_is_not_reported_as_verified(base):
    with sqlite3.connect(base) as c:
        c.execute(
            "CREATE TRIGGER altere AFTER UPDATE ON contrats BEGIN "
            "UPDATE contrats SET weekly_hours=99 WHERE IDcontrat=NEW.IDcontrat; END"
        )
    db = FileGestionDb(base)
    port = GestionDbContractWriteAdapter(db)
    opened = port.read_contract(417)
    result = update_contract(
        port, command=_command(opened, weekly_hours=Decimal("28.00")), expected=opened
    )
    assert result.committed and not result.ok
    assert result.code == WriteCode.READBACK_ERROR
    assert "weekly_hours" in result.message
    db.connexion.close()


def test_lost_connection_during_save_is_an_explicit_failure(base):
    db = FileGestionDb(base)
    port = GestionDbContractWriteAdapter(db)
    opened = port.read_contract(417)
    db.connexion.close()
    result = update_contract(
        port, command=_command(opened, weekly_hours=Decimal("28.00")), expected=opened
    )
    assert not result.ok and not result.committed
    assert result.code == WriteCode.DATABASE_ERROR
    assert _row(base) == (35.0, 3000.0)


def test_failed_read_query_raises_instead_of_returning_an_empty_list():
    from infrastructure.persistence.ccns_data_reader import CcnsDataReader
    from infrastructure.persistence.person_reader import PersonReader

    class SwallowingDb:
        """Comme GestionDB : l'erreur SQL est imprimée et ExecuterReq renvoie 0."""
        echec = 0
        isNetwork = False

        def ExecuterReq(self, req):
            return 0

        def ResultatReq(self):
            return []

        def GetListeChamps2(self, table):
            return []

        def Close(self):
            pass

    with pytest.raises(RuntimeError, match="Lecture impossible"):
        PersonReader(db_factory=SwallowingDb).lire_identites()
    with pytest.raises(RuntimeError, match="Lecture impossible"):
        CcnsDataReader(db_factory=SwallowingDb).lire_contrats_personne(12)
