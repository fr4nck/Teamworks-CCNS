from pathlib import Path


BUTTON_SOURCE = Path("teamworks/Ctrl/CTRL_Bouton_image.py")
STYLES_SOURCE = Path("teamworks/Utils/UTILS_Styles.py")


def _read(path):
    return path.read_text(encoding="utf-8")


def test_button_icons_follow_interface_scale():
    source = _read(BUTTON_SOURCE)
    assert "taille_cible = _echelle_taille(self.tailleImage)" in source
    assert "_chemin_image_existant(self.cheminImage, max(taille_cible))" in source
    assert "img.resize(taille_cible" in source


def test_button_icons_choose_from_multiresolution_assets():
    source = _read(BUTTON_SOURCE)
    assert "ICON_RESOURCE_SIZES = (16, 22, 32, 48, 80, 128)" in source
    assert "if size >= target" in source
    assert "return max(candidates, key=lambda item: item[0])[1]" in source


def test_semantic_icon_sizes_remain_centralized():
    source = _read(STYLES_SOURCE)
    assert 'ICON_SIZES = {"micro": 12, "small": 16, "medium": 20, "large": 24, "hero": 32}' in source
    assert "def GetIconSize(" in source
