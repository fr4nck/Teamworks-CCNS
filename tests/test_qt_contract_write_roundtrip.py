from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtWidgets import QApplication  # noqa: E402

from data_adapter import PersonView  # noqa: E402
from infrastructure.persistence.ccns_data_reader import CcnsDataReader  # noqa: E402
from infrastructure.persistence.contract_write_adapter import (  # noqa: E402
    GestionDbContractWriteAdapter,
)
from pilot_view import PeopleContractsPilot  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


class SqliteGestionDbCompat:
    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False
        self.commit_count = 0
        self._create_fixture()

    def _create_fixture(self):
        self.cursor.executescript(
            """
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY,
                prenom TEXT,
                nom TEXT
            );
            CREATE TABLE contrats_class (
                IDclassification INTEGER PRIMARY KEY,
                nom TEXT
            );
            CREATE TABLE contrats_types (
                IDtype INTEGER PRIMARY KEY,
                nom TEXT
            );
            CREATE TABLE contrats (
                IDcontrat INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                IDclassification INTEGER,
                IDtype INTEGER,
                date_debut TEXT,
                date_fin TEXT,
                date_rupture TEXT,
                signature TEXT,
                due TEXT
            );
            INSERT INTO personnes VALUES (12, 'Ada', 'Lovelace');
            INSERT INTO contrats_class VALUES (3, 'Groupe historique');
            INSERT INTO contrats_types VALUES (4, 'CDI');
            INSERT INTO contrats VALUES (
                417, 12, 3, 4, '2026-09-01', '2999-01-01', NULL, '', ''
            );
            """
        )
        self.connexion.commit()

    def GetListeChamps2(self, table_name):
        rows = self.connexion.execute(
            "PRAGMA table_info(%s)" % table_name
        ).fetchall()
        return [(row[1], row[2]) for row in rows]

    def ExecuterReq(self, req):
        self.cursor.execute(req)
        return 1

    def ResultatReq(self):
        return self.cursor.fetchall()

    def Commit(self):
        self.commit_count += 1
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


class RoundTripAdapter:
    def __init__(self, reader):
        self.reader = reader

    def list_people(self):
        return (
            PersonView(
                id="—",
                id_historique=12,
                name="Ada Lovelace",
                first_name="Ada",
                last_name="Lovelace",
                birth_date="—",
                role="—",
                classification="—",
                contract="CDI",
                weekly_hours="—",
                status="—",
                site="—",
                medical="—",
                mutual="—",
            ),
        )

    def list_contracts(self, person_id):
        records = self.reader.lire_contrats_personne(int(person_id))
        return tuple(
            TeamworksProductionReadAdapter._contract_to_view(record)
            for record in records
        )


def _app():
    return QApplication.instance() or QApplication([])


def test_signature_action_roundtrips_qt_service_db_readback_and_refresh():
    _app()
    db = SqliteGestionDbCompat()
    reader = CcnsDataReader(db_factory=lambda: db)
    adapter = RoundTripAdapter(reader)
    window = PeopleContractsPilot(
        adapter,
        contract_write_port_factory=lambda: GestionDbContractWriteAdapter(db),
    )

    try:
        window.people_table.selectRow(0)
        QApplication.processEvents()

        assert window.contracts_model.rowCount() == 1
        before = window.contracts_model.contract_at(0)
        assert before.id_historique == 417
        assert before.signature == ""

        window.contracts_table.selectRow(0)
        QApplication.processEvents()
        assert window.contract_signature_button.isEnabled() is True

        window.contract_signature_button.click()
        QApplication.processEvents()

        stored = db.connexion.execute(
            "SELECT signature, due FROM contrats WHERE IDcontrat=?",
            (417,),
        ).fetchone()
        assert stored == ("Oui", "")
        assert db.commit_count == 1

        refreshed = window.contracts_model.contract_at(0)
        assert refreshed.id_historique == 417
        assert refreshed.signature == "Oui"
        assert window.contracts_table.selectionModel().selectedRows()[0].row() == 0
        assert "Contrat n°417" in window.statusBar().currentMessage()
        assert "Signature : Oui" in window.statusBar().currentMessage()
    finally:
        window.close()
        reader.close()


def test_contract_widget_contains_no_sql():
    source = (POC / "pilot_view.py").read_text(encoding="utf-8")
    assert "SELECT " not in source
    assert "UPDATE " not in source
    assert "DELETE FROM" not in source
    assert "INSERT INTO" not in source
