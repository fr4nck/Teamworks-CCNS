from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

POC_DIR = Path(__file__).resolve().parents[1] / "poc" / "qt-theme"
if str(POC_DIR) not in sys.path:
    sys.path.insert(0, str(POC_DIR))

from PySide6.QtWidgets import QApplication, QDoubleSpinBox

from contract_editor import decimal_from_qt_number, parse_decimal_text


def test_qdouble_spinbox_quarter_hour_reaches_application_as_decimal() -> None:
    app = QApplication.instance() or QApplication([])
    widget = QDoubleSpinBox()
    widget.setDecimals(2)
    widget.setSingleStep(0.25)
    widget.setValue(21.25)

    assert decimal_from_qt_number(widget.value()) == Decimal("21.25")
    assert app is not None


@pytest.mark.parametrize("text", ("", " ", "-", ","))
def test_incomplete_salary_input_stays_pending(text: str) -> None:
    assert parse_decimal_text(text) is None


def test_french_salary_input_is_normalized_without_float() -> None:
    assert parse_decimal_text("1 850,25") == Decimal("1850.25")
