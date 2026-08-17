from teamworks.Utils.UTILS_Presences import (
    formater_libelle_activite,
    normaliser_intitule_presence,
)


def test_normalise_les_fausses_legendes_vides():
    assert normaliser_intitule_presence(None) == ""
    assert normaliser_intitule_presence("") == ""
    assert normaliser_intitule_presence("   ") == ""
    assert normaliser_intitule_presence("()") == ""
    assert normaliser_intitule_presence("( )") == ""


def test_conserve_les_vraies_legendes():
    assert normaliser_intitule_presence(" Piscine ") == "Piscine"


def test_formate_activite_sans_parentheses_si_legende_vide():
    assert formater_libelle_activite("Animation", None) == "Animation"
    assert formater_libelle_activite("Animation", "") == "Animation"
    assert formater_libelle_activite("Animation", "   ") == "Animation"
    assert formater_libelle_activite("Animation", "()") == "Animation"


def test_formate_activite_avec_parentheses_si_legende_reelle():
    assert formater_libelle_activite("Animation", "Piscine") == "Animation (Piscine)"
