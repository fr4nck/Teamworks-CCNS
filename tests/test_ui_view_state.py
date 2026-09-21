from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "teamworks"))

from Utils import UTILS_Etat_vues as etat


def test_etat_corrompu_retombe_sur_les_defauts():
    resultat = etat.normaliser_etat_colonnes(
        {"version": 999, "order": ["telephone"]},
        ["nom", "telephone", "qualification"],
        ordre_defaut=["nom", "qualification", "telephone"],
        visibilite_defaut={"nom": True, "qualification": True, "telephone": True},
    )
    assert resultat["order"] == ["nom", "qualification", "telephone"]
    assert resultat["widths"] == {}
    assert resultat["visible"]["qualification"] is True


def test_etat_ignore_inconnues_doublons_et_borne_largeurs():
    resultat = etat.normaliser_etat_colonnes(
        {
            "version": 1,
            "order": ["telephone", "inconnue", "nom", "telephone"],
            "widths": {"telephone": "120", "qualification": 99999, "inconnue": 50},
            "visible": {"qualification": False, "inconnue": True},
            "scale": 2.0,
        },
        ["nom", "telephone", "qualification"],
        ordre_defaut=["nom", "telephone", "qualification"],
    )
    assert resultat["order"] == ["telephone", "nom", "qualification"]
    assert resultat["widths"]["telephone"] == 120
    assert resultat["widths"]["qualification"] == etat.LARGEUR_MAX
    assert "inconnue" not in resultat["widths"]
    assert resultat["visible"]["qualification"] is False
    assert resultat["scale"] == 2.0


def test_fusion_ordre_visible_preserve_les_colonnes_masquees():
    assert etat.fusionner_ordre_visible(
        ["nom", "email_cache", "telephone", "qualification"],
        ["qualification", "nom", "telephone"],
    ) == ["qualification", "email_cache", "nom", "telephone"]


def test_largeur_est_adaptee_au_changement_de_dpi():
    assert etat.adapter_largeur(120, 1.0, 1.5) == 180
    assert etat.adapter_largeur(0, 1.0, 2.0) == 0
