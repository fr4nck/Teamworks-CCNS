from pathlib import Path


def test_normalisation_cp_internationale_est_disponible_pour_l_import():
    source = Path("teamworks/Utils/UTILS_Generalites_international.py").read_text(encoding="utf-8")
    assert "def normalise_code_postal" in source
    assert "if not est_france(pays):" in source
    assert "return texte" in source
