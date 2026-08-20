from pathlib import Path


THEME = Path("teamworks/Utils/UTILS_Theme.py")
OLV = Path("teamworks/Ctrl/CTRL_ObjectListView.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def test_group_headers_use_semantic_theme_roles():
    source = _source(THEME)

    assert '"surface_high"' in source
    assert 'GetToken("surface_container_high"' in source
    assert "def _apply_objectlistview_group_theme" in source
    assert 'window.groupTextColour = palette["text"]' in source
    assert 'window.groupBackgroundColour = palette["surface_high"]' in source


def test_group_theming_does_not_patch_checkbox_business_logic():
    theme = _source(THEME)
    olv = _source(OLV)

    assert "_HandleLeftDownOnImage" not in theme
    assert "CocheListeTout" not in theme
    assert "CocheListeRien" not in theme

    # Contrat TW-180 : un clic d'image inverse une seule fois l'état métier de
    # la colonne puis rafraîchit la ligne et appelle OnCheck.
    bridge = olv.split("def _HandleLeftDownOnImage", 1)[1].split("def OnCheck", 1)[0]
    assert "column.HasCheckState()" in bridge
    assert "column.SetCheckState(modelObject, not column.GetCheckState(modelObject))" in bridge
    assert "self.RefreshIndex(rowIndex, modelObject)" in bridge
    assert "self.OnCheck(modelObject)" in bridge


def test_historical_group_blue_is_confined_to_legacy_component():
    theme = _source(THEME)

    assert "159, 185, 250" not in theme
    assert "33, 33, 33" not in theme
