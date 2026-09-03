from pathlib import Path


PERSONNES = Path("teamworks/Ctrl/CTRL_Personnes.py")


def test_personnes_ne_reintroduit_pas_de_bitmap_button_local():
    source = PERSONNES.read_text(encoding="utf-8")
    assert "wx.BitmapButton(" not in source
    assert "def _bitmap_action(" not in source
    assert "CTRL_Bouton_image.CTRL(" in source


def test_personnes_conserve_les_onze_actions_metier():
    source = PERSONNES.read_text(encoding="utf-8")
    for nom in (
        "bouton_ajouter",
        "bouton_modifier",
        "bouton_supprimer",
        "bouton_rechercher",
        "bouton_affichertout",
        "bouton_options",
        "bouton_courrier",
        "bouton_imprimer",
        "bouton_export_texte",
        "bouton_export_excel",
        "bouton_aide",
    ):
        assert "self.%s = _bouton_action(" % nom in source


def test_personnes_utilise_une_source_icone_multiresolution():
    source = PERSONNES.read_text(encoding="utf-8")
    assert 'Images/32x32/%s' in source
    assert 'Images/16x16/%s' not in source
