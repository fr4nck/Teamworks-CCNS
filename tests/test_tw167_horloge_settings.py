from pathlib import Path


def test_horloge_settings_guard_empty_results_and_use_fallbacks():
    source = Path("teamworks/Dlg/DLG_Parametres_horloge.py").read_text(encoding="utf-8")

    assert "donnees = DB.ResultatReq()[0]" not in source
    assert source.count("resultats = DB.ResultatReq()") >= 2
    assert "if not resultats:" in source
    assert "Les paramètres par défaut du gadget Horloge sont introuvables." in source
    assert "self.InitValeurs((" in source
    assert '"(300, 300)"' in source
    assert "'couleur_face': (255, 255, 255)" in source
    assert "return False" in source
    assert "return True" in source
