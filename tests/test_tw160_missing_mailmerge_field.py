from pathlib import Path


def test_mailmerge_field_import_guards_empty_result():
    source = Path("teamworks/Dlg/DLG_Saisie_champs_publipostage.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "IDchamp, categorie, nom, mot_cle, defaut = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source
