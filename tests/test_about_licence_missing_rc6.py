# -*- coding: utf-8 -*-
"""Régression du crash RC6 : menu À propos > Licence (FileNotFoundError)."""
import ast
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import mock
import sys


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def _handler(path, wx):
    source = CORE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "On_propos_licence"
    )
    ns = {
        "Chemins": SimpleNamespace(GetMainPath=lambda name: str(path)),
        "_": lambda text: text,
        "wx": wx,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[fn], type_ignores=[],
    )), str(CORE), "exec"), ns)
    return ns["On_propos_licence"]


class Modal:
    def __init__(self):
        self.show_count = 0
        self.destroy_count = 0

    def ShowModal(self):
        self.show_count += 1

    def Destroy(self):
        self.destroy_count += 1


def test_missing_licence_does_not_crash_and_reports_problem(tmp_path):
    modal = Modal()
    captured = []
    wx = SimpleNamespace(
        OK=1, ICON_ERROR=2,
        MessageDialog=lambda *args: (captured.append(args) or modal),
    )
    _handler(tmp_path / "Licence.txt", wx)(object(), None)
    assert len(captured) == 1
    assert "Licence.txt" in captured[0][1]
    assert modal.show_count == 1
    assert modal.destroy_count == 1


def test_present_licence_is_read_in_utf8_and_modal_destroyed(tmp_path):
    content = "Licence GPL — © 2008–2020\n"
    path = tmp_path / "Licence.txt"
    path.write_text(content, encoding="utf-8")

    lib = ModuleType("wx.lib")
    lib.__path__ = []
    dialogs = ModuleType("wx.lib.dialogs")
    lib.dialogs = dialogs
    wx = ModuleType("wx")
    wx.__path__ = []
    wx.lib = lib
    captured = []
    modal = Modal()
    dialogs.ScrolledMessageDialog = lambda *args, **kw: (
        captured.append((args, kw)) or modal
    )
    with mock.patch.dict(sys.modules, {
        "wx": wx, "wx.lib": lib, "wx.lib.dialogs": dialogs,
    }):
        _handler(path, wx)(object(), None)
    assert captured[0][0][1] == content
    assert modal.show_count == 1
    assert modal.destroy_count == 1


def test_source_licence_exists_and_has_expected_gpl_text():
    content = (ROOT / "teamworks" / "Licence.txt").read_text(encoding="utf-8")
    assert "LICENCE ET CONDITIONS D'UTILISATION" in content
    assert "Licence Publique" in content
    assert len(content) > 1000
