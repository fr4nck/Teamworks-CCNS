import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_frais.py"


def _source():
    return PAGE.read_text(encoding="utf-8")


def test_expenses_page_is_valid_python():
    ast.parse(_source())


def test_expenses_page_uses_two_semantic_sections_and_labeled_actions():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "wx.BitmapButton" not in source
    assert source.count("CTRL_Section.Section(") == 2
    assert 'titre=_(u"Déplacements")' in source
    assert 'titre=_(u"Remboursements")' in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert "wx.WrapSizer" in source


def test_expenses_tables_use_available_width_and_semantic_surface():
    source = _source()
    assert "class _ListeFrais" in source
    assert source.count("def AjusterColonnes") >= 2
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Styles.GetIconSize("small")' in source
    assert 'attr1.SetBackgroundColour("#EEF4FB")' not in source
    assert "def OnGetItemAttr(self, item):\n        return None" in source


def test_expenses_page_keeps_business_actions_and_guards():
    source = _source()
    assert "DLG_Saisie_deplacement.SaisieDeplacement" in source
    assert "DLG_Saisie_remboursement.SaisieRemboursement" in source
    assert 'DB.ReqDEL("deplacements", "IDdeplacement", IDdeplacement)' in source
    assert 'DB.ReqDEL("remboursements", "IDremboursement", IDremboursement)' in source
    assert '[("IDremboursement", 0)]' in source
    assert "DLG_Impression_frais.Dialog" in source
    assert "MAJ_frm_gestion_frais" in source


def test_expenses_status_is_data_not_decorative_micro_icon():
    source = _source()
    assert 'u"N°%s" % IDremboursement' in source
    assert '"Ok.png"' not in source
    assert '"Interdit.png"' not in source
    assert "OnGetItemImage(self, item):\n        return -1" in source
