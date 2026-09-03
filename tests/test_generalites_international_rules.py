from teamworks.Utils import UTILS_Generalites_international as rules


def test_code_postal_francais_reste_normalise_sur_cinq_chiffres():
    assert rules.normalise_code_postal("3500", "France") == "03500"
    assert rules.normalise_code_postal(35650, "France") == "35650"


def test_code_postal_etranger_reste_libre():
    assert rules.normalise_code_postal("L-1234", "Luxembourg") == "L-1234"
    assert rules.normalise_code_postal("SW1A 1AA", "Royaume-Uni") == "SW1A 1AA"


def test_base_locale_des_villes_ne_bloque_que_la_france():
    assert rules.ville_locale_obligatoire("France") is True
    assert rules.ville_locale_obligatoire("Luxembourg") is False


def test_nir_etranger_attend_le_departement_99():
    assert rules.departement_nir_attendu("Luxembourg", "L-1234") == "99"
    assert rules.nir_lieu_compatible("99", "Luxembourg", "") is True
    assert rules.nir_lieu_compatible("35", "Luxembourg", "") is False


def test_nir_france_conserve_le_departement_du_cp():
    assert rules.departement_nir_attendu("France", "35650") == "35"
    assert rules.nir_lieu_compatible("35", "France", "35650") is True
