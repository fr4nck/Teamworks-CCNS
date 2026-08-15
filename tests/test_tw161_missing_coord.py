from pathlib import Path


def test_missing_coord_is_guarded_before_first_row_access():
    source = Path("teamworks/Dlg/DLG_Saisie_coords.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "Coordonnée introuvable" in source
    assert "wx.CallAfter(self.EndModal, wx.ID_CANCEL)" in source
    assert "donnees = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source
