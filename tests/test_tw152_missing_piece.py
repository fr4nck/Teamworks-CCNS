from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_missing_piece_is_guarded():
    source = (ROOT / "teamworks/Dlg/DLG_Saisie_piece.py").read_text(encoding="utf-8")

    assert "donnees = DB.ResultatReq()[0]" not in source
    assert "if not resultats:" in source
    assert "Cette pièce n'existe plus dans la base de données." in source
    assert "wx.CallAfter(self.EndModal, wx.ID_CANCEL)" in source
