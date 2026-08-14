from pathlib import Path


SOURCE = Path("teamworks/Dlg/DLG_Saisie_cat_presences.py")


def test_importation_guards_missing_category():
    text = SOURCE.read_text(encoding="utf-8")
    assert "resultats = DB.ResultatReq()" in text
    assert "if not resultats:" in text
    assert "donnees = resultats[0]" in text
    assert "donnees = DB.ResultatReq()[0]" not in text


def test_sauvegarde_guards_empty_max_order_result():
    text = SOURCE.read_text(encoding="utf-8")
    assert "ordreMax = resultats[0][0] if resultats and resultats[0] else None" in text
    assert "ordreMax = DB.ResultatReq()[0][0]" not in text
