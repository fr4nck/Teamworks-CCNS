from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur.py"


def _source():
    return PATH.read_text(encoding="utf-8")


def test_publiposteur_has_no_raw_business_buttons():
    source = _source()
    assert "wx.BitmapButton(" not in source
    assert "wx.Button(" not in source
    assert "SetBitmapLabel(" not in source
    assert source.count("CTRL_Bouton_image.CTRL(") == 16


def test_publiposteur_navigation_uses_semantic_common_actions():
    source = _source()
    assert "def SetSuiteAction" in source
    assert 'self.SetSuiteAction(u"Suivant", "Suite_L72.png")' in source
    assert 'self.SetSuiteAction(u"Valider", "Valider_L72.png")' in source
    assert 'self.GetGrandParent().SetSuiteAction(u"Arrêter", "Arreter_L72.png", role="danger")' in source
    assert 'role="primary"' in source
    assert 'role="quiet"' in source


def test_publiposteur_small_ellipsis_buttons_are_replaced_by_named_actions():
    source = _source()
    assert 'texte=_(u"Parcourir…")' in source
    assert 'texte=_(u"Préfixe…")' in source
    assert 'wx.Button(self.sizer_contenu_staticbox, -1, "...")' not in source


def test_publiposteur_destructive_actions_use_danger_role():
    source = _source()
    # Deux suppressions visibles (champ personnalisé et modèle) + Arrêter.
    assert source.count('role="danger"') >= 3
