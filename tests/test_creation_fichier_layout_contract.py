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


def test_creation_fichier_parente_les_controles_a_leur_staticbox():
    # Contrat wx.StaticBoxSizer (cf. tests/test_rc_static_audit.py) : les
    # enfants d'un StaticBoxSizer doivent avoir la StaticBox pour parent.
    source = _lire(DLG)
    attendus = {
        "self.radio_local = wx.RadioButton(self.sizer_type_staticbox,": 1,
        "self.radio_reseau = wx.RadioButton(self.sizer_type_staticbox,": 1,
        "self.label_nom = wx.StaticText(self.sizer_contenu_staticbox,": 1,
        "self.text_nom = wx.TextCtrl(self.sizer_contenu_staticbox,": 1,
        "self.checkbox_details = wx.CheckBox(self.sizer_contenu_staticbox,": 1,
        "self.hyperlink_details = self.Build_Hyperlink(self.sizer_contenu_staticbox)": 1,
        "hl.HyperLinkCtrl(parent,": 1,
        "self.panelReseau = PanelReseau(self.sizer_reseau_staticbox)": 1,
    }
    for fragment, nombre in attendus.items():
        assert source.count(fragment) == nombre, fragment


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
