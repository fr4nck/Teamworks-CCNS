from pathlib import Path


def test_missing_holiday_is_guarded_before_first_result_access():
    source = Path("teamworks/Dlg/DLG_Saisie_jour_ferie.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "donnees = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source
