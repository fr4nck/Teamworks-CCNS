# -*- coding: utf-8 -*-
"""Contrats de stabilisation runtime Windows wxPython 4.3."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_preferences_buttons_use_panel_parent():
    source = _source("teamworks/Dlg/DLG_Preferences.py")
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "Button"
        and call.args
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id == "panel"
        for call in calls
    )
    assert not any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "CreateStdDialogButtonSizer"
        for call in calls
    )


def test_object_listview_widths_are_coerced_to_int():
    source = _source("teamworks/ObjectListView/__init__.py")
    assert "bounded_width = int(round(" in source
    assert "_ResizeSpaceFillingColumns = _resize_space_filling_columns_int" in source
    assert source.index("time.clock = time.monotonic") < source.index("from . ObjectListView import")


def test_dynamic_person_import_applies_safe_age_guard():
    source = _source("teamworks/Utils/UTILS_Adaptations.py")
    assert 'nom_module.endswith("OL_personnes")' in source
    assert "module.Track.RetourneAge = _safe_person_age" in source
    assert "datetime.date.fromisoformat" in source
    assert "except (TypeError, ValueError, OverflowError)" in source
