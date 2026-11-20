"""Garde-fous statiques du dialogue de démarrage (sans session graphique).

Ce test ne remplace pas la recette manuelle GTK3 / Windows.
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Assistant_demarrage.py"
ASSETS = ROOT / "teamworks" / "Static" / "Images" / "Branding"
PACKAGE = ROOT / "packaging" / "debian" / "build.sh"


def test_identite_graphique_du_dialogue():
    source = DIALOG.read_text(encoding="utf-8")
    ast.parse(source)
    assert (ASSETS / "Teamworks-CCNS.ico").is_file()
    assert 'Images/Branding/Teamworks-CCNS.ico' in source
    assert 'self.SetIcon(icone)' in source


def test_le_pied_du_dialogue_est_reajuste_apres_affichage():
    source = DIALOG.read_text(encoding="utf-8")
    assert 'wx.RESIZE_BORDER' in source
    assert 'self.Bind(wx.EVT_SHOW, self.OnAffichage)' in source
    assert 'wx.CallAfter(self._AssurerBoutonsVisibles)' in source
    assert 'self.SetMinClientSize((largeur, hauteur))' in source
    assert 'self.SetClientSize((largeur, hauteur))' in source
    assert 'self.bouton_ok.GetRect().GetBottom()' in source


def test_paquet_debian_utilise_le_logo_personnalise():
    assert (ASSETS / "Teamworks-CCNS.png").is_file()
    source = PACKAGE.read_text(encoding="utf-8")
    assert '$app/teamworks/Static/Images/Branding/Teamworks-CCNS.png' in source
