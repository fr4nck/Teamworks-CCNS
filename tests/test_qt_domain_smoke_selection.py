"""Reponse complete du faux adaptateur de recette lors de la selection d'une personne.

La recette ne doit jamais ouvrir une base SQL ni inventer des presences.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
for source in (POC, ROOT / "teamworks", ROOT):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from PySide6.QtWidgets import QApplication  # noqa: E402
from domain_read_adapter import build_domain_smoke_adapter  # noqa: E402
from pilot_generalities import PeopleContractsGeneralitiesPilot  # noqa: E402


def test_domain_smoke_adapter_implements_empty_presence_contract() -> None:
    adapter = build_domain_smoke_adapter()
    people = adapter.list_people()
    assert len(people) == 2
    assert adapter.list_presence_categories() == ()
    for person in people:
        assert adapter.list_presences(person.id) == ()
        assert len(adapter.list_contracts(person.id)) == 1


def test_real_qt_pilot_can_select_a_smoke_person() -> None:
    app = QApplication.instance() or QApplication([])
    window = PeopleContractsGeneralitiesPilot(build_domain_smoke_adapter())
    try:
        window.show()
        app.processEvents()
        window.people_table.selectRow(0)
        app.processEvents()
        assert window.detail_stack.currentIndex() == 1
        assert window.contracts_model.rowCount() == 1
        assert "dossier affiché" in window.statusBar().currentMessage()
        assert window.people_table.horizontalHeader().sectionSize(0) >= 108
        assert window.legacy_tabs.presences_page.source_model.rowCount() == 0
        window.tabs.setCurrentIndex(3)
        app.processEvents()
        assert window.section_buttons[3].isChecked()
        assert window.contracts_table.isVisible()
    finally:
        window.close()
        app.processEvents()
