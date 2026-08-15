from pathlib import Path


def test_visualiseur_image_zoom_uses_integer_dimensions_and_scroll_steps():
    source = Path("teamworks/Dlg/DLG_Visualiseur_image.py").read_text(encoding="utf-8")

    assert "self.SetScrollRate((10 * ratio) // 100, (10 * ratio) // 100)" in source
    assert "largeur = (self.imgORIX * self.ratio) // 100" in source
    assert "hauteur = (self.imgORIY * self.ratio) // 100" in source

    assert "self.SetScrollRate((10*ratio)/100, (10*ratio)/100)" not in source
    assert "largeur = (self.imgORIX * self.ratio)/100" not in source
    assert "hauteur = (self.imgORIY * self.ratio)/100" not in source
