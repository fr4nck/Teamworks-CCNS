import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ETAT = ROOT / "teamworks/Utils/UTILS_Etat_colonnes.py"
PERSONNES = ROOT / "teamworks/Ol/OL_personnes.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _charger_etat():
    spec = importlib.util.spec_from_file_location("etat_colonnes_test", ETAT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _defauts():
    return [
        ["Nom", "left", 120, "nom", "", "Nom", True, 1],
        ["Téléphones", "left", 200, "telephones", "", "Téléphones", True, 2],
        ["Email", "left", 150, "email", "", "Email", True, 3],
    ]


def test_premiere_utilisation_garde_strictement_les_defauts():
    module = _charger_etat()
    resultat = module.fusionner_colonnes(_defauts(), None)
    assert resultat == _defauts()
    assert resultat is not _defauts()


def test_etat_utilisateur_restaure_largeur_ordre_et_visibilite():
    module = _charger_etat()
    etat = {
        "version": 1,
        "colonnes": {
            "telephones": {"largeur": 345, "ordre": 1, "visible": True},
            "nom": {"largeur": 180, "ordre": 2, "visible": False},
        },
        "tri": {"champ": "telephones", "ascendant": False},
    }
    resultat = module.fusionner_colonnes(_defauts(), etat)
    par_champ = {colonne[3]: colonne for colonne in resultat}
    assert par_champ["telephones"][2] == 345
    assert par_champ["telephones"][7] == 1
    assert par_champ["nom"][2] == 180
    assert par_champ["nom"][6] is False
    assert module.extraire_tri(etat, ["nom", "telephones", "email"]) == (
        "telephones",
        False,
    )


def test_colonne_nouvelle_prend_son_defaut_et_colonne_supprimee_est_ignoree():
    module = _charger_etat()
    etat = {
        "version": 1,
        "colonnes": {
            "nom": {"largeur": 160, "ordre": 1, "visible": True},
            "ancienne_colonne_supprimee": {"largeur": 999, "ordre": 2, "visible": False},
        },
        "tri": {"champ": "ancienne_colonne_supprimee", "ascendant": False},
    }
    resultat = module.fusionner_colonnes(_defauts(), etat)
    par_champ = {colonne[3]: colonne for colonne in resultat}
    assert par_champ["email"][2] == 150
    assert "ancienne_colonne_supprimee" not in par_champ
    assert module.extraire_tri(
        etat,
        ["nom", "telephones", "email"],
        champ_defaut="nom",
    ) == ("nom", False)


def test_vieux_config_invalide_ne_peut_pas_casser_la_liste():
    module = _charger_etat()
    etats_invalides = (
        "ancien format",
        {"version": 999, "colonnes": []},
        {"version": 1, "colonnes": {"nom": {"largeur": "abc", "ordre": -5, "visible": "oui"}}},
        {"version": 1, "colonnes": {"nom": {"largeur": 999999, "ordre": 1, "visible": True}}},
    )
    for etat in etats_invalides:
        resultat = module.fusionner_colonnes(_defauts(), etat)
        assert len(resultat) == 3
        assert all(len(colonne) >= 8 for colonne in resultat)


def test_etat_serialise_utilise_les_noms_de_champs_stables():
    module = _charger_etat()
    etat = module.construire_etat(
        _defauts(),
        {"nom": 222, "telephones": 333, "email": 144},
        "telephones",
        False,
    )
    assert set(etat["colonnes"]) == {"nom", "telephones", "email"}
    assert etat["colonnes"]["telephones"]["largeur"] == 333
    assert etat["tri"] == {"champ": "telephones", "ascendant": False}


def test_listview_persiste_resize_tri_et_configuration_explicitement():
    source = _source(PERSONNES)
    assert '"wx_personnes_etat_colonnes_v1"' in source
    assert "wx.EVT_LIST_COL_END_DRAG" in source
    assert "def _HandleColumnClick" in source
    assert "UTILS_Config.FichierConfig().SetItemConfig" in source
    assert "UTILS_Etat_colonnes.fusionner_colonnes" in source
    assert "self.listeColonnesOriginale" in source
    assert "self._sauvegarder_presentation_colonnes()" in source


def test_fichiers_compilent():
    for path in (ETAT, PERSONNES):
        compile(_source(path), str(path), "exec")
