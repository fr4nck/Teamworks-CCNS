from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QIcon, QStandardItem  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from data_adapter import PresenceCategoryView, PresenceView  # noqa: E402
from individual_pages import PresencesPage  # noqa: E402
from presence_editor import PresenceEditorDialog  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


class _NoopReader:
    def close(self) -> None:
        return None


class _DB:
    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.isNetwork = False
        self.echec = 0

    def Commit(self):
        self.connexion.commit()


class _ActivityReader(_NoopReader):
    def __init__(self):
        self.db = _DB()

    def lire_categories_presences(self):
        return (
            SimpleNamespace(
                IDcategorie=7,
                nom_categorie="Travail",
                couleur="#123456",
            ),
        )


def _adapter(activity_reader):
    return TeamworksProductionReadAdapter(
        person_reader=_NoopReader(),
        contract_reader=_NoopReader(),
        activity_reader=activity_reader,
    )


def test_production_adapter_expose_categories_et_port_ecriture_partage():
    activity = _ActivityReader()
    adapter = _adapter(activity)

    try:
        categories = adapter.list_presence_categories()
        port = adapter.build_presence_write_port()
    finally:
        adapter.close()

    assert categories == (
        PresenceCategoryView(
            category_id=7,
            name="Travail",
            color="#123456",
        ),
    )
    assert port.db is activity.db


def test_page_presence_active_le_crud_seulement_quand_autorise(app):
    page = PresencesPage(lambda _name: QIcon())

    assert page.actions.button("add").isEnabled() is False
    assert page.actions.button("edit").isEnabled() is False
    assert page.actions.button("delete").isEnabled() is False

    page.set_write_enabled(True)
    assert page.actions.button("add").isEnabled() is True
    assert page.actions.button("edit").isEnabled() is False
    assert page.actions.button("delete").isEnabled() is False

    view = PresenceView(
        key=501,
        category_id=7,
        category="Travail",
        category_color="#123456",
        date="Lundi 21 septembre 2026",
        vacation="",
        schedule="8h00-9h00",
        duration="1h00",
        label="Travail",
    )
    items = [QStandardItem(value) for value in (
        view.date,
        view.vacation,
        view.schedule,
        view.duration,
        view.label,
    )]
    for item in items:
        item.setData(view, Qt.ItemDataRole.UserRole)
    page.source_model.appendRow(items)
    page.table.selectRow(0)
    app.processEvents()

    assert page.selected_presence() is view
    assert page.actions.button("edit").isEnabled() is True
    assert page.actions.button("delete").isEnabled() is True

    emitted = []
    page.action_requested.connect(lambda action, payload: emitted.append((action, payload)))
    page.actions.button("edit").click()
    app.processEvents()

    assert emitted == [("edit", view)]

    page.set_write_enabled(False)
    assert page.actions.button("add").isEnabled() is False
    assert page.actions.button("edit").isEnabled() is False
    assert page.actions.button("delete").isEnabled() is False


def test_editeur_preserve_categorie_historique_absente(app):
    snapshot = SimpleNamespace(
        presence_date=__import__("datetime").date(2026, 9, 21),
        start_time="08:00",
        end_time="09:00",
        category_id=99,
        title="Ancienne catégorie",
    )

    dialog = PresenceEditorDialog(
        (),
        person_id=12,
        snapshot=snapshot,
    )

    assert dialog.category_combo.currentData() == 99
    assert "historique" in dialog.category_combo.currentText().lower()
    assert dialog.date_edit.isEnabled() is False


def test_launcher_et_pilote_transportent_la_factory_presence():
    launcher = (POC / "launcher.py").read_text(encoding="utf-8")
    pilot = (POC / "pilot_generalities.py").read_text(encoding="utf-8")

    assert "presence_write_port_factory = adapter.build_presence_write_port" in launcher
    assert "presence_write_port_factory=presence_write_port_factory" in launcher
    assert "PresenceCrudController" in pilot
    assert "refresh_callback=self._refresh_presences_after_write" in pilot
