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
from data_adapter import ContractView  # noqa: E402
from pilot_view import PeopleContractsPilot  # noqa: E402


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


class _EmptyPilotAdapter:
    def list_people(self):
        return ()

    def list_contracts(self, _person_id):
        return ()


def _contract_view(kind: str) -> ContractView:
    return ContractView(
        kind=kind,
        start="01/09/2026",
        end="30/09/2026",
        classification="Groupe 6",
        duration="35 h",
        status="",
        id_historique=700,
    )


def test_advanced_contract_buttons_are_hidden_by_default():
    _app()
    window = PeopleContractsPilot(
        _EmptyPilotAdapter(),
        contract_write_port_factory=lambda: object(),
    )
    try:
        assert window._advanced_contracts_enabled is False
        assert window.contract_renew_button.isHidden() is True
        assert window.contract_to_cdi_button.isHidden() is True
        assert window.contract_legacy_classification_button.isHidden() is True
    finally:
        window.close()


def test_advanced_contract_buttons_are_visible_only_when_gate_is_enabled():
    _app()
    window = PeopleContractsPilot(
        _EmptyPilotAdapter(),
        contract_write_port_factory=lambda: object(),
        advanced_contracts_enabled=True,
    )
    try:
        assert window._advanced_contracts_enabled is True
        assert window.contract_renew_button.isHidden() is False
        assert window.contract_to_cdi_button.isHidden() is False
        assert window.contract_legacy_classification_button.isHidden() is False

        window.contracts_model.replace((_contract_view("CDD"),))
        window.contracts_stack.setCurrentIndex(1)
        window.contracts_table.selectRow(0)
        QApplication.processEvents()

        assert window.contract_renew_button.isEnabled() is True
        assert window.contract_to_cdi_button.isEnabled() is True
        assert window.contract_legacy_classification_button.isEnabled() is True

        window.contracts_model.replace((_contract_view("CDI"),))
        window.contracts_table.selectRow(0)
        QApplication.processEvents()
        window._on_contract_selection()

        assert window.contract_renew_button.isEnabled() is False
        assert window.contract_to_cdi_button.isEnabled() is False
        assert window.contract_legacy_classification_button.isEnabled() is True
    finally:
        window.close()


def test_feature_gate_defaults_to_false_in_public_constructor():
    source = (POC / "pilot_view.py").read_text(encoding="utf-8")

    assert "advanced_contracts_enabled: bool = False" in source
    assert "self._advanced_contracts_enabled = advanced_contracts_enabled is True" in source



def test_production_pilot_propagates_gate_but_launcher_does_not_enable_it():
    generalities_source = (POC / "pilot_generalities.py").read_text(encoding="utf-8")
    launcher_source = (POC / "launcher.py").read_text(encoding="utf-8")

    assert "advanced_contracts_enabled: bool = False" in generalities_source
    assert "advanced_contracts_enabled=advanced_contracts_enabled" in generalities_source
    assert "advanced_contracts_enabled=True" not in launcher_source
