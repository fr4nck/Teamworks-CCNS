"""Barres d'outils et clavier de la fenêtre Individus / Contrats (événements QTest réels)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
for path in (POC, ROOT / "teamworks", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from PySide6.QtCore import Qt, QTimer  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLabel, QMessageBox, QToolButton  # noqa: E402

from data_adapter import ContractView, PersonView  # noqa: E402
from person_editor import PersonDetailsEditDialog  # noqa: E402
from pilot_view import TOOL_BUTTON_SIZE, UNAVAILABLE_SUFFIX, PeopleContractsPilot  # noqa: E402


def _person(i, name):
    first, last = name.split(" ", 1)
    return PersonView(
        id="—", id_historique=i, name=name, first_name=first, last_name=last,
        birth_date="—", role="—", classification="—", contract="—", weekly_hours="—",
        status="—", site="—", medical="—", mutual="—",
    )


class _Adapter:
    def list_people(self):
        return (_person(1, "Paul AUTRET"), _person(2, "Aurélie GUEGUEN"))

    def list_contracts(self, person_id):
        return (ContractView(kind="CDI", start="01/09/2026", end="Indétermin.",
                             classification="Groupe 4", duration="28 h", status="—",
                             id_historique=40 + person_id),)


@pytest.fixture
def window():
    QApplication.instance() or QApplication([])
    w = PeopleContractsPilot(_Adapter(), contract_write_port_factory=lambda: None)
    w.show()
    QApplication.processEvents()
    yield w
    w.close()


def _select_first(window):
    window.people_table.selectRow(0)
    QApplication.processEvents()


def test_tool_buttons_share_consistent_sizing_and_accessible_names(window):
    icons = window.findChildren(QToolButton, "legacyToolButton")
    contracts = window.findChildren(QToolButton, "contractActionButton")
    assert len(icons) >= 7  # fonctions historiques désactivées, accessibles dans Autres
    assert len(contracts) == 9
    for button in icons:
        assert button.maximumSize().toTuple() == (TOOL_BUTTON_SIZE, TOOL_BUTTON_SIZE)
        assert button.iconSize().width() == 20
        assert button.accessibleName()
    for button in contracts:
        assert button.text()
        assert button.accessibleName()
        assert button.toolTip().startswith(button.accessibleName())
        assert button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        assert button.minimumHeight() >= 38


def test_unavailable_commands_are_disabled_and_say_so(window):
    unavailable = [b for b in window.findChildren(QToolButton, "legacyToolButton")
                   if b.property("unavailable")]
    names = {b.accessibleName() for b in unavailable}
    assert {"Supprimer la fiche sélectionnée", "Imprimer la liste", "Exporter la liste",
            "Aide", "Courrier ou publipostage"} <= names
    _select_first(window)
    for button in unavailable:
        assert not button.isEnabled()
        assert UNAVAILABLE_SUFFIX in button.toolTip()



def test_all_eight_sections_are_readable_and_switch_with_real_clicks(window):
    _select_first(window)
    assert window.tabs.count() == 8
    assert window.tabs.tabBar().isHidden()
    assert len(window.section_buttons) == 8
    assert [b.text() for b in window.section_buttons] == [
        "Généralités", "Questionnaire", "Qualifications", "Contrats",
        "Présences", "Scénarios", "Frais", "Recrutement",
    ]
    for size in ((900, 620), (1380, 860)):
        window.resize(*size)
        QApplication.processEvents()
        assert window.section_navigation.columns == (2 if size[0] == 900 else 4)
        for index, button in enumerate(window.section_buttons):
            assert button.isVisible()
            assert button.height() >= 40
            assert button.width() > button.fontMetrics().horizontalAdvance(button.text()) + 8
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            assert window.tabs.currentIndex() == index
            assert sum(b.isChecked() for b in window.section_buttons) == 1
            assert button.isChecked()
            # Recliquer sur la rubrique deja active ne doit jamais la decocher.
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            assert window.tabs.currentIndex() == index
            assert button.isChecked()
            assert sum(item.isChecked() for item in window.section_buttons) == 1

    # Le code historique peut toujours selectionner une page directement.
    window.tabs.setCurrentIndex(3)
    assert window.section_buttons[3].isChecked()


def test_person_summary_is_compact_and_has_no_prototype_heading(window):
    _select_first(window)
    assert window.person_avatar.width() <= 64
    assert window.person_avatar.height() <= 64
    assert window.detail_title.text() == "Paul AUTRET"
    assert window.findChildren(QLabel, "personSummaryName")
    assert not any(
        isinstance(label, QLabel) and "Transposition Qt" in label.text()
        for label in window.findChildren(QLabel)
    )



def test_individual_actions_show_labels_and_keep_inactive_commands_explicit(window):
    _select_first(window)
    for button, label in (
        (window.person_create_button, "Ajouter"),
        (window.person_edit_button, "Modifier"),
    ):
        assert button.isVisible()
        assert button.text() == label
        assert button.accessibleName() and button.toolTip()
        assert button.minimumSize().width() >= 99
        assert button.iconSize().width() == 18

    other_actions = window.people_more_actions
    assert other_actions.isVisible()
    assert other_actions.text() == "Autres"
    menu = other_actions.menu()
    assert menu is not None
    assert len(menu.actions()) >= 7
    assert all(not action.isEnabled() for action in menu.actions())
    assert all("indisponible" in action.text() for action in menu.actions())

    # La colonne d'outils a disparu : le tableau dispose de la largeur du panneau.
    window.resize(1380, 860)
    QApplication.processEvents()
    assert window.people_table.width() >= 300

def test_contract_actions_are_labeled_and_table_uses_full_width(window):
    _select_first(window)
    window.tabs.setCurrentIndex(3)
    window.resize(900, 620)
    QApplication.processEvents()
    expected = (
        (window.contract_create_button, "Ajouter"),
        (window.contract_edit_button, "Modifier"),
        (window.contract_delete_button, "Supprimer"),
        (window.contract_signature_button, "Signature"),
        (window.contract_due_button, "DUE"),
        (window.contract_document_button, "Documents"),
    )
    for button, label in expected:
        assert button.text() == label
        assert button.width() >= 86
        assert button.isVisible()
    assert window.contracts_table.isVisible()
    assert window.contracts_table.width() >= 300


def test_enter_on_contract_row_opens_edit_and_delete_key_asks_confirmation(window):
    _select_first(window)
    window.tabs.setCurrentIndex(3)  # Contrats
    window.contracts_table.selectRow(0)
    QApplication.processEvents()
    edits, deletes = [], []
    window._edit_selected_contract = lambda: edits.append(1)
    window.contract_edit_button.clicked.disconnect()
    window.contract_edit_button.clicked.connect(window._edit_selected_contract)
    window.contracts_table.setFocus()
    QTest.keyClick(window.contracts_table, Qt.Key.Key_Return)
    assert edits == [1]

    def answer_no():
        box = QApplication.activeModalWidget()
        if isinstance(box, QMessageBox):
            deletes.append(box.text())
            box.button(QMessageBox.StandardButton.No).click()
    QTimer.singleShot(0, answer_no)
    QTest.keyClick(window.contracts_table, Qt.Key.Key_Delete)
    QApplication.processEvents()
    assert deletes and "supprimer ce contrat" in deletes[0]
    assert window.statusBar().currentMessage() == "Suppression annulée · aucune écriture"


def test_escape_in_search_restores_full_list(window):
    window.search.setFocus()
    QTest.keyClicks(window.search, "GUEG")
    assert window.people_proxy.rowCount() == 1
    QTest.keyClick(window.search, Qt.Key.Key_Escape)
    assert window.search.text() == ""
    assert window.people_proxy.rowCount() == 2


def test_tab_order_walks_list_then_tools(window):
    window.people_table.setFocus()
    seen = []
    for _ in range(4):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        seen.append(QApplication.focusWidget())
    assert window.search in seen
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Backtab)
    assert QApplication.focusWidget() is seen[-2]


def test_person_dialog_enter_validates_and_escape_cancels():
    QApplication.instance() or QApplication([])
    dialog = PersonDetailsEditDialog(None)
    dialog.show()
    QApplication.processEvents()
    try:
        save = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save)
        assert save.text().replace("&", "") in ("Save", "Enregistrer")

        def close_warning():
            box = QApplication.activeModalWidget()
            if isinstance(box, QMessageBox):
                box.button(QMessageBox.StandardButton.Ok).click()
        QTimer.singleShot(0, close_warning)
        dialog.last_name.setFocus()
        QTest.keyClick(dialog.last_name, Qt.Key.Key_Return)  # champs vides : refus
        QApplication.processEvents()
        assert dialog.isVisible() and dialog.result() == 0

        QTest.keyClick(dialog.last_name, Qt.Key.Key_Escape)
        QApplication.processEvents()
        assert not dialog.isVisible() and dialog.result() == 0
    finally:
        dialog.close()


class _FailingSecondAdapter(_Adapter):
    def list_contracts(self, person_id):
        if person_id == 2:
            raise RuntimeError("Lecture impossible (contrats) : base indisponible ou requête refusée.")
        return super().list_contracts(person_id)


def test_failed_contract_read_never_shows_the_previous_person_contracts():
    QApplication.instance() or QApplication([])
    w = PeopleContractsPilot(_FailingSecondAdapter(), contract_write_port_factory=lambda: None)
    w.show()
    try:
        w.people_table.selectRow(0)
        QApplication.processEvents()
        assert w.contracts_model.rowCount() == 1
        w.people_table.selectRow(1)
        QApplication.processEvents()
        assert w.contracts_model.rowCount() == 0
        assert not w.contract_create_button.isEnabled()
        assert "Lecture des contrats impossible" in w.statusBar().currentMessage()
        assert w.detail_contracts.text() == "Contrats non lus"
    finally:
        w.close()
