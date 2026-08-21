from pathlib import Path


def test_saisie_candidat_handles_missing_row():
    source = Path("teamworks/Dlg/DLG_Saisie_candidat_core.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "Ce candidat n'existe plus dans la base de données." in source
    assert "DB.ResultatReq()[0]" not in source
