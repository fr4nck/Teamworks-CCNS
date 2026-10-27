"""Regression: Enter validates the protected-file password without bypassing authentication."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks/Teamworks_core.py"


def _class_method(cls_name, fn_name):
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls_name)
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    return ast.get_source_segment(source, fn)


def test_password_entry_routes_enter_to_the_existing_ok_result():
    init = _class_method("SaisiePassword", "__init__")
    handler = _class_method("SaisiePassword", "OnPasswordEnter")
    assert "wx.TE_PASSWORD | wx.TE_PROCESS_ENTER" in init
    assert "self.bouton_ok.SetDefault()" in init
    assert "self.text_password.Bind(wx.EVT_TEXT_ENTER, self.OnPasswordEnter)" in init
    assert "self.text_password.SetFocus()" in init
    assert "self.EndModal(wx.ID_OK)" in handler


def test_enter_does_not_skip_password_validation_or_cancel_logic():
    source = _class_method("SaisiePassword", "__init__")
    auth = _class_method("MainFrame", "Verif_Password") if "class MainFrame(" in SOURCE.read_text(encoding="utf-8") else SOURCE.read_text(encoding="utf-8")
    assert "id=wx.ID_CANCEL" in source
    assert "if pwd == password" in auth
    assert "dlg.ShowModal() == wx.ID_OK" in auth
    assert "Votre mot de passe est erroné." in auth
