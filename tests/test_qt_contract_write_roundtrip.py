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

from PySide6.QtCore import QDate, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from contract_editor import ContractCreateDialog, ContractEditDialog  # noqa: E402
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
                nom TEXT,
                nom_abrege TEXT
            );
            CREATE TABLE contrats (
                IDcontrat INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                IDclassification INTEGER,
                IDtype INTEGER,
                valeur_point INTEGER,
                date_debut TEXT,
                date_fin TEXT,
                date_rupture TEXT,
                essai INTEGER,
                signature TEXT,
                due TEXT,
                convention_code TEXT,
                ccns_group TEXT,
                cee_qualification TEXT,
                weekly_hours REAL,
                gross_monthly_salary REAL,
                gross_annual_salary REAL
            );
            INSERT INTO personnes VALUES (12, 'Ada', 'Lovelace');
            INSERT INTO contrats_class VALUES (3, 'Classification historique');
            INSERT INTO contrats_types VALUES (4, 'CDI', 'CDI');
            INSERT INTO contrats VALUES (
                417, 12, NULL, 4, NULL,
                '2026-09-01', '2999-01-01', NULL, 0,
                '', '',
                'CCNS', 'G3', NULL, 35.0, 3000.0, NULL
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

    def ReqInsert(self, table_name, data, commit=True):
        fields = ", ".join(name for name, _value in data)
        placeholders = ", ".join("?" for _name, _value in data)
        values = tuple(value for _name, value in data)
        self.cursor.execute(
            f"INSERT INTO {table_name} ({fields}) VALUES ({placeholders})",
            values,
        )
        inserted = int(self.cursor.lastrowid)
        if commit:
            self.Commit()
        return inserted

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


def _window(db, reader):
    return PeopleContractsPilot(
        RoundTripAdapter(reader),
        contract_write_port_factory=lambda: GestionDbContractWriteAdapter(db),
    )


def _select_contract(window):
    window.people_table.selectRow(0)
    QApplication.processEvents()
    window.contracts_table.selectRow(0)
    QApplication.processEvents()


def test_signature_action_roundtrips_qt_service_db_readback_and_refresh():
    _app()
    db = SqliteGestionDbCompat()
    reader = CcnsDataReader(db_factory=lambda: db)
    window = _window(db, reader)

    try:
        _select_contract(window)

        assert window.contracts_model.rowCount() == 1
        before = window.contracts_model.contract_at(0)
        assert before.id_historique == 417
        assert before.signature == ""
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


def test_modify_action_roundtrips_real_dialog_service_db_readback_and_refresh():
    _app()
    db = SqliteGestionDbCompat()
    reader = CcnsDataReader(db_factory=lambda: db)
    window = _window(db, reader)

    try:
        _select_contract(window)
        before = window.contracts_model.contract_at(0)
        assert before.id_historique == 417
        assert before.start == "01/09/2026"
        assert before.classification == "Groupe 3"
        assert window.contract_edit_button.isEnabled() is True

        def drive_dialog():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, ContractEditDialog)
            dialog.start_date.setDate(QDate(2026, 10, 1))
            group_index = dialog.group.findData("G4")
            assert group_index >= 0
            dialog.group.setCurrentIndex(group_index)
            dialog.weekly_hours.setValue(28.0)
            dialog.monthly_salary.setText("3000,00")
            dialog._on_accept()

        QTimer.singleShot(0, drive_dialog)
        window.contract_edit_button.click()
        QApplication.processEvents()

        stored = db.connexion.execute(
            """
            SELECT date_debut, date_fin, date_rupture,
                   convention_code, ccns_group, weekly_hours,
                   gross_monthly_salary, gross_annual_salary
            FROM contrats
            WHERE IDcontrat=?
            """,
            (417,),
        ).fetchone()
        assert stored == (
            "2026-10-01",
            "2999-01-01",
            None,
            "CCNS",
            "G4",
            28.0,
            3000.0,
            None,
        )
        assert db.commit_count == 1

        refreshed = window.contracts_model.contract_at(0)
        assert refreshed.id_historique == 417
        assert refreshed.start == "01/10/2026"
        assert refreshed.classification == "Groupe 4"
        assert refreshed.duration == "28 h"
        assert window.contracts_table.selectionModel().selectedRows()[0].row() == 0
        assert (
            window.statusBar().currentMessage()
            == "Contrat n°417 modifié et relu depuis la base"
        )
    finally:
        window.close()
        reader.close()



def test_create_action_roundtrips_dialog_insert_commit_readback_and_refresh():
    _app()
    db = SqliteGestionDbCompat()
    reader = CcnsDataReader(db_factory=lambda: db)
    window = _window(db, reader)

    try:
        _select_contract(window)
        assert window.contracts_model.rowCount() == 1
        assert window.contract_create_button.isEnabled() is True

        def drive_create_dialog():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, ContractCreateDialog)
            assert dialog.contract_type.currentData() == "CDI"

            dialog.start_date.setDate(QDate(2026, 11, 1))
            group_index = dialog.group.findData("G4")
            assert group_index >= 0
            dialog.group.setCurrentIndex(group_index)
            dialog.weekly_hours.setValue(28.0)
            dialog.monthly_salary.setText("3000,00")
            dialog._on_accept()

        QTimer.singleShot(0, drive_create_dialog)
        window.contract_create_button.click()
        QApplication.processEvents()

        rows = db.connexion.execute(
            """
            SELECT IDcontrat, IDpersonne, IDclassification, IDtype,
                   date_debut, date_fin, date_rupture, essai,
                   signature, due, convention_code, ccns_group,
                   weekly_hours, gross_monthly_salary, gross_annual_salary
            FROM contrats
            ORDER BY IDcontrat
            """
        ).fetchall()

        assert len(rows) == 2
        created = rows[-1]
        assert created == (
            418,
            12,
            None,
            4,
            "2026-11-01",
            "2999-01-01",
            None,
            61,
            "",
            "",
            "CCNS",
            "G4",
            28.0,
            3000.0,
            None,
        )
        assert db.commit_count == 1

        assert window.contracts_model.rowCount() == 2
        selected_rows = window.contracts_table.selectionModel().selectedRows()
        assert len(selected_rows) == 1
        refreshed = window.contracts_model.contract_at(selected_rows[0].row())
        assert refreshed.id_historique == 418
        assert refreshed.start == "01/11/2026"
        assert refreshed.classification == "Groupe 4"
        assert refreshed.duration == "28 h"
        assert (
            window.statusBar().currentMessage()
            == "Contrat n°418 créé et relu depuis la base"
        )
    finally:
        window.close()
        reader.close()


def test_invalid_business_validation_blocks_write_shows_error_and_preserves_database():
    _app()
    db = SqliteGestionDbCompat()
    reader = CcnsDataReader(db_factory=lambda: db)
    window = _window(db, reader)

    before_db = db.connexion.execute(
        """
        SELECT date_debut, date_fin, date_rupture,
               convention_code, ccns_group, weekly_hours,
               gross_monthly_salary, gross_annual_salary,
               signature, due
        FROM contrats
        WHERE IDcontrat=?
        """,
        (417,),
    ).fetchone()
    observed = {}

    try:
        _select_contract(window)
        assert window.contract_edit_button.isEnabled() is True

        def drive_invalid_dialog():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, ContractEditDialog)

            # Modification volontairement invalide : salaire très inférieur
            # au minimum CCNS/SMIC pour le groupe et la durée sélectionnés.
            dialog.monthly_salary.setText("1,00")
            dialog._on_accept()
            QApplication.processEvents()

            observed["error"] = dialog.error_label.text()
            observed["accepted"] = dialog.result()
            observed["still_visible"] = dialog.isVisible()

            # La validation invalide doit laisser le dialogue ouvert.
            dialog.reject()

        QTimer.singleShot(0, drive_invalid_dialog)
        window.contract_edit_button.click()
        QApplication.processEvents()

        after_db = db.connexion.execute(
            """
            SELECT date_debut, date_fin, date_rupture,
                   convention_code, ccns_group, weekly_hours,
                   gross_monthly_salary, gross_annual_salary,
                   signature, due
            FROM contrats
            WHERE IDcontrat=?
            """,
            (417,),
        ).fetchone()

        assert "minimum CCNS/SMIC" in observed["error"]
        assert observed["accepted"] == 0
        assert observed["still_visible"] is True
        assert db.commit_count == 0
        assert after_db == before_db

        refreshed = window.contracts_model.contract_at(0)
        assert refreshed.id_historique == 417
        assert refreshed.start == "01/09/2026"
        assert refreshed.classification == "Groupe 3"
        assert refreshed.duration == "35 h"
    finally:
        window.close()
        reader.close()


def test_contract_widgets_contain_no_sql():
    for filename in ("pilot_view.py", "contract_editor.py"):
        source = (POC / filename).read_text(encoding="utf-8")
        assert "SELECT " not in source
        assert "UPDATE " not in source
        assert "DELETE FROM" not in source
        assert "INSERT INTO" not in source
