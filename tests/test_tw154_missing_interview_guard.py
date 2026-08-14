from pathlib import Path


def test_entretien_importation_guard_missing_row():
    source = Path("teamworks/Dlg/DLG_Saisie_entretien.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "donnees = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source
