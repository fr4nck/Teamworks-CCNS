from pathlib import Path


def test_contract_fields_dialog_handles_missing_and_nullable_values():
    source = Path("teamworks/Dlg/DLG_Saisie_champs_contrats.py").read_text(encoding="utf-8")

    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "donnees = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source

    for index in (1, 2, 3, 4, 5):
        assert f"donnees[{index}] or \"\"" in source

    assert "self.text_exemple.SetFocus()" in source
