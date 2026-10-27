# -*- coding: utf-8 -*-
"""RC5 : garde-fous ciblés des défauts constatés en recette Windows."""
import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
BUTTON = ROOT / "teamworks/Ctrl/CTRL_Bouton_image.py"
WIZARD = ROOT / "teamworks/Dlg/DLG_Publiposteur.py"
LIST = ROOT / "teamworks/Ctrl/CTRL_Page_contrats_core.py"
SMOKE = ROOT / "tools/smoke_contract_documents.py"


def _load_function(path, name, namespace=None):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    module = ast.Module(body=[node], type_ignores=[])
    scope = dict(namespace or {})
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), scope)
    return scope[name]


def test_legacy_wordmark_button_png_is_never_scaled_as_square_text_icon():
    classifier = _load_function(
        BUTTON, "_est_image_bouton_avec_libelle", {"Path": Path}
    )
    assert classifier("Images/BoutonsImages/Retour_L72.png") is True
    assert classifier("Images/BoutonsImages/Valider_L72.png") is True
    assert classifier("Images/32x32/Suivant.png") is False
    assert classifier(None) is False
    source = BUTTON.read_text(encoding="utf-8")
    assert 'self.texte and _est_image_bouton_avec_libelle(self.cheminImage)' in source
    assert "return wx.NullBitmap" in source


def test_publiposteur_navigation_uses_real_icons_without_changing_events():
    source = WIZARD.read_text(encoding="utf-8")
    for key, icon in (
        ("Suite_L72.png", "Suivant.png"),
        ("Valider_L72.png", "Valider.png"),
        ("Arreter_L72.png", "Annuler.png"),
        ("Fermer_L72.png", "Fermer.png"),
    ):
        assert '"%s": "%s"' % (key, icon) in source
    assert 'cheminImage=Chemins.GetStaticPath("Images/32x32/Precedent.png")' in source
    assert 'cheminImage=Chemins.GetStaticPath("Images/32x32/Suivant.png")' in source
    assert source.count("margesTexte=(6, 0)") >= 2
    assert 'Images/BoutonsImages/%s" % nom_image' not in source
    for callback in ("Onbouton_retour", "Onbouton_suite", "Onbouton_annuler"):
        assert "self.Bind(wx.EVT_BUTTON, self.%s" % callback in source
    assert "self.panel_base.Layout()" in source
    assert "32x32" in SMOKE.read_text(encoding="utf-8")


def test_contracts_list_msw_avoids_hover_flicker_rules():
    wx = SimpleNamespace(
        Platform="__WXMSW__",
        LC_REPORT=0x20,
        LC_SINGLE_SEL=0x2000,
        LC_HRULES=0x02,
        LC_VRULES=0x01,
    )
    style = _load_function(LIST, "_style_liste_contrats", {"wx": wx})
    windows = style()
    linux = style("__WXGTK__")
    assert windows == wx.LC_REPORT | wx.LC_SINGLE_SEL
    assert not windows & (wx.LC_HRULES | wx.LC_VRULES)
    assert linux & (wx.LC_HRULES | wx.LC_VRULES) == (
        wx.LC_HRULES | wx.LC_VRULES
    )
    source = LIST.read_text(encoding="utf-8")
    assert "style=_style_liste_contrats()" in source
    assert "if self.GetColumnWidth(index) != taille:" in source
    assert "self.Freeze()" in source
    assert "self.Thaw()" in source
    assert "finally:" in source
    assert "self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)" in source
    assert "self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)" in source
