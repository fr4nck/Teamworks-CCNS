from pathlib import Path


GENERALITES = Path("teamworks/Ctrl/CTRL_Page_generalites.py")


def test_coordonnees_sont_deja_embarquees_dans_generalites():
    source = GENERALITES.read_text(encoding="utf-8")
    assert 'titre=_(u"Coordonnées")' in source
    assert "self.list_ctrl_coords = ListCtrlCoords(" in source
    assert "self.button_coords_ajout = CTRL_Bouton_image.CTRL(" in source
    assert "self.button_coords_modif = CTRL_Bouton_image.CTRL(" in source
    assert "self.button_coords_suppr = CTRL_Bouton_image.CTRL(" in source


def test_le_dialogue_coords_n_est_plus_un_element_de_layout_principal():
    source = GENERALITES.read_text(encoding="utf-8")
    # Le dialogue reste un adaptateur de saisie pour Ajouter/Modifier ; la liste
    # et les actions sont directement visibles sur Généralités.
    assert "self.section_coords" in source
    assert "panel_coords.SetSizer(coords)" in source
