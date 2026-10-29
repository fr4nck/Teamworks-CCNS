"""Non-régressions des défauts reproduits lors de la recette Windows réelle Qt.

Recette : vrai launcher, adaptateurs production, GestionDB sur une copie
fictive de Static/Exemples/Exemple_TDATA.dat, événements QTest.
"""
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
for path in (POC, ROOT / "teamworks", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from PySide6.QtCore import QObject, QThread, Signal, Slot  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialogButtonBox  # noqa: E402

from application.services.contract_write import ContractCreateCommand  # noqa: E402
from contract_editor import _money_text  # noqa: E402
from data_adapter import PersonView  # noqa: E402
from infrastructure.persistence.ccns_data_reader import CcnsDataReader  # noqa: E402
from infrastructure.persistence.legacy_table_ddl import legacy_add_column_query  # noqa: E402
import launcher  # noqa: E402
from pilot_view import PeopleContractsPilot  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


def _app():
    return QApplication.instance() or QApplication([])


class LegacySqliteDb:
    """GestionDB minimal : base historique sans les colonnes CCNS des contrats."""

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.isNetwork = False
        self.cursor.executescript(
            """
            CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, prenom TEXT, nom TEXT);
            CREATE TABLE contrats_types (IDtype INTEGER PRIMARY KEY, nom TEXT, nom_abrege TEXT);
            CREATE TABLE contrats_class (IDclassification INTEGER PRIMARY KEY, nom TEXT);
            CREATE TABLE contrats_valchamps (IDval_champ INTEGER PRIMARY KEY, IDcontrat INTEGER);
            CREATE TABLE contrats (
                IDcontrat INTEGER PRIMARY KEY AUTOINCREMENT, IDpersonne INTEGER,
                IDclassification INTEGER, IDtype INTEGER, valeur_point INTEGER,
                date_debut TEXT, date_fin TEXT, date_rupture TEXT, essai INTEGER,
                signature TEXT, due TEXT
            );
            INSERT INTO personnes VALUES (2, 'Aurélie', 'GUEGUEN');
            INSERT INTO contrats_types VALUES (2, 'Contrat à Durée Indéterminée', 'CDI');
            """
        )

    def GetListeChamps2(self, table_name):
        return [(row[1], row[2]) for row in self.connexion.execute(f"PRAGMA table_info({table_name})")]

    def AjoutChamp(self, nomTable="", nomChamp="", typeChamp=""):
        self.cursor.execute(legacy_add_column_query(nomTable, nomChamp, typeChamp))
        self.connexion.commit()

    def ExecuterReq(self, req):
        self.cursor.execute(req)
        return 1

    def ResultatReq(self):
        return self.cursor.fetchall()

    def ReqInsert(self, table_name, data, commit=True):
        fields = ", ".join(name for name, _ in data)
        marks = ", ".join("?" for _ in data)
        self.cursor.execute(f"INSERT INTO {table_name} ({fields}) VALUES ({marks})",
                            tuple(value for _, value in data))
        if commit:
            self.connexion.commit()
        return int(self.cursor.lastrowid)

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


class _ClosableStub:
    def close(self):
        pass


def test_contract_write_port_adds_ccns_columns_on_legacy_base_then_creation_works():
    db = LegacySqliteDb()
    reader = CcnsDataReader(db_factory=lambda: db)
    adapter = TeamworksProductionReadAdapter(
        person_reader=_ClosableStub(), contract_reader=reader, activity_reader=_ClosableStub()
    )
    assert adapter.list_contracts(2) == ()  # met le schéma historique en cache

    port = adapter.build_contract_write_port()
    columns = {name for name, _ in db.GetListeChamps2("contrats")}
    assert {"convention_code", "ccns_group", "weekly_hours", "gross_monthly_salary"} <= columns

    contract_id = port.insert_contract(
        ContractCreateCommand(
            person_id=2, contract_type_code="CDI", start_date=date(2026, 11, 2),
            end_date=None, convention_code="CCNS", ccns_group="G4",
            cee_qualification=None, weekly_hours=Decimal("28"),
            gross_monthly_salary=Decimal("3000"), gross_annual_salary=None,
            trial_period_value=2, trial_period_unit="MONTH",
        )
    )
    port.commit()
    views = adapter.list_contracts(2)
    assert [view.id_historique for view in views] == [contract_id]
    assert views[0].classification == "Groupe 4"  # cache de colonnes invalidé
    assert views[0].duration == "28 h"

    adapter.build_contract_write_port()  # idempotent
    db.Close()


def test_contract_edit_dialog_shows_saved_money_with_two_decimals():
    assert _money_text(Decimal("3200.0")) == "3200,00"
    assert _money_text(3200.0) == "3200,00"
    assert _money_text(Decimal("1834.5")) == "1834,50"


class _OneShotPeopleWorker(QObject):
    loaded = Signal(object, object)
    failed = Signal(str)

    @Slot()
    def run(self):
        person = PersonView(
            id="—", id_historique=7, name="Aurore FLOCH", first_name="Aurore",
            last_name="FLOCH", birth_date="—", role="—", classification="—",
            contract="—", weekly_hours="—", status="—", site="—", medical="—", mutual="—",
        )
        self.loaded.emit((person,), {})


class _EmptyAdapter:
    def list_people(self):
        return ()

    def list_contracts(self, _person_id):
        return ()


def test_people_loader_updates_model_and_count_in_gui_thread():
    app = _app()
    window = PeopleContractsPilot(_EmptyAdapter())
    owned = []  # la fenêtre réelle conserve worker et thread
    window.attach_people_loader = lambda thread, worker: owned.append((thread, worker))
    window.is_closing_requested = lambda: False
    gui_thread = app.thread()
    seen = []
    original = window.people_model.replace

    def traced(people):
        seen.append(QThread.currentThread() == gui_thread)
        original(people)

    window.people_model.replace = traced
    thread = launcher.start_people_loader(window, _OneShotPeopleWorker, total_to_show_seconds=0.0)
    for _ in range(200):
        app.processEvents()
        if seen and thread.isFinished():
            break
        thread.wait(10)
    assert seen == [True]
    assert window.people_count.text() == "1 personne"
    thread.wait(2000)
    window.close()


def test_people_list_hides_empty_columns_and_keeps_name_readable():
    _app()

    class Adapter(_EmptyAdapter):
        def list_people(self):
            return tuple(
                PersonView(
                    id="—", id_historique=i, name=f"Personne {i}", first_name="P",
                    last_name=str(i), birth_date="—", role="—", classification="—",
                    contract="—", weekly_hours="—", status="—", site="—", medical="—", mutual="—",
                )
                for i in (1, 2)
            )

    window = PeopleContractsPilot(Adapter())
    try:
        table = window.people_table
        assert not table.isColumnHidden(1)
        assert all(table.isColumnHidden(c) for c in range(window.people_model.columnCount()) if c != 1)
    finally:
        window.close()


def test_launcher_installs_french_qt_standard_buttons():
    app = _app()
    assert launcher.install_french_qt_translation(app) is True
    box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
    labels = (
        box.button(QDialogButtonBox.StandardButton.Save).text().replace("&", ""),
        box.button(QDialogButtonBox.StandardButton.Cancel).text().replace("&", ""),
    )
    assert labels == ("Enregistrer", "Annuler")
