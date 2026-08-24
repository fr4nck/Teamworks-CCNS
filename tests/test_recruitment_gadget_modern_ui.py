import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Ctrl" / "CTRL_Gadget_candidatures.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_recruitment_gadget_is_valid_python():
    ast.parse(_source())


def test_recruitment_gadget_uses_semantic_typography_and_surfaces():
    source = _source()
    assert "Tekton" not in source
    assert "SetPointSize" not in source
    assert "wx.FFont" not in source
    assert "(122, 161, 230)" not in source
    assert "wx.FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert 'UTILS_Styles.GetFont("body-small")' in source
    assert 'UTILS_Styles.GetFont("h6")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Interface.GetToken("primary_container")' in source


def test_recruitment_gadget_empty_state_is_responsive():
    source = _source()
    assert '_(u"Aucune information")' in source
    assert "GetBestSize()" in source
    assert "GetClientSize()" in source
    assert "size=(200, 30)" not in source
    assert "-60" not in source


def test_recruitment_gadget_keeps_business_queries():
    source = _source()
    assert "FROM entretiens WHERE (date <= '%s' AND avis=0)" in source
    assert "FROM candidatures WHERE (reponse_obligatoire=1 AND reponse=0)" in source
    assert "def GetNom" in source
    assert "def GetListeDonnees" in source
