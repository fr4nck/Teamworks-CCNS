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
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtWidgets import QApplication  # noqa: E402

from application.services.contract_write import (  # noqa: E402
    ContractEditSnapshot,
    LegacyClassificationChoice,
    LegacyContractOptions,
    LegacyPointChoice,
)
from contract_editor import (  # noqa: E402
    ContractOperationDialog,
    LegacyClassificationDialog,
)
from domain.contracts.contract_operation import ContractOperation  # noqa: E402


def _app():
    return QApplication.instance() or QApplication([])


def _previous_cdd(**changes):
    values = dict(
        contract_id=700,
        person_id=12,
        contract_type_code="CDD",
        contract_type_label="CDD",
        convention_code="CCNS",
        ccns_group="G6",
        cee_qualification=None,
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=Decimal("9999.00"),
        gross_annual_salary=None,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        break_date=None,
        modern_fields_supported=True,
        operation_type="NEW",
        previous_contract_id=None,
        legacy_classification_id=None,
        legacy_point_id=None,
        legacy_trial_days=14,
        trial_period_value=14,
        trial_period_unit="DAY",
    )
    values.update(changes)
    return ContractEditSnapshot(**values)


def test_renewal_dialog_builds_operation_command_without_exposing_new_contract_type():
    _app()
    dialog = ContractOperationDialog(
        12,
        _previous_cdd(),
        ContractOperation.CDD_RENEWAL,
    )
    try:
        dialog.monthly_salary.setText("9999")
        command = dialog.command()

        assert command.contract_type_code == "CDD"
        assert command.operation_type == "CDD_RENEWAL"
        assert command.previous_contract_id == 700
        assert command.start_date == date(2026, 10, 1)
        assert command.trial_period_value == 0
        assert command.trial_period_unit == "DAY"
        assert dialog.contract_type.isEnabled() is False
        assert dialog.start_date.isEnabled() is False
    finally:
        dialog.close()


def test_cdd_to_cdi_dialog_preloads_remaining_probation_from_previous_cdd():
    _app()
    dialog = ContractOperationDialog(
        12,
        _previous_cdd(),
        ContractOperation.CDD_TO_CDI,
    )
    try:
        dialog.monthly_salary.setText("9999")
        command = dialog.command()

        assert command.contract_type_code == "CDI"
        assert command.operation_type == "CDD_TO_CDI"
        assert command.previous_contract_id == 700
        assert command.start_date == date(2026, 10, 1)
        assert command.end_date is None
        assert command.trial_period_value == 62
        assert command.trial_period_unit == "DAY"
    finally:
        dialog.close()


def test_legacy_classification_dialog_uses_applicable_point_identity_not_amount():
    _app()
    options = LegacyContractOptions(
        classifications=(
            LegacyClassificationChoice(2, "Animateur BAFA"),
            LegacyClassificationChoice(3, "Direction"),
        ),
        point_values=(
            LegacyPointChoice(9, Decimal("6.10"), date(2026, 1, 1)),
            LegacyPointChoice(10, Decimal("6.20"), date(2026, 9, 1)),
        ),
        applicable_point_id=10,
    )
    snapshot = _previous_cdd(
        convention_code=None,
        legacy_classification_id=2,
        legacy_point_id=9,
    )
    dialog = LegacyClassificationDialog(options, snapshot)
    try:
        target = dialog.classification.findData(3)
        assert target >= 0
        dialog.classification.setCurrentIndex(target)
        command = dialog.command()

        assert command.contract_id == 700
        assert command.classification_id == 3
        assert command.point_id == 10
        assert dialog.point.currentData() == 10
        assert dialog.point.isEnabled() is False
    finally:
        dialog.close()


def test_advanced_contract_ui_is_prepared_but_not_exposed_in_toolbar():
    source = (POC / "pilot_view.py").read_text(encoding="utf-8")

    assert "def _run_advanced_contract_operation" in source
    assert "def _run_legacy_classification" in source
    assert "contract_renew_button" not in source
    assert "contract_to_cdi_button" not in source
    assert "contract_legacy_classification_button" not in source
    assert ".clicked.connect(self._run_advanced_contract_operation" not in source
    assert ".clicked.connect(self._run_legacy_classification" not in source
