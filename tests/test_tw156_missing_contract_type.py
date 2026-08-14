from pathlib import Path


def test_missing_contract_type_is_guarded():
    source = Path("teamworks/Dlg/DLG_Saisie_types_contrats.py").read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "donnees = DB.ResultatReq()[0]" not in source
