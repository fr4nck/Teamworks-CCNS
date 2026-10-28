"""User-visible Qt employee-edit journey against a real SQLite file."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
QT_DIR = ROOT / "poc" / "qt-theme"
if str(QT_DIR) not in sys.path:
    sys.path.insert(0, str(QT_DIR))

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox  # noqa: E402
from data_adapter import DemoAdapter, PersonView  # noqa: E402
from infrastructure.persistence.person_generalities_write_adapter import (  # noqa: E402
    GestionDbPersonDetailsWriteAdapter,
)
from person_editor import PersonDetailsEditDialog  # noqa: E402
from pilot_generalities import PeopleContractsGeneralitiesPilot  # noqa: E402


def _app():
    return QApplication.instance() or QApplication([])


def _db_file(tmp_path):
    path = tmp_path / "employees.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY,
                nom TEXT, prenom TEXT, adresse_resid TEXT,
                cp_resid INTEGER, ville_resid TEXT, memo TEXT,
                num_secu TEXT, date_naiss TEXT
            );
            INSERT INTO personnes VALUES (
                12,'DUPONT','Alice','Rue initiale',3510,'Bais',
                'Ancien mémo','DONNEE-SENSIBLE','1990-02-03'
            );
        """)
    return path


class WriteDb:
    def __init__(self, path):
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()
        self.isNetwork = False
        self.echec = 0

    def Close(self):
        self.connexion.close()


class EmployeeAdapter(DemoAdapter):
    def list_people(self):
        return (
            PersonView(
                id="—", id_historique=12,
                name="Alice DUPONT", first_name="Alice", last_name="DUPONT",
                birth_date="—", role="—", classification="—",
                contract="—", weekly_hours="—", status="—", site="—",
                medical="—", mutual="—",
            ),
        )

    def list_contracts(self, _person_id):
        return ()


def _window(path):
    return PeopleContractsGeneralitiesPilot(
        EmployeeAdapter(),
        person_details_write_port_factory=lambda: GestionDbPersonDetailsWriteAdapter(
            WriteDb(path)
        ),
    )


def test_employee_edit_roundtrip_from_selected_row_to_verified_db_and_ui(tmp_path, monkeypatch):
    _app()
    path = _db_file(tmp_path)
    window = _window(path)
    try:
        window.people_table.selectRow(0)
        QApplication.processEvents()
        assert window.person_edit_button.isEnabled()

        def edit(self):
            self.last_name.setText("MARTIN")
            self.first_name.setText("Élodie")
            self.address.setPlainText("5 rue de la Mairie")
            self.postcode.setText("35000")
            self.city.setText("Rennes")
            self.memo.setPlainText("Fiche vérifiée")
            self._validate_and_accept()
            return self.result()

        monkeypatch.setattr(PersonDetailsEditDialog, "exec", edit)
        window.person_edit_button.click()
        QApplication.processEvents()

        with sqlite3.connect(path) as db:
            assert db.execute(
                "SELECT nom,prenom,adresse_resid,cp_resid,ville_resid,memo "
                "FROM personnes WHERE IDpersonne=12"
            ).fetchone() == (
                "MARTIN", "Élodie", "5 rue de la Mairie", 35000,
                "Rennes", "Fiche vérifiée"
            )
            assert db.execute(
                "SELECT num_secu,date_naiss FROM personnes WHERE IDpersonne=12"
            ).fetchone() == ("DONNEE-SENSIBLE", "1990-02-03")
        assert window.people_model.person_at(0).name == "Élodie MARTIN"
        assert window.detail_title.text() == "Élodie MARTIN"
        assert window.generalities_page.memo.toPlainText() == "Fiche vérifiée"
        assert "relue" in window.statusBar().currentMessage().lower()
    finally:
        window.close()
        QApplication.processEvents()


def test_employee_cancel_does_not_write_or_rename_row(tmp_path, monkeypatch):
    _app()
    path = _db_file(tmp_path)
    window = _window(path)
    try:
        window.people_table.selectRow(0)
        QApplication.processEvents()
        monkeypatch.setattr(
            PersonDetailsEditDialog, "exec",
            lambda self: QDialog.DialogCode.Rejected,
        )
        window.person_edit_button.click()
        with sqlite3.connect(path) as db:
            assert db.execute("SELECT nom,memo FROM personnes").fetchone() == (
                "DUPONT", "Ancien mémo"
            )
        assert window.people_model.person_at(0).name == "Alice DUPONT"
        assert "annulée" in window.statusBar().currentMessage()
    finally:
        window.close()
        QApplication.processEvents()


def test_empty_or_invalid_employee_selection_disables_writing(tmp_path):
    _app()
    path = _db_file(tmp_path)
    window = PeopleContractsGeneralitiesPilot(EmployeeAdapter())
    try:
        assert not window.person_edit_button.isEnabled()
        window.people_table.selectRow(0)
        QApplication.processEvents()
        assert not window.person_edit_button.isEnabled()
        window._edit_selected_person()
        with sqlite3.connect(path) as db:
            assert db.execute("SELECT nom FROM personnes").fetchone() == ("DUPONT",)
    finally:
        window.close()
        QApplication.processEvents()


def test_editor_validation_blocks_blank_name_without_commit(tmp_path, monkeypatch):
    _app()
    path = _db_file(tmp_path)
    port = GestionDbPersonDetailsWriteAdapter(WriteDb(path))
    try:
        dialog = PersonDetailsEditDialog(port.load(12))
        alerts = []
        monkeypatch.setattr(QMessageBox, "warning", lambda *args: alerts.append(args))
        dialog.last_name.clear()
        dialog._validate_and_accept()
        assert dialog.result() != QDialog.DialogCode.Accepted
        assert alerts
        with pytest.raises(RuntimeError, match="validation"):
            dialog.values()
        dialog.close()
    finally:
        port.close()
