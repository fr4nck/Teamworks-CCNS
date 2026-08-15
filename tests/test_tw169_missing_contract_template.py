from pathlib import Path


def test_contract_template_importation_handles_missing_row():
    source = Path("teamworks/Dlg/DLG_Creation_modele_contrat.py").read_text(encoding="utf-8")

    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert 'self.dictModeles["IDmodele"] = 0' in source
    assert "return False" in source
    assert "listeDonnees = resultats[0]" in source
    assert "return True" in source
    assert "DB.ResultatReq()[0]" not in source
