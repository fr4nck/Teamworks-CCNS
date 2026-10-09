import ast
from pathlib import Path

from teamworks.Utils.UTILS_Duration import duree_presence_wx


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "teamworks" / "Dlg" / "DLG_Scenario.py"


def _get_heures_realisees_methods():
    source = SCENARIO.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(SCENARIO))
    methods = []
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name in {"Tableau", "GetDictColonnes"}:
            methods.extend(
                child
                for child in node.body
                if isinstance(child, ast.FunctionDef) and child.name == "GetHeuresRealisees"
            )
    return methods


def test_scenario_distingue_horaire_de_journee_et_duree_cumulee():
    methods = _get_heures_realisees_methods()
    assert len(methods) == 2
    for method in methods:
        calls = [
            node.func.id
            for node in ast.walk(method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "duree_presence_wx" in calls


def test_scenario_ne_reconstruit_plus_les_horaires_comme_durees_signees():
    source = SCENARIO.read_text(encoding="utf-8")
    methods = _get_heures_realisees_methods()
    for method in methods:
        segment = ast.get_source_segment(source, method)
        assert '"+" + heure_fin' not in segment
        assert '"+" + heure_debut' not in segment


def test_presence_negative_inferieure_a_une_heure_conserve_son_signe():
    valeur, resultat = duree_presence_wx("09:00", "08:30")
    assert resultat.ok
    assert valeur == "-0:30"


def test_horaires_identiques_valent_zero_sans_inventer_24_heures():
    valeur, resultat = duree_presence_wx("08:00", "08:00")
    assert resultat.ok
    assert valeur == "+0:00"


def test_passage_de_minuit_reste_explicite():
    valeur_brute, resultat_brut = duree_presence_wx("22:00", "02:00")
    valeur_nuit, resultat_nuit = duree_presence_wx("22:00", "02:00", allow_overnight=True)
    assert resultat_brut.ok and valeur_brute == "-20:00"
    assert resultat_nuit.ok and valeur_nuit == "+4:00"


def test_presence_invalide_retourne_une_erreur_metier_structuree():
    valeur, resultat = duree_presence_wx(None, "12:00")
    assert valeur is None
    assert not resultat.ok
    assert resultat.error.code == "MISSING_TIME"
    assert resultat.error.field == "debut"
