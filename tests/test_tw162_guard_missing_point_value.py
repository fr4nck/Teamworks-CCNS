from pathlib import Path


def test_point_value_import_guards_empty_result():
    source = Path("teamworks/Dlg/DLG_Saisie_val_point.py").read_text(encoding="utf-8")

    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "donnees = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source
