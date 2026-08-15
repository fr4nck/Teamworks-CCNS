from pathlib import Path


def test_vacation_period_import_guards_empty_result():
    source = Path("teamworks/Dlg/DLG_Saisie_periode_vacances.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "donnees = DB.ResultatReq()[0]" not in source
