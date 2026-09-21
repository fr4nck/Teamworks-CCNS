from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtCore import QDate, QTimer, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from data_adapter import PersonView, ReimbursementView, TripView  # noqa: E402
from infrastructure.persistence.expense_reimbursement_write_adapter import (  # noqa: E402
    GestionDbReimbursementWriteAdapter,
)
from pilot_generalities import PeopleContractsGeneralitiesPilot  # noqa: E402
from scenario_expense_dialogs import ReimbursementPreviewDialog  # noqa: E402


class SqliteGestionDbCompat:
    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False
        self.commit_count = 0
        self.cursor.executescript(
            """
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY
            );
            CREATE TABLE remboursements (
                IDremboursement INTEGER PRIMARY KEY AUTOINCREMENT,
                IDpersonne INTEGER,
                date TEXT,
                montant REAL,
                listeIDdeplacement TEXT
            );
            CREATE TABLE deplacements (
                IDdeplacement INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                date TEXT,
                objet TEXT,
                ville_depart TEXT,
                ville_arrivee TEXT,
                distance REAL,
                aller_retour TEXT,
                tarif_km REAL,
                IDremboursement INTEGER
            );
            INSERT INTO personnes VALUES (12);
            INSERT INTO deplacements VALUES
                (7, 12, '2026-09-10', 'Réunion', 'Bruz', 'Rennes', 20, 'False', 0.50, 0),
                (8, 12, '2026-09-11', 'Formation', 'Bruz', 'Vitré', 50, 'False', 0.40, 0);
            """
        )
        self.connexion.commit()

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


class ExpenseRoundTripAdapter:
    def __init__(self, db):
        self.db = db

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
                contract="—",
                weekly_hours="—",
                status="—",
                site="—",
                medical="—",
                mutual="—",
            ),
        )

    def get_person_generalities(self, person_id):
        return None

    def list_contracts(self, person_id):
        return ()

    def list_scenarios(self, person_id):
        return ()

    def list_trips(self, person_id):
        rows = self.db.connexion.execute(
            """
            SELECT IDdeplacement, date, objet, ville_depart, ville_arrivee,
                   distance, tarif_km, IDremboursement
            FROM deplacements
            WHERE IDpersonne=?
            ORDER BY IDdeplacement
            """,
            (int(person_id),),
        ).fetchall()
        result = []
        for row in rows:
            reimbursement_id = int(row[7]) if row[7] not in (None, 0) else None
            result.append(
                TripView(
                    number=str(row[0]),
                    date=row[1],
                    purpose=row[2],
                    route=f"{row[3]} -> {row[4]}",
                    distance=f"{row[5]} Km",
                    tariff=f"{row[6]} €/km",
                    amount=f"{Decimal(str(row[5])) * Decimal(str(row[6])):.2f} €",
                    reimbursement="" if reimbursement_id is None else f"N°{reimbursement_id}",
                    id_historique=int(row[0]),
                    reimbursement_id=reimbursement_id,
                )
            )
        return tuple(result)

    def list_reimbursements(self, person_id):
        rows = self.db.connexion.execute(
            """
            SELECT IDremboursement, date, montant, listeIDdeplacement
            FROM remboursements
            WHERE IDpersonne=?
            ORDER BY IDremboursement
            """,
            (int(person_id),),
        ).fetchall()
        result = []
        for reimbursement_id, payment_date, amount, trip_text in rows:
            trip_ids = tuple(
                int(value)
                for value in str(trip_text or "").split("-")
                if str(value).strip()
            )
            result.append(
                ReimbursementView(
                    number=str(reimbursement_id),
                    date=payment_date,
                    amount=f"{Decimal(str(amount)):.2f} €",
                    attached_trips=(
                        "Aucun déplacement rattaché"
                        if not trip_ids
                        else "N° " + ", ".join(str(value) for value in trip_ids)
                    ),
                    id_historique=int(reimbursement_id),
                    payment_date_value=date.fromisoformat(payment_date),
                    amount_value=Decimal(str(amount)),
                    attached_trip_ids=trip_ids,
                )
            )
        return tuple(result)


def _app():
    return QApplication.instance() or QApplication([])


def _window(db):
    return PeopleContractsGeneralitiesPilot(
        ExpenseRoundTripAdapter(db),
        reimbursement_write_port_factory=lambda: GestionDbReimbursementWriteAdapter(db),
    )


def _select_person(window):
    window.people_table.selectRow(0)
    QApplication.processEvents()


def test_reimbursement_create_then_modify_roundtrips_qt_service_db_and_refresh():
    _app()
    db = SqliteGestionDbCompat()
    window = _window(db)

    try:
        _select_person(window)
        page = window.legacy_tabs.expenses_page
        assert page.reimbursement_actions.button("add").isEnabled() is True
        assert page.trip_model.rowCount() == 2

        def drive_create():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, ReimbursementPreviewDialog)
            dialog.date_edit.setDate(QDate(2026, 9, 30))
            dialog.amount_edit.setText("10,00")
            model = dialog.trip_table.model()
            assert model.rowCount() == 2
            model.item(0, 0).setCheckState(Qt.CheckState.Checked)
            dialog._validate_and_accept()

        QTimer.singleShot(0, drive_create)
        page.reimbursement_actions.button("add").click()
        QApplication.processEvents()

        assert db.connexion.execute(
            "SELECT IDpersonne, date, montant, listeIDdeplacement FROM remboursements"
        ).fetchone() == (12, "2026-09-30", 10.0, "7")
        assert db.connexion.execute(
            "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
        ).fetchall() == [(7, 1), (8, 0)]
        assert db.commit_count == 1
        assert page.reimbursement_model.rowCount() == 1
        selected = page._selected_reimbursement()
        assert selected.id_historique == 1
        assert selected.attached_trip_ids == (7,)
        assert page.reimbursement_actions.button("edit").isEnabled() is True

        def drive_edit():
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, ReimbursementPreviewDialog)
            assert dialog.reimbursement.id_historique == 1
            dialog.amount_edit.setText("20.00")
            model = dialog.trip_table.model()
            assert model.rowCount() == 2
            model.item(0, 0).setCheckState(Qt.CheckState.Unchecked)
            model.item(1, 0).setCheckState(Qt.CheckState.Checked)
            dialog._validate_and_accept()

        QTimer.singleShot(0, drive_edit)
        page.reimbursement_actions.button("edit").click()
        QApplication.processEvents()

        assert db.connexion.execute(
            "SELECT date, montant, listeIDdeplacement FROM remboursements WHERE IDremboursement=1"
        ).fetchone() == ("2026-09-30", 20.0, "8")
        assert db.connexion.execute(
            "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
        ).fetchall() == [(7, 0), (8, 1)]
        assert db.commit_count == 2
        refreshed = page._selected_reimbursement()
        assert refreshed.id_historique == 1
        assert refreshed.amount_value == Decimal("20.0")
        assert refreshed.attached_trip_ids == (8,)
        assert "Remboursement enregistré" in window.statusBar().currentMessage()
        assert page.reimbursement_actions.button("delete").isEnabled() is True

        observed = []

        def confirm_final_delete():
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            observed.append(box.text())
            yes = box.button(QMessageBox.StandardButton.Yes)
            assert yes is not None
            yes.click()

        def confirm_attached_delete():
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            observed.append(box.text())
            QTimer.singleShot(0, confirm_final_delete)
            yes = box.button(QMessageBox.StandardButton.Yes)
            assert yes is not None
            yes.click()

        QTimer.singleShot(0, confirm_attached_delete)
        page.reimbursement_actions.button("delete").click()
        QApplication.processEvents()

        assert len(observed) == 2
        assert "1 déplacement(s) rattaché(s)" in observed[0]
        assert "remboursement n°1" in observed[1]
        assert db.connexion.execute(
            "SELECT IDremboursement FROM remboursements WHERE IDremboursement=1"
        ).fetchone() is None
        assert db.connexion.execute(
            "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
        ).fetchall() == [(7, 0), (8, 0)]
        assert db.commit_count == 3
        assert page.reimbursement_model.rowCount() == 0
        assert page.reimbursement_actions.button("edit").isEnabled() is False
        assert page.reimbursement_actions.button("delete").isEnabled() is False
        assert "supprimé" in window.statusBar().currentMessage()
    finally:
        window.close()


def test_expenses_qt_widgets_contain_no_sql_statements():
    source = (POC / "individual_pages.py").read_text(encoding="utf-8")
    dialogs = (POC / "scenario_expense_dialogs.py").read_text(encoding="utf-8")
    upper = (source + "\n" + dialogs).upper()
    for token in ("SELECT ", "UPDATE ", "INSERT ", "DELETE "):
        assert token not in upper



def test_reimbursement_delete_cancel_keeps_parent_and_trips_unchanged():
    _app()
    db = SqliteGestionDbCompat()
    db.connexion.execute(
        "INSERT INTO remboursements VALUES (1, 12, '2026-09-30', 10.0, '7')"
    )
    db.connexion.execute(
        "UPDATE deplacements SET IDremboursement=1 WHERE IDdeplacement=7"
    )
    db.connexion.commit()
    window = _window(db)

    try:
        _select_person(window)
        page = window.legacy_tabs.expenses_page
        page.reimbursement_table.selectRow(0)
        QApplication.processEvents()
        assert page.reimbursement_actions.button("delete").isEnabled() is True

        def cancel_attached_delete():
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            no = box.button(QMessageBox.StandardButton.No)
            assert no is not None
            no.click()

        QTimer.singleShot(0, cancel_attached_delete)
        page.reimbursement_actions.button("delete").click()
        QApplication.processEvents()

        assert db.commit_count == 0
        assert db.connexion.execute(
            "SELECT IDremboursement FROM remboursements WHERE IDremboursement=1"
        ).fetchone() == (1,)
        assert db.connexion.execute(
            "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=7"
        ).fetchone() == (1,)
        assert page.reimbursement_model.rowCount() == 1
        assert window.statusBar().currentMessage() == "Suppression annulée · aucune écriture"
    finally:
        window.close()
