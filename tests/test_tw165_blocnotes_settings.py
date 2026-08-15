from pathlib import Path


def test_blocnotes_settings_guard_empty_query_results():
    source = Path("teamworks/Dlg/DLG_Parametres_blocnotes.py").read_text(encoding="utf-8")

    assert source.count("resultats = DB.ResultatReq()") >= 2
    assert "if not resultats:" in source
    assert "self.InitValeurs(resultats[0])" in source
    assert "DB.ResultatReq()[0]" not in source
    assert "self.val_largeur = 300" in source
    assert "self.val_hauteur = 300" in source
    assert "return False" in source
    assert "return True" in source
