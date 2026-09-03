from pathlib import Path


ADAPTER = Path("teamworks/Ctrl/CTRL_Page_generalites_091e.py")


def test_adaptateur_generalites_est_valide_et_non_bloquant_a_letranger():
    source = ADAPTER.read_text(encoding="utf-8")
    compile(source, str(ADAPTER), "exec")
    assert "class Panel_general(LEGACY.Panel_general):" in source
    assert "def _naissance_en_france" in source
    assert "def Code_KillFocus1" in source
    assert "def Ville_KillFocus1" in source
    assert "def VilleText1" in source
    assert 'departement_nir_attendu(pays_naissance, dep_naiss)' in source
    assert 'texteSansEsp[5:7] != attendu' in source


def test_cp_naissance_devient_libre_hors_france_sans_couper_la_residence():
    source = ADAPTER.read_text(encoding="utf-8")
    assert 'SetCtrlParameters(mask="#####" if france else "")' in source
    assert "self.autoComplete = True" in source
    assert "seuls les\n        # gestionnaires du lieu de naissance" in source
