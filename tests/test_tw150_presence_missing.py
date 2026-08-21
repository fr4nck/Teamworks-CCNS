from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "teamworks/Dlg/DLG_Saisie_presence.py").read_text(encoding="utf-8")


def test_missing_presence_is_guarded_before_indexing():
    assert "resultats = DB.ResultatReq()" in SOURCE
    assert "if not resultats:" in SOURCE
    assert "Cette présence n'existe plus dans la base de données." in SOURCE
    assert "return None" in SOURCE
    assert "donnees = DB.ResultatReq()[0]" not in SOURCE


def test_dialog_closes_when_presence_disappeared():
    assert "if donnees_modif is None:" in SOURCE
    assert "dialog = _dialog_ancestor(self)" in SOURCE
    assert "wx.CallAfter(dialog.EndModal, wx.ID_CANCEL)" in SOURCE
