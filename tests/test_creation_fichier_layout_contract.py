"""Contrat statique (sans GUI) : boîte « Création d'un fichier » et boutons communs."""

import ast
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "teamworks"
DLG = RACINE / "Dlg" / "DLG_Saisie_nouveau_fichier.py"
BOUTON = RACINE / "Ctrl" / "CTRL_Bouton_image.py"


def _lire(chemin):
    return chemin.read_text(encoding="utf-8")


def test_creation_fichier_compile_et_garde_les_boutons_communs():
    source = _lire(DLG)
    ast.parse(source)
    assert source.count("CTRL_Bouton_image.CTRL(") == 3


def test_creation_fichier_ne_parente_plus_les_controles_a_un_staticbox():
    source = _lire(DLG)
    for ligne in source.splitlines():
        if "_staticbox" in ligne and "StaticBoxSizer" not in ligne:
            # Seule la création des wx.StaticBox elles-mêmes peut y faire référence.
            assert "wx.StaticBox(self, -1" in ligne or "self.sizer_" in ligne.split("=")[0]


def test_creation_fichier_ne_force_plus_police_fixe_ni_taille_bouton():
    source = _lire(DLG)
    assert "wx.Font(8" not in source
    assert ".SetSize(self.bouton_" not in source


def test_creation_fichier_ajuste_la_fenetre_au_contenu_et_reste_redimensionnable():
    source = _lire(DLG)
    assert "UTILS_Styles.FitWindowToContent(self" in source
    assert "wx.RESIZE_BORDER" in source


def test_contrat_bouton_reinitialise_min_size_avant_mesure():
    source = _lire(BOUTON)
    debut = source.index("def _appliquer_contrat_bouton")
    fin = source.index("class CTRL(", debut)
    corps = source[debut:fin]
    assert corps.index("SetMinSize((-1, -1))") < corps.index("SetInitialSize()")
    assert corps.index("InvalidateBestSize") < corps.index("SetInitialSize()")
