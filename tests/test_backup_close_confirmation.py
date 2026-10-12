"""Régressions sans affichage : vrai Start(), dialogues et stockage doublés."""
import ast
import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "teamworks/Utils/UTILS_Sauvegarde_auto.py"


def _start(namespace):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == "Sauvegarde_auto")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                  and node.name == "Start")
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["Start"]


@pytest.mark.parametrize("answer,expected_saves,expected_result", [
    (1, 1, True), (2, 0, True), (3, 0, 3),
])
@pytest.mark.parametrize("ask_option", [1, "1"])
def test_close_confirmation_keeps_yes_no_cancel_semantics(answer, expected_saves, expected_result, ask_option):
    events = []

    class Dialog:
        def __init__(self, parent, message, *, caption, style):
            assert parent == "parent"
            assert "quotidienne" in message
            assert caption == "Sauvegarde automatique"
            assert style == 8 | 16 | 32 | 64
            events.append("create")

        def SetYesNoCancelLabels(self, *labels):
            assert labels == ("Oui", "Non", "Annuler")
            return True

        def ShowModal(self):
            return answer

        def Destroy(self):
            events.append("destroy")

    wx = SimpleNamespace(MessageDialog=Dialog, YES_NO=8, CANCEL=16,
                         YES_DEFAULT=32, ICON_QUESTION=64, ID_YES=1, ID_NO=2, ID_CANCEL=3)
    db = SimpleNamespace(ReqMAJ=lambda *args: events.append("date"), Close=lambda: None)
    namespace = {"wx": wx, "_": lambda text: text, "datetime": datetime,
                 "GestionDB": SimpleNamespace(DB=lambda: db)}
    data = {"nom": "quotidienne", "sauvegarde_nom": "test", "option_demander": ask_option,
            "option_afficher_interface": 0, "option_confirmation": 0,
            "option_suppression": None, "IDsauvegarde": 7}
    instance = SimpleNamespace(parent="parent", listeSauvegardes=[data],
                               VerificationConditions=lambda data: True,
                               Sauvegarde=lambda data: events.append("save") or True)
    assert _start(namespace)(instance) == expected_result
    assert events.count("save") == expected_saves
    assert events.count("date") == expected_saves
    assert events[:2] == ["create", "destroy"]


def test_confirmation_is_destroyed_even_if_modal_fails():
    events = []

    class Dialog:
        def __init__(self, *args, **kwargs):
            pass

        def SetYesNoCancelLabels(self, *labels):
            return True

        def ShowModal(self):
            raise RuntimeError("modal failed")

        def Destroy(self):
            events.append("destroy")

    wx = SimpleNamespace(MessageDialog=Dialog, YES_NO=8, CANCEL=16,
                         YES_DEFAULT=32, ICON_QUESTION=64)
    namespace = {"wx": wx, "_": lambda text: text, "datetime": datetime}
    instance = SimpleNamespace(parent=None, listeSauvegardes=[{
        "sauvegarde_nom": "test", "nom": "test", "option_demander": 1,
    }], VerificationConditions=lambda data: True)
    with pytest.raises(RuntimeError, match="modal failed"):
        _start(namespace)(instance)
    assert events == ["destroy"]


def test_both_backup_prompts_use_native_dialogs():
    source = SOURCE.read_text(encoding="utf-8")
    assert "MultiMessageDialog" not in source
    assert "wx.lib.dialogs" not in source
    assert source.count("dlg.SetYesNoCancelLabels(") == 2
