"""Non-régressions des défauts reproduits lors de la recette Windows réelle Qt.

Recette : vrai launcher, adaptateurs production, GestionDB sur une copie
fictive de Static/Exemples/Exemple_TDATA.dat, événements QTest.
"""
from __future__ import annotations

import os
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
import launcher  # noqa: E402
from pilot_view import PeopleContractsPilot  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


def _app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def GestionDB(monkeypatch):
    """Vrai GestionDB et ses dépendances, même si d'autres tests ont laissé des faux.

    Certains tests installent des ``SimpleNamespace`` dans ``sys.modules`` ou sur
    les paquets ``Utils``/``Data`` ; ils sont retirés le temps du test puis restaurés.
    """
    import importlib
    import types

    for name, module in list(sys.modules.items()):
        if module is not None and not isinstance(module, types.ModuleType):
            monkeypatch.delitem(sys.modules, name)
    for package_name in ("Utils", "Data", "infrastructure.persistence"):
        package = sys.modules.get(package_name)
        if isinstance(package, types.ModuleType):
            for attr, value in list(vars(package).items()):
                if isinstance(value, types.SimpleNamespace):
                    monkeypatch.delattr(package, attr)
    current = sys.modules.get("GestionDB")
    if current is not None and not getattr(current, "__file__", None):
        monkeypatch.delitem(sys.modules, "GestionDB")
    try:
        import appdirs  # noqa: F401  (dépendance de GestionDB/UTILS_Fichiers)
        legacy_runtime = True
    except ImportError:
        legacy_runtime = False
    if not legacy_runtime:
        # CI Linux minimale : GestionDB réel inimportable ; le job Windows natif
        # exécute ces mêmes tests sur le vrai module.
        module = types.SimpleNamespace(DB=_SqliteGestionDbShim)
    else:
        module = importlib.import_module("GestionDB")
    monkeypatch.setitem(sys.modules, "GestionDB", module)
    return module

class _SqliteGestionDbShim:
    """Sous-ensemble fidèle de GestionDB.DB (SQLite local) pour les CI sans appdirs."""

    def __init__(self, nomFichier="", suffixe=None, modeCreation=False):
        import sqlite3

        self.nomFichier = nomFichier
        self.isNetwork = False
        self.connexion = sqlite3.connect(nomFichier)
        self.cursor = self.connexion.cursor()
        self.echec = 0

    def ExecuterReq(self, req):
        self.cursor.execute(req)
        return 1

    def ResultatReq(self):
        return self.cursor.fetchall()

    def GetListeTables(self):
        self.ExecuterReq("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return self.ResultatReq()

    def GetListeChamps2(self, nomTable=""):
        self.ExecuterReq("PRAGMA table_info('%s');" % nomTable)
        return [(row[1], row[2]) for row in self.ResultatReq()]

    def AjoutChamp(self, nomTable="", nomChamp="", typeChamp=""):
        from infrastructure.persistence.legacy_table_ddl import legacy_add_column_query

        self.ExecuterReq(legacy_add_column_query(nomTable, nomChamp, typeChamp))
        self.connexion.commit()

    def ReqInsert(self, nomTable, listeDonnees, commit=True):
        fields = ", ".join(name for name, _ in listeDonnees)
        marks = ", ".join("?" for _ in listeDonnees)
        self.cursor.execute("INSERT INTO %s (%s) VALUES (%s)" % (nomTable, fields, marks),
                            tuple(value for _, value in listeDonnees))
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


def _legacy_adapter(tmp_path, GestionDB):
    import shutil

    path = tmp_path / "Recette_TDATA.dat"
    shutil.copyfile(ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat", path)
    db = GestionDB.DB(nomFichier=str(path), suffixe=None)
    reader = CcnsDataReader(db_factory=lambda: db)
    adapter = TeamworksProductionReadAdapter(
        person_reader=_ClosableStub(), contract_reader=reader, activity_reader=_ClosableStub()
    )
    return adapter, db


def _contract_columns(db):
    return {name for name, _ in db.GetListeChamps2("contrats")}


def test_contract_write_port_never_alters_schema_implicitly(tmp_path, GestionDB):
    adapter, db = _legacy_adapter(tmp_path, GestionDB)
    try:
        adapter.build_contract_write_port()
        assert "ccns_group" not in _contract_columns(db)
        assert len(adapter.contract_schema_report().missing_contract_columns) == 10
    finally:
        db.Close()


def test_authorised_evolution_then_contract_creation_and_readback(tmp_path, GestionDB):
    adapter, db = _legacy_adapter(tmp_path, GestionDB)
    try:
        assert adapter.list_contracts(2) == ()  # met le schéma historique en cache
        result = adapter.evolve_contract_schema()
        assert result.ok, result.message
        assert Path(result.backup_path).is_file()
        assert adapter.contract_schema_report().contract_writes_ready

        port = adapter.build_contract_write_port()
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
    finally:
        db.Close()


class _SchemaPort:
    def __init__(self, missing):
        self.missing = missing
        self.evolved = 0

    def contract_schema_report(self):
        from types import SimpleNamespace
        return SimpleNamespace(missing_contract_columns=self.missing)

    def evolve_contract_schema(self):
        from types import SimpleNamespace
        self.evolved += 1
        self.missing = ()
        return SimpleNamespace(ok=True, message="10 colonne(s) CCNS ajoutée(s) · sauvegarde : x.bak")


def _answer_message_box(button):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QMessageBox

    seen = {}

    def answer():
        box = QApplication.activeModalWidget()
        if isinstance(box, QMessageBox):
            seen["text"] = box.text()
            box.button(button).click()
    QTimer.singleShot(0, answer)
    return seen


@pytest.mark.parametrize("accept", [False, True])
def test_contract_creation_asks_before_any_schema_evolution(accept):
    from PySide6.QtWidgets import QMessageBox

    _app()
    port = _SchemaPort(("ccns_group", "weekly_hours"))
    opened = []
    window = PeopleContractsPilot(
        _EmptyAdapter(),
        contract_write_port_factory=lambda: opened.append("port") or None,
        contract_schema_port=port,
    )
    try:
        window._current_contract_person_key = 2
        seen = _answer_message_box(
            QMessageBox.StandardButton.Yes if accept else QMessageBox.StandardButton.No
        )
        assert window._contract_schema_ready() is accept
        assert "sauvegarde" in seen["text"] and "Aucune donnée existante" in seen["text"]
        assert port.evolved == (1 if accept else 0)
        if not accept:
            assert "aucune écriture" in window.statusBar().currentMessage()
        assert opened == []
    finally:
        window.close()


def test_schema_ready_without_question_when_columns_present():
    _app()
    port = _SchemaPort(())
    window = PeopleContractsPilot(_EmptyAdapter(), contract_schema_port=port)
    try:
        assert window._contract_schema_ready() is True
        assert QApplication.activeModalWidget() is None
    finally:
        window.close()


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


def test_icon_tool_buttons_have_accessible_names():
    _app()
    window = PeopleContractsPilot(_EmptyAdapter())
    try:
        for button in (window.person_create_button, window.person_edit_button,
                       window.contract_create_button, window.contract_edit_button,
                       window.contract_delete_button):
            assert button.accessibleName() and button.toolTip().startswith(button.accessibleName())
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
