from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_qualifications.py"


def _source():
    return PAGE.read_text(encoding="utf-8")


def test_qualifications_page_has_no_legacy_chrome():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert "wx.StaticBoxSizer" not in source
    assert "wx.BitmapButton" not in source
    assert "wx.SUNKEN_BORDER" not in source
    assert ".Fit(self)" not in source
    assert "Images/16x16/" not in source


def test_qualifications_page_uses_flexible_semantic_layout():
    source = _source()
    assert "wx.BoxSizer" in source
    assert "wx.WrapSizer" in source
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Interface.GetToken("success")' in source
    assert 'UTILS_Interface.GetToken("warning")' in source
    assert 'UTILS_Interface.GetToken("danger")' in source
    assert "proportions = (0.40, 0.14, 0.14, 0.32)" in source


def test_qualifications_page_keeps_document_business_operations():
    source = _source()
    assert 'DB.ReqDEL("pieces", "IDpiece", varIDpiece)' in source
    assert 'INSERT INTO diplomes (IDpersonne, IDtype_diplome)' in source
    assert 'DELETE FROM diplomes WHERE IDpersonne=%d AND IDtype_diplome=%d' in source
    assert 'GestionDB.DB(suffixe="DOCUMENTS")' in source
    assert "AjouterPiece(IDtypePiece=IDtypePiece)" in source
