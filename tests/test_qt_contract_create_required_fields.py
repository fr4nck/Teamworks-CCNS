"""Création de contrat : aucune valeur métier présélectionnée ne peut être enregistrée par oubli."""
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

from PySide6.QtCore import QDate  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from contract_editor import UNSET_DATE, ContractCreateDialog  # noqa: E402


def _dialog():
    QApplication.instance() or QApplication([])
    return ContractCreateDialog(12, ("CDI", "CDD", "CEE"))


def test_no_business_value_is_preselected():
    dialog = _dialog()
    try:
        assert dialog.contract_type.currentData() is None
        assert dialog.start_date.date() == UNSET_DATE and not dialog.start_date.is_set()
        assert dialog.end_date.date() == UNSET_DATE
        assert dialog.group.currentData() is None
        assert dialog.weekly_hours.value() == 0
        assert dialog.weekly_hours.text() == "À saisir"
        assert "à saisir" in dialog.start_date.text()
    finally:
        dialog.close()


def test_save_without_choices_stays_open_and_lists_missing_fields_inline():
    dialog = _dialog()
    try:
        dialog._on_accept()
        assert dialog.result() == 0
        assert "type de contrat" in dialog.error_label.text()

        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CDI"))
        dialog._on_accept()
        text = dialog.error_label.text()
        for expected in ("date de début", "groupe CCNS", "durée hebdomadaire", "brut mensuel"):
            assert expected in text
        assert "date de fin" not in text  # CDI : pas de date de fin
        assert dialog.result() == 0
    finally:
        dialog.close()


def test_validation_message_disappears_as_soon_as_a_field_is_corrected():
    dialog = _dialog()
    try:
        dialog._on_accept()
        assert "type de contrat" in dialog.error_label.text()
        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CDI"))
        assert dialog.error_label.text() == ""
        dialog._on_accept()
        assert "brut mensuel" in dialog.error_label.text()
        dialog.weekly_hours.setValue(28.0)
        assert dialog.error_label.text() == ""
    finally:
        dialog.close()


def test_types_are_distinguished_by_labels_hints_and_required_fields():
    dialog = _dialog()
    try:
        labels = [dialog.contract_type.itemText(i) for i in range(dialog.contract_type.count())]
        assert any(label.startswith("CDI — ") for label in labels)
        assert any(label.startswith("CDD — ") for label in labels)
        assert any(label.startswith("CEE — ") for label in labels)

        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CDD"))
        assert dialog.end_date.isEnabled()
        assert "fin obligatoire" in dialog.type_hint.text()
        dialog._on_accept()
        assert "date de fin" in dialog.error_label.text()

        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CEE"))
        dialog._on_accept()
        text = dialog.error_label.text()
        assert "qualification CEE" in text and "groupe CCNS" not in text

        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CDI"))
        assert not dialog.end_date.isEnabled() and not dialog.end_date.is_set()
    finally:
        dialog.close()


def test_complete_cdi_is_accepted_with_exactly_the_entered_values():
    dialog = _dialog()
    try:
        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CDI"))
        dialog.start_date.setDate(QDate(2026, 11, 2))
        dialog.group.setCurrentIndex(dialog.group.findData("G4"))
        dialog.weekly_hours.setValue(28.0)
        dialog.monthly_salary.setText("3000,00")
        dialog._on_accept()
        assert dialog.result() == 1, dialog.error_label.text()
        command = dialog.command()
        assert command.contract_type_code == "CDI"
        assert command.start_date == date(2026, 11, 2)
        assert command.end_date is None
        assert command.ccns_group == "G4"
        assert command.weekly_hours == Decimal("28.00")
        assert command.gross_monthly_salary == Decimal("3000.00")
    finally:
        dialog.close()


def test_business_controls_still_apply_after_required_fields():
    dialog = _dialog()
    try:
        dialog.contract_type.setCurrentIndex(dialog.contract_type.findData("CDI"))
        dialog.start_date.setDate(QDate(2026, 11, 2))
        dialog.group.setCurrentIndex(dialog.group.findData("G4"))
        dialog.weekly_hours.setValue(28.0)
        dialog.monthly_salary.setText("1,00")
        dialog._on_accept()
        assert dialog.result() == 0
        assert "minimum CCNS/SMIC" in dialog.error_label.text()
    finally:
        dialog.close()
