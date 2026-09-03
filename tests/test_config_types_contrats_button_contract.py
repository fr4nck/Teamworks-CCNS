from pathlib import Path


SOURCE = Path("teamworks/Dlg/DLG_Config_types_contrats.py")


def test_types_contrats_ne_reintroduit_pas_de_bitmapbutton_brut():
    source = SOURCE.read_text(encoding="utf-8")
    assert "wx.BitmapButton(" not in source
    assert "CTRL_Bouton_image.CTRL(" in source


def test_types_contrats_conserve_les_roles_semantiques():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'texte=_(u"Supprimer")' in source
    assert 'role="danger"' in source
    assert 'texte=_(u"Aide")' in source
    assert 'texte=_(u"Fermer")' in source
    assert source.count('role="quiet"') >= 2
